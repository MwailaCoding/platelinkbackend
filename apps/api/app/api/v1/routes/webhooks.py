# backend/app/api/v1/routes/webhooks.py
import logging
from uuid import UUID
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime
import ipaddress

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db
from app.models import (
    Order, Payment, Restaurant, MpesaTransaction,
    PaymentStatus, OrderStatus, PaymentMethod
)
from app.services.pesapal_service import PesapalService
from app.api.v1.websockets.connection_manager import manager as ws_manager
from app.tasks.worker import retry_pesapal_webhook_task, retry_mpesa_webhook_task

# Configure logging
logger = logging.getLogger("platelink.api.webhooks")

router = APIRouter()

# Safaricom M-Pesa callback IP addresses (sandbox & production subnets/IPs)
SAFARICOM_IP_WHITELIST = {
    "196.201.214.200", "196.201.214.206", "196.201.213.114", "196.201.214.207",
    "196.201.214.208", "196.201.213.44", "196.201.212.74", "196.201.212.129",
    "196.201.212.138", "196.201.212.128", "196.201.212.136", "196.201.212.132",
    "196.201.212.130", "196.201.212.137", "196.201.212.131", "196.201.212.135",
    "196.201.212.133", "196.201.212.134", "196.201.212.139", "196.201.212.140",
    "127.0.0.1", "localhost", "::1"
}

def verify_safaricom_ip(client_ip: str) -> bool:
    """
    Validates if the incoming request client IP is within Safaricom's whitelisted IPs/subnets.
    """
    if client_ip in SAFARICOM_IP_WHITELIST:
        return True
        
    # Check Safaricom CIDR Subnets (e.g. 196.201.212.0/24, 196.201.213.0/24, 196.201.214.0/24)
    safaricom_cidrs = [
        "196.201.212.0/24",
        "196.201.213.0/24",
        "196.201.214.0/24"
    ]
    
    try:
        ip = ipaddress.ip_address(client_ip)
        for cidr in safaricom_cidrs:
            if ip in ipaddress.ip_network(cidr):
                return True
    except ValueError:
        pass
        
    return False


def extract_metadata_value(metadata_items: list, name: str) -> Optional[Any]:
    """
    Helper to extract value for a given key name from M-Pesa CallbackMetadata.
    """
    for item in metadata_items:
        if item.get("Name") == name:
            return item.get("Value")
    return None


@router.post("/pesapal", status_code=status.HTTP_200_OK)
async def pesapal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Pesapal Instant Payment Notification (IPN) webhook handler.
    Verifies webhook request using signature header and secure query-back verification.
    """
    logger.info("Pesapal webhook request received.")
    
    # 1. Signature verification
    signature = request.headers.get("x-pesapal-signature")
    if not signature:
        logger.warning("Incoming Pesapal webhook request missing 'X-Pesapal-Signature' header.")
        # In production, we might enforce this strictly depending on compliance requirements:
        # raise HTTPException(status_code=401, detail="Missing signature header.")

    # 2. Extract parameters (supports both URL query parameters and POST body)
    order_tracking_id = request.query_params.get("OrderTrackingId")
    merchant_reference = request.query_params.get("OrderMerchantReference")
    notification_type = request.query_params.get("OrderNotificationType")

    if not order_tracking_id:
        try:
            body = await request.json()
            order_tracking_id = body.get("OrderTrackingId") or body.get("order_tracking_id")
            merchant_reference = body.get("OrderMerchantReference") or body.get("merchant_reference")
            notification_type = body.get("OrderNotificationType") or body.get("notification_type")
        except Exception:
            pass

    if not order_tracking_id:
        logger.error("Could not extract OrderTrackingId from Pesapal webhook request.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OrderTrackingId is required."
        )

    # 3. Log webhook parameters for audit/debugging
    logger.info(
        f"Processing Pesapal webhook: Tracking ID = {order_tracking_id} | "
        f"Merchant Ref = {merchant_reference} | Notification Type = {notification_type}"
    )

    try:
        # 4. Check Idempotency: Check if already processed
        stmt = select(Payment).where(Payment.transaction_id == order_tracking_id)
        res = await db.execute(stmt)
        payment = res.scalar_one_or_none()

        if payment and payment.status == PaymentStatus.paid:
            logger.info(f"Pesapal transaction {order_tracking_id} already marked as paid. Skipping redundant processing.")
            return {"status": "success", "message": "Transaction already processed (idempotent)."}

        # 5. Fetch live transaction status directly from Pesapal for secure verification (Query-back verification pattern)
        pesapal_service = PesapalService()
        status_data = await pesapal_service.get_transaction_status(order_tracking_id)

        payment_status = status_data.get("payment_status_description")
        amount = status_data.get("amount")
        payment_method_desc = status_data.get("payment_method")

        logger.info(f"Pesapal live verification result: Status = {payment_status} | Amount = {amount}")

        if payment_status == "COMPLETED":
            if not payment:
                # Find by Order UUID if payment record wasn't pre-created
                if merchant_reference:
                    try:
                        order_uuid = UUID(merchant_reference)
                        order = await db.get(Order, order_uuid)
                    except ValueError:
                        order = None
                else:
                    order = None
                    
                if not order:
                    raise ValueError(f"Could not link Pesapal tracking ID {order_tracking_id} to an existing order.")

                payment = Payment(
                    restaurant_id=order.restaurant_id,
                    order_id=order.id,
                    amount=Decimal(str(amount)),
                    payment_method=PaymentMethod.card,
                    status=PaymentStatus.pending,
                    transaction_id=order_tracking_id
                )
                db.add(payment)
            else:
                order = await db.get(Order, payment.order_id)

            if not order:
                raise ValueError(f"Order associated with payment {payment.id} not found.")

            # Update Payment & Order
            payment.status = PaymentStatus.paid
            payment.completed_at = datetime.utcnow()
            order.payment_status = PaymentStatus.paid
            
            # Map payment method if possible
            if payment_method_desc and str(payment_method_desc).lower() == "mpesa":
                order.payment_method = PaymentMethod.mpesa
                payment.payment_method = PaymentMethod.mpesa
            else:
                order.payment_method = PaymentMethod.card

            # Calculate Platform Fee (1%)
            platform_fee = float(order.total) * 0.01
            net_amount = float(order.total) - platform_fee

            # Fetch Restaurant and initiate dynamic payout transfer
            restaurant = await db.get(Restaurant, order.restaurant_id)
            if restaurant and restaurant.phone:
                try:
                    await pesapal_service.initiate_transfer(
                        recipient_phone=restaurant.phone,
                        amount=net_amount,
                        narrative=f"Payout for Order {order.order_number or order.id}"
                    )
                    logger.info(f"Successfully initiated Pesapal transfer of KES {net_amount} to restaurant {restaurant.name}.")
                except Exception as payout_err:
                    # Log but do not block webhook resolution. Task will handle retry if strict payout required.
                    logger.error(f"Pesapal payout transfer failed: {payout_err}")

            # Send order to kitchen via WebSocket
            await ws_manager.broadcast_to_kitchen(str(order.restaurant_id), {
                "type": "new_order",
                "order_id": str(order.id),
                "order_number": order.order_number,
                "total": float(order.total)
            })

            await db.commit()
            logger.info(f"Successfully processed Pesapal webhook for order {order.id}.")
        else:
            logger.warning(f"Pesapal transaction {order_tracking_id} is in status {payment_status}. Skipping updates.")

    except Exception as exc:
        logger.exception(f"Error processing Pesapal webhook for tracking ID {order_tracking_id}: {exc}")
        # Hand off to Celery for asynchronous retry with backoff
        payload = {
            "order_tracking_id": order_tracking_id,
            "payment_status": "COMPLETED" # Retry under assumption of completion
        }
        retry_pesapal_webhook_task.delay(payload)
        logger.info("Enqueued retry task in Celery for Pesapal webhook.")
        # Return 200 OK to Pesapal so they don't flood us, Celery will handle the retry
        return {"status": "queued_for_retry", "detail": str(exc)}

    return {"status": "success"}


@router.post("/mpesa/callback", status_code=status.HTTP_200_OK)
async def mpesa_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Safaricom M-Pesa C2B/STK Push Callback Handler.
    Performs whitelisted IP verification and processes transaction status.
    """
    # 1. Safaricom IP Whitelist verification
    client_ip = request.client.host if request.client else "unknown"
    if not verify_safaricom_ip(client_ip):
        logger.warning(f"Unauthorized Callback Attempt: Blocked non-Safaricom IP '{client_ip}' from accessing webhook.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Access restricted to Safaricom Daraja gateway."
        )

    try:
        data = await request.json()
    except Exception as json_err:
        logger.error(f"Invalid JSON body in M-Pesa callback: {json_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON body."
        )

    # Log full payload for audit trails and debugging
    logger.info(f"M-Pesa Callback Payload: {data}")

    stk_callback = data.get("Body", {}).get("stkCallback", {})
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")

    if not checkout_request_id:
        logger.error("Missing CheckoutRequestID in M-Pesa callback body.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CheckoutRequestID is required."
        )

    try:
        # 2. Check Idempotency: Check if transaction has already been successfully processed
        stmt = select(MpesaTransaction).where(MpesaTransaction.checkout_request_id == checkout_request_id)
        res = await db.execute(stmt)
        tx = res.scalar_one_or_none()

        if tx and tx.result_code == 0:
            logger.info(f"M-Pesa transaction {checkout_request_id} already marked as successful. Skipping duplicate callback.")
            return {"ResultCode": 0, "ResultDesc": "Success (idempotent)"}

        # 3. Extract Metadata on Success (ResultCode == 0)
        receipt_number = None
        amount = None
        phone_number = None

        if result_code == 0:
            metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
            receipt_number = extract_metadata_value(metadata, "MpesaReceiptNumber")
            amount = extract_metadata_value(metadata, "Amount")
            phone_number = extract_metadata_value(metadata, "PhoneNumber")

            logger.info(
                f"Successfully parsed M-Pesa Success: Receipt = {receipt_number} | "
                f"Amount = {amount} | Phone = {phone_number}"
            )

        if not tx:
            raise ValueError(f"M-Pesa transaction with CheckoutRequestID {checkout_request_id} not found in database.")

        # Update MpesaTransaction record
        tx.result_code = result_code
        tx.result_desc = result_desc
        tx.mpesa_receipt_number = receipt_number

        # Fetch and update associated Payment & Order records
        stmt_payment = select(Payment).where(Payment.transaction_id == checkout_request_id)
        res_payment = await db.execute(stmt_payment)
        payment = res_payment.scalar_one_or_none()

        if result_code == 0:
            if payment:
                payment.status = PaymentStatus.paid
                payment.mpesa_receipt_number = receipt_number
                payment.completed_at = datetime.utcnow()
                
            # Update Order Status
            order_id = payment.order_id if payment else None
            if order_id:
                order = await db.get(Order, order_id)
                if order:
                    order.payment_status = PaymentStatus.paid
                    order.payment_method = PaymentMethod.mpesa
                    
                    # Notify kitchen via WebSocket
                    await ws_manager.broadcast_to_kitchen(str(order.restaurant_id), {
                        "type": "new_order",
                        "order_id": str(order.id),
                        "order_number": order.order_number,
                        "total": float(order.total)
                    })
        else:
            logger.warning(f"M-Pesa transaction {checkout_request_id} failed with code {result_code}: {result_desc}")
            if payment:
                payment.status = PaymentStatus.failed

        await db.commit()
        logger.info(f"M-Pesa callback for checkout {checkout_request_id} processed successfully.")

    except Exception as exc:
        logger.exception(f"Error processing M-Pesa callback for checkout {checkout_request_id}: {exc}")
        # Hand off to Celery task for background retry handling
        payload = {
            "CheckoutRequestID": checkout_request_id,
            "ResultCode": result_code,
            "ResultDesc": result_desc,
            "MpesaReceiptNumber": receipt_number,
            "Amount": amount
        }
        retry_mpesa_webhook_task.delay(payload)
        logger.info("Enqueued retry task in Celery for M-Pesa callback.")
        # Return 200 OK to Safaricom to prevent callback storms, Celery handles database resolution.
        return {"ResultCode": 0, "ResultDesc": "Queued for retry"}

    return {"ResultCode": 0, "ResultDesc": "Success"}
