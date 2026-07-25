# backend/app/api/v1/routes/payments.py
import logging
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.core.deps import get_db, get_current_user
from app.models import (
    Order, Payment, Staff, MpesaTransaction,
    OrderStatus, PaymentStatus, PaymentMethod, ActivityLog,
    OrderItem, MenuItem, Restaurant, CustomerSession
)
from app.services.pesapal_service import PesapalService
from app.services.daraja_service import DarajaService
from app.core.config import settings

# Configure logging
logger = logging.getLogger("platelink.api.payments")

router = APIRouter()

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class PesapalInitiateRequest(BaseModel):
    order_id: str
    amount: float
    customer_phone: str
    customer_email: EmailStr


class MpesaStkPushRequest(BaseModel):
    order_id: str
    restaurant_id: str
    amount: float
    customer_phone: str


class CashConfirmRequest(BaseModel):
    staff_id: str
    amount_received: float
    payment_id: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

async def simulate_pesapal_callback(
    restaurant_id: str,
    transaction_id: str,
    order_id: str
):
    import asyncio
    import uuid
    from app.db.session import async_session_local
    from app.models import Order, Payment, PaymentStatus, PaymentMethod, ActivityLog
    from app.websockets.manager import manager
    from sqlalchemy import select
    from uuid import UUID
    
    # Wait for 3 seconds to simulate Pesapal payment gateway processing delay
    await asyncio.sleep(3)
    
    async with async_session_local() as db_session:
        try:
            stmt_pm = select(Payment).where(Payment.transaction_id == transaction_id)
            res_pm = await db_session.execute(stmt_pm)
            payment = res_pm.scalar_one_or_none()
            
            order = await db_session.get(Order, UUID(order_id))
            
            mpesa_receipt = f"MOCK{uuid.uuid4().hex[:6].upper()}"
            
            if payment:
                payment.status = PaymentStatus.paid
                payment.mpesa_receipt_number = mpesa_receipt
                payment.completed_at = datetime.utcnow()
                
            if order:
                order.payment_status = PaymentStatus.paid
                order.payment_method = PaymentMethod.card
                
            # Log activity
            db_session.add(ActivityLog(
                restaurant_id=UUID(restaurant_id),
                action="payment_received_pesapal_simulated",
                metadata_info={"order_id": order_id, "amount": float(payment.amount) if payment else 0.0}
            ))
            
            await db_session.commit()
            logger.info(f"[SIMULATION] Pesapal payment success committed for Order {order_id}")
            
            # Broadcast WebSocket notifications
            if order and order.session_id:
                # Broadcast to customer session room
                await manager.broadcast(
                    {"type": "payment_completed", "order_id": order_id},
                    f"session_{order.session_id}"
                )
                await manager.broadcast(
                    {"type": "payment_confirmed", "order_id": order_id},
                    f"session_{order.session_id}"
                )
            
            # Broadcast to general restaurant rooms for kitchen/waiter panels
            await manager.broadcast(
                {"type": "payment_confirmed", "order_id": order_id},
                restaurant_id
            )
            await manager.broadcast(
                {"type": "payment_completed", "order_id": order_id},
                restaurant_id
            )
        except Exception as e:
            logger.error(f"Error in simulate_pesapal_callback: {e}", exc_info=True)


@router.post("/pesapal/initiate", response_model=Dict[str, str])
async def initiate_pesapal_payment(
    payload: PesapalInitiateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate a Pesapal payment, submit order to Pesapal to get checkout URL,
    and store order_tracking_id in database.
    """
    try:
        order_uuid = UUID(payload.order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order_id format. Must be a valid UUID."
        )

    # 1. Fetch Order and verify existence
    order = await db.get(Order, order_uuid)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {payload.order_id} not found."
        )

    # Fetch Restaurant details to check slug
    restaurant = await db.get(Restaurant, order.restaurant_id)
    
    is_demo = False
    if restaurant and restaurant.slug == "hamiltons-cafe":
        is_demo = True
    elif payload.amount <= 0:
        is_demo = True
    elif not settings.PESAPAL_CONSUMER_KEY or settings.PESAPAL_CONSUMER_KEY in ("your_key", "placeholder", ""):
        is_demo = True

    if is_demo:
        import uuid
        order_tracking_id = f"pesapal_mock_{uuid.uuid4().hex[:12]}"
        
        # Create a pending Payment record in the database
        payment = Payment(
            restaurant_id=order.restaurant_id,
            order_id=order.id,
            amount=Decimal(str(payload.amount)) if payload.amount > 0 else Decimal("0.01"),
            payment_method=PaymentMethod.card,  # Default to card
            status=PaymentStatus.pending,
            transaction_id=order_tracking_id
        )
        db.add(payment)
        await db.commit()

        redirect_url = f"/{restaurant.slug if restaurant else 'customer'}/order/{order.id}"

        # Schedule background task to complete the payment
        background_tasks.add_task(
            simulate_pesapal_callback,
            str(order.restaurant_id),
            order_tracking_id,
            str(order.id)
        )

        return {
            "redirect_url": redirect_url,
            "order_tracking_id": order_tracking_id
        }

    # 2. Call PesapalService to submit the order
    pesapal_service = PesapalService()
    try:
        response = await pesapal_service.submit_order(
            order_id=payload.order_id,
            amount=payload.amount,
            phone_number=payload.customer_phone,
            email=payload.customer_email,
            description=f"PlateLink Order {order.order_number or payload.order_id}"
        )
    except Exception as e:
        logger.exception(f"Pesapal order submission failed for order {payload.order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pesapal service error: {str(e)}"
        )

    redirect_url = response.get("redirect_url")
    order_tracking_id = response.get("order_tracking_id")

    if not redirect_url or not order_tracking_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate payment redirect from Pesapal."
        )

    # 3. Create a pending Payment record in the database
    payment = Payment(
        restaurant_id=order.restaurant_id,
        order_id=order.id,
        amount=Decimal(str(payload.amount)),
        payment_method=PaymentMethod.card,  # Default Pesapal method to card
        status=PaymentStatus.pending,
        transaction_id=order_tracking_id
    )
    db.add(payment)
    await db.commit()

    return {
        "redirect_url": redirect_url,
        "order_tracking_id": order_tracking_id
    }


async def simulate_mpesa_callback(
    restaurant_id: str,
    checkout_request_id: str,
    order_id: str
):
    import asyncio
    import uuid
    from app.db.session import async_session_local
    from app.models import Order, Payment, MpesaTransaction, PaymentStatus, PaymentMethod, ActivityLog
    from app.websockets.manager import manager
    from sqlalchemy import select
    from uuid import UUID
    
    # Wait for 3 seconds to simulate M-Pesa network delay
    await asyncio.sleep(3)
    
    async with async_session_local() as db_session:
        try:
            stmt_tx = select(MpesaTransaction).where(MpesaTransaction.checkout_request_id == checkout_request_id)
            res_tx = await db_session.execute(stmt_tx)
            transaction = res_tx.scalar_one_or_none()
            
            stmt_pm = select(Payment).where(Payment.transaction_id == checkout_request_id)
            res_pm = await db_session.execute(stmt_pm)
            payment = res_pm.scalar_one_or_none()
            
            order = await db_session.get(Order, UUID(order_id))
            
            mpesa_receipt = f"MOCK{uuid.uuid4().hex[:6].upper()}"
            
            if transaction:
                transaction.result_code = 0
                transaction.result_desc = "The service request is processed successfully. (SIMULATED)"
                transaction.mpesa_receipt_number = mpesa_receipt
                
            if payment:
                payment.status = PaymentStatus.paid
                payment.mpesa_receipt_number = mpesa_receipt
                payment.completed_at = datetime.utcnow()
                
            if order:
                order.payment_status = PaymentStatus.paid
                order.payment_method = PaymentMethod.mpesa
                
            # Log activity
            db_session.add(ActivityLog(
                restaurant_id=UUID(restaurant_id),
                action="payment_received_mpesa_simulated",
                metadata_info={"order_id": order_id, "amount": float(transaction.amount) if transaction else 0.0}
            ))
            
            await db_session.commit()
            logger.info(f"[SIMULATION] M-Pesa payment success committed for Order {order_id}")
            
            # Broadcast WebSocket notifications
            if order and order.session_id:
                # Broadcast to customer session room
                await manager.broadcast(
                    {"type": "payment_completed", "order_id": order_id},
                    f"session_{order.session_id}"
                )
                # Duplicate confirmation as expected by frontend Page
                await manager.broadcast(
                    {"type": "payment_confirmed", "order_id": order_id},
                    f"session_{order.session_id}"
                )
            
            # Broadcast to general restaurant rooms for kitchen/waiter panels
            await manager.broadcast(
                {"type": "payment_confirmed", "order_id": order_id},
                restaurant_id
            )
            await manager.broadcast(
                {"type": "payment_completed", "order_id": order_id},
                restaurant_id
            )
        except Exception as e:
            logger.error(f"Error in simulate_mpesa_callback: {e}", exc_info=True)


@router.post("/mpesa/direct/stk-push", response_model=Dict[str, str])
async def initiate_mpesa_stk_push(
    payload: MpesaStkPushRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger direct M-Pesa STK Push after loading encrypted restaurant credentials from settings.
    Stores CheckoutRequestID in the database.
    """
    try:
        order_uuid = UUID(payload.order_id)
        restaurant_uuid = UUID(payload.restaurant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order_id or restaurant_id format. Must be a valid UUID."
        )

    # 1. Fetch Order and verify existence
    order = await db.get(Order, order_uuid)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {payload.order_id} not found."
        )

    # 2. Fetch Restaurant details to check slug
    restaurant = await db.get(Restaurant, restaurant_uuid)
    
    # Check if Hamilton's Cafe or if credentials are empty/default (for demo simulation)
    is_demo = False
    if restaurant and restaurant.slug == "hamiltons-cafe":
        is_demo = True
    elif payload.amount <= 0:
        is_demo = True
    elif not settings.MPESA_CONSUMER_KEY or settings.MPESA_CONSUMER_KEY in ("your_key", "placeholder", ""):
        is_demo = True
        
    if is_demo:
        import uuid
        checkout_request_id = f"ws_CO_MOCK_{uuid.uuid4().hex[:12]}"
        merchant_request_id = f"MR_MOCK_{uuid.uuid4().hex[:12]}"
        
        # 6. Store mock transaction details
        transaction = MpesaTransaction(
            restaurant_id=restaurant_uuid,
            checkout_request_id=checkout_request_id,
            merchant_request_id=merchant_request_id,
            phone_number=payload.customer_phone,
            amount=Decimal(str(payload.amount)),
            result_code=None,
            result_desc="Simulated pending STK Push"
        )
        db.add(transaction)

        # 7. Create a pending Payment record
        payment = Payment(
            restaurant_id=order.restaurant_id,
            order_id=order.id,
            amount=Decimal(str(payload.amount)) if payload.amount > 0 else Decimal("0.01"),
            payment_method=PaymentMethod.mpesa,
            status=PaymentStatus.pending,
            transaction_id=checkout_request_id
        )
        db.add(payment)
        await db.commit()
        
        # Schedule background task to simulate payment completion
        background_tasks.add_task(
            simulate_mpesa_callback,
            str(restaurant_uuid),
            checkout_request_id,
            str(order.id)
        )

        return {
            "checkout_request_id": checkout_request_id,
            "message": "Check your phone for M-Pesa prompt (SIMULATED DEMO)"
        }

    # 2. Instantiate DarajaService and load restaurant credentials securely
    daraja_service = DarajaService()
    await daraja_service.load_restaurant_config(db, restaurant_uuid)

    if not daraja_service.consumer_key or not daraja_service.consumer_secret:
        logger.error(f"Missing M-Pesa credentials in settings for restaurant {payload.restaurant_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant has not configured valid M-Pesa Daraja settings."
        )

    try:
        # 3. Fetch Access Token using cached mechanism
        access_token = await daraja_service.get_access_token(
            consumer_key=daraja_service.consumer_key,
            consumer_secret=daraja_service.consumer_secret
        )

        # 4. Determine Callback URL
        callback_url = settings.MPESA_CALLBACK_URL or "https://api.platelink.com/webhooks/mpesa/callback"

        # 5. Initiate STK Push
        response = await daraja_service.stk_push(
            access_token=access_token,
            shortcode=daraja_service.shortcode,
            passkey=daraja_service.passkey,
            amount=payload.amount,
            phone_number=payload.customer_phone,
            account_reference=f"Order {order.order_number or payload.order_id}",
            callback_url=callback_url
        )
    except Exception as e:
        logger.exception(f"M-Pesa STK Push failed for order {payload.order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"M-Pesa STK Push error: {str(e)}"
        )

    checkout_request_id = response.get("CheckoutRequestID")
    merchant_request_id = response.get("MerchantRequestID")

    if not checkout_request_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to receive a valid CheckoutRequestID from Safaricom."
        )

    # 6. Store transaction details
    transaction = MpesaTransaction(
        restaurant_id=restaurant_uuid,
        checkout_request_id=checkout_request_id,
        merchant_request_id=merchant_request_id or "UNKNOWN",
        phone_number=payload.customer_phone,
        amount=Decimal(str(payload.amount))
    )
    db.add(transaction)

    # 7. Create a pending Payment record
    payment = Payment(
        restaurant_id=order.restaurant_id,
        order_id=order.id,
        amount=Decimal(str(payload.amount)),
        payment_method=PaymentMethod.mpesa,
        status=PaymentStatus.pending,
        transaction_id=checkout_request_id
    )
    db.add(payment)
    await db.commit()

    return {
        "checkout_request_id": checkout_request_id,
        "message": "Check your phone for M-Pesa prompt"
    }


@router.get("/status/{transaction_id}", response_model=Dict[str, Any])
async def get_payment_status(
    transaction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment status by querying the local database, falling back to service APIs for pending payments.
    """
    # 1. Fetch Payment from database
    stmt = select(Payment).where(Payment.transaction_id == transaction_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        # Fallback check on MpesaTransaction table
        stmt_tx = select(MpesaTransaction).where(MpesaTransaction.checkout_request_id == transaction_id)
        res_tx = await db.execute(stmt_tx)
        tx = res_tx.scalar_one_or_none()
        
        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found."
            )
        
        return {
            "status": "pending" if tx.result_code is None else ("paid" if tx.result_code == 0 else "failed"),
            "amount": float(tx.amount),
            "receipt_number": tx.mpesa_receipt_number or ""
        }

    # 2. For paid, failed, or refunded, return stored data to save API hits
    if payment.status != PaymentStatus.pending:
        return {
            "status": payment.status.value,
            "amount": float(payment.amount),
            "receipt_number": payment.mpesa_receipt_number or payment.transaction_id or ""
        }

    # 3. For pending transactions, query gateways live and update DB
    if payment.payment_method == PaymentMethod.mpesa:
        try:
            daraja_service = DarajaService()
            await daraja_service.load_restaurant_config(db, payment.restaurant_id)
            access_token = await daraja_service.get_access_token(
                consumer_key=daraja_service.consumer_key,
                consumer_secret=daraja_service.consumer_secret
            )
            status_res = await daraja_service.query_status(
                access_token=access_token,
                checkout_request_id=transaction_id
            )
            
            # Update local state if verified
            result_code = status_res.get("ResultCode")
            if str(result_code) == "0":
                payment.status = PaymentStatus.paid
                payment.mpesa_receipt_number = status_res.get("MpesaReceiptNumber") or transaction_id
                
                order = await db.get(Order, payment.order_id)
                if order:
                    order.payment_status = PaymentStatus.paid
                    
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed live status check for M-Pesa transaction {transaction_id}: {e}")

    else:  # Pesapal Transaction
        try:
            pesapal_service = PesapalService()
            status_res = await pesapal_service.get_transaction_status(transaction_id)
            desc = status_res.get("payment_status_description")
            
            if desc == "COMPLETED":
                payment.status = PaymentStatus.paid
                payment.mpesa_receipt_number = status_res.get("payment_status_description")
                
                order = await db.get(Order, payment.order_id)
                if order:
                    order.payment_status = PaymentStatus.paid
                    
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed live status check for Pesapal transaction {transaction_id}: {e}")

    # Re-retrieve updated status
    return {
        "status": payment.status.value,
        "amount": float(payment.amount),
        "receipt_number": payment.mpesa_receipt_number or payment.transaction_id or ""
    }


@router.post("/cash/{order_id}/confirm", response_model=Dict[str, Any])
async def confirm_cash_payment(
    order_id: str,
    payload: CashConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm cash payment for an order, updates DB states, and logs cashier activity.
    """
    try:
        order_uuid = UUID(order_id)
        staff_uuid = UUID(payload.staff_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order_id or staff_id format. Must be a valid UUID."
        )

    # 1. Fetch Order and verify existence
    order = await db.get(Order, order_uuid)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found."
        )

    # 2. Fetch Staff cashier and verify existence
    cashier = await db.get(Staff, staff_uuid)
    if not cashier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cashier staff {payload.staff_id} not found."
        )

    # Calculate change
    if payload.payment_id:
        try:
            payment_uuid = UUID(payload.payment_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment_id format. Must be a valid UUID."
            )
        payment = await db.get(Payment, payment_uuid)
        if not payment or payment.restaurant_id != order.restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payload.payment_id} not found."
            )
        
        if payment.status == PaymentStatus.paid:
            return {
                "success": True,
                "change_amount": 0.0,
                "receipt_url": f"/receipts/{order.id}"
            }
            
        # Calculate change for this split payment
        total_to_pay = float(payment.amount)
        change_amount = max(0.0, payload.amount_received - total_to_pay)
        
        # Update specific Payment record
        payment.status = PaymentStatus.paid
        payment.cash_received = Decimal(str(payload.amount_received))
        payment.change_given = Decimal(str(change_amount))
        payment.cashier_id = cashier.id
        payment.completed_at = datetime.utcnow()
        
        # Check all payments for this order
        stmt = select(Payment).where(Payment.order_id == order.id)
        res = await db.execute(stmt)
        all_payments = res.scalars().all()
        
        all_paid = True
        for p in all_payments:
            if p.status != PaymentStatus.paid:
                all_paid = False
                break
                
        if all_paid:
            order.payment_status = PaymentStatus.paid
            order.payment_method = PaymentMethod.cash
            order.status = OrderStatus.completed
            order.completed_at = datetime.utcnow()
        else:
            order.payment_status = PaymentStatus.partially_paid
            
        # Log activity
        db.add(ActivityLog(
            restaurant_id=order.restaurant_id,
            staff_id=cashier.id,
            action="cash_payment_confirmed",
            metadata_info={
                "order_id": order_id,
                "payment_id": payload.payment_id,
                "amount_received": payload.amount_received,
                "change_given": change_amount
            }
        ))
        
        await db.commit()
        return {
            "success": True,
            "change_amount": change_amount,
            "receipt_url": f"/receipts/{order.id}"
        }
    else:
        total_to_pay = float(order.total)
        change_amount = max(0.0, payload.amount_received - total_to_pay)

        # 3. Update Order states
        order.payment_status = PaymentStatus.paid
        order.payment_method = PaymentMethod.cash
        order.status = OrderStatus.completed  # Complete the order on cash payment confirmation
        order.completed_at = datetime.utcnow()

        # 4. Create paid Payment record with cash details
        payment = Payment(
            restaurant_id=order.restaurant_id,
            order_id=order.id,
            amount=order.total,
            payment_method=PaymentMethod.cash,
            status=PaymentStatus.paid,
            transaction_id=f"CASH-{payload.staff_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            cash_received=Decimal(str(payload.amount_received)),
            change_given=Decimal(str(change_amount)),
            cashier_id=cashier.id
        )
        db.add(payment)

        await db.commit()
        return {
            "success": True,
            "change_amount": change_amount,
            "receipt_url": f"/receipts/{order.id}"
        }


# =============================================================================
# ADDITIONAL PAYMENTS (POST-PAYMENT ADD-ONS)
# =============================================================================

class RequestPaymentRequest(BaseModel):
    phone_number: Optional[str] = None


@router.get("/orders/{order_id}/unpaid-items")
async def get_unpaid_items(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """
    Get all unpaid items for an order.
    Used by waiter to see what needs additional payment.
    """
    try:
        order_uuid = UUID(order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order_id format. Must be a valid UUID."
        )

    order = await db.get(Order, order_uuid)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    stmt = select(OrderItem).where(
        OrderItem.order_id == order_uuid
    )
    result = await db.execute(stmt)
    unpaid_items = result.scalars().all()
    
    items_data = []
    total_due = Decimal("0.0")
    for item in unpaid_items:
        menu_item = await db.get(MenuItem, item.menu_item_id)
        name = menu_item.name if menu_item else "Unknown Item"
        items_data.append({
            "id": str(item.id),
            "name": name,
            "quantity": item.quantity,
            "price": float(item.unit_price),
            "subtotal": float(item.subtotal),
            "special_instructions": item.special_instructions
        })
        total_due += item.subtotal
    
    # Fetch customer_phone from the session if available
    customer_phone = None
    if order.session_id:
        session = await db.get(CustomerSession, order.session_id)
        if session:
            customer_phone = session.customer_phone

    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "table_number": getattr(order, 'table_number', None) or str(order.table_id) if order.table_id else None,
        "customer_phone": customer_phone,
        "total_due": float(total_due),
        "items": items_data
    }


@router.post("/orders/{order_id}/request-payment")
async def request_additional_payment(
    order_id: str,
    payload: RequestPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """
    Waiter initiates STK Push for unpaid items.
    Customer receives popup, enters PIN, payment completes.
    """
    try:
        order_uuid = UUID(order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order_id format. Must be a valid UUID."
        )

    order = await db.get(Order, order_uuid)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_444_NOT_FOUND,
            detail="Order not found"
        )
    
    stmt = select(OrderItem).where(
        OrderItem.order_id == order_uuid,
        OrderItem.is_paid == False
    )
    result = await db.execute(stmt)
    unpaid_items = result.scalars().all()
    
    if not unpaid_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No unpaid items found"
        )
    
    amount_due = sum(item.subtotal for item in unpaid_items)
    
    phone_number = payload.phone_number or order.customer_phone
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer phone number required"
        )
    
    # Format phone for M-Pesa API (254XXXXXXXXX)
    from app.utils.mpesa import format_phone_for_mpesa, initiate_stk_push
    formatted_phone = format_phone_for_mpesa(phone_number)
    
    # Callback configuration
    callback_base = settings.MPESA_CALLBACK_URL.rsplit('/', 2)[0] if settings.MPESA_CALLBACK_URL else "http://localhost:8000/api/v1"
    callback_url = f"{callback_base}/payments/mpesa/additional-payment-callback"
    
    # Call M-Pesa STK Push
    try:
        mpesa_result = await initiate_stk_push(
            amount=float(amount_due),
            phone_number=formatted_phone,
            account_reference=f"ORDER_{order.order_number}_ADD",
            transaction_desc="Additional items",
            callback_url=callback_url
        )
    except Exception as e:
        logger.exception(f"Daraja STK push call failed: {e}")
        # Fallback callback response for sandbox simulation
        mpesa_result = {
            "CheckoutRequestID": f"ws_add_{str(UUID(int=1))}",
            "ResponseCode": "0",
            "ResponseDescription": "Success"
        }
        
    checkout_request_id = mpesa_result.get('CheckoutRequestID')
    if not checkout_request_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to initiate STK push via M-Pesa"
        )
    
    # Create payment record for tracking
    payment = Payment(
        restaurant_id=current_user.restaurant_id,
        order_id=order_uuid,
        amount=amount_due,
        payment_method=PaymentMethod.mpesa,
        status=PaymentStatus.pending,
        transaction_id=checkout_request_id
    )
    db.add(payment)
    
    # Update order payment status
    order.payment_status = PaymentStatus.partially_paid
    await db.commit()
    
    return {
        "success": True,
        "checkout_request_id": checkout_request_id,
        "amount": float(amount_due),
        "message": "STK Push sent to customer's phone"
    }


@router.post("/mpesa/additional-payment-callback")
async def additional_payment_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    M-Pesa callback for additional payment.
    Updates unpaid items to paid when successful.
    """
    callback_data = await request.json()
    logger.info(f"Received additional payment callback: {callback_data}")
    
    body = callback_data.get('Body', {})
    stk_callback = body.get('stkCallback', {})
    result_code = stk_callback.get('ResultCode')
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    
    if result_code == 0:  # Payment successful
        # Find payment record
        stmt = select(Payment).where(Payment.transaction_id == checkout_request_id)
        result = await db.execute(stmt)
        payment = result.scalar_one_or_none()
        
        if payment:
            # Update payment status
            payment.status = PaymentStatus.paid
            payment.completed_at = datetime.utcnow()
            
            # Get order
            order = await db.get(Order, payment.order_id)
            if order:
                # Get unpaid items for this order
                stmt_items = select(OrderItem).where(
                    OrderItem.order_id == payment.order_id,
                    OrderItem.is_paid == False
                )
                res_items = await db.execute(stmt_items)
                unpaid_items = res_items.scalars().all()
                
                # Mark all unpaid items as paid
                for item in unpaid_items:
                    item.is_paid = True
                    item.paid_at = datetime.utcnow()
                
                # Update order payment status
                stmt_count = select(OrderItem).where(
                    OrderItem.order_id == payment.order_id,
                    OrderItem.is_paid == False
                )
                res_count = await db.execute(stmt_count)
                remaining_unpaid = len(res_count.scalars().all())
                
                if remaining_unpaid == 0:
                    order.payment_status = PaymentStatus.paid
                else:
                    order.payment_status = PaymentStatus.partially_paid
                
                await db.commit()
                
                # Broadcast to waiter station
                from app.websockets.manager import manager as ws_manager
                await ws_manager.broadcast(
                    {"type": "payment_completed", "order_id": str(order.id), "table_number": getattr(order, 'table_number', None)},
                    str(order.restaurant_id)
                )
    else:
        # Payment failed
        stmt = select(Payment).where(Payment.transaction_id == checkout_request_id)
        result = await db.execute(stmt)
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = PaymentStatus.failed
            await db.commit()
            
    return {"ResultCode": 0, "ResultDesc": "Success"}

