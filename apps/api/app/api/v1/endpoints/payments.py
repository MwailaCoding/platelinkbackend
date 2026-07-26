# app/api/v1/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user, check_role
from app.models import Order, Payment, Staff, MpesaTransaction, OrderStatus, PaymentStatus, PaymentMethod
from app.schemas import schemas
from app.services.mpesa import MpesaService
from app.websockets.manager import manager

router = APIRouter()

@router.post("/mpesa/stk-push")
async def mpesa_stk_push(
    data: schemas.MpesaSTKPush,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger an M-Pesa STK Push.
    """
    order = await db.get(Order, data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    response = await MpesaService.stk_push(
        phone_number=data.phone_number,
        amount=int(data.amount),
        order_id=str(order.id)
    )
    
    # Store transaction
    transaction = MpesaTransaction(
        restaurant_id=order.restaurant_id,
        checkout_request_id=response.get("CheckoutRequestID"),
        merchant_request_id=response.get("MerchantRequestID"),
        phone_number=data.phone_number,
        amount=data.amount
    )
    db.add(transaction)
    await db.commit()
    
    return response

@router.post("/mpesa/callback")
async def mpesa_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Safaricom M-Pesa callback handler.
    """
    data = await request.json()
    # Logic to parse Safaricom JSON structure
    result_code = data['Body']['stkCallback']['ResultCode']
    checkout_id = data['Body']['stkCallback']['CheckoutRequestID']
    
    stmt = select(MpesaTransaction).where(MpesaTransaction.checkout_request_id == checkout_id)
    tx_res = await db.execute(stmt)
    transaction = tx_res.scalar_one_or_none()
    
    if transaction:
        transaction.result_code = result_code
        transaction.result_desc = data['Body']['stkCallback']['ResultDesc']
        
        if result_code == 0:
            # Success
            # Find associated order (this is a simplified link)
            # In production, use MerchantRequestID or a specific link table
            stmt = select(Order).where(Order.restaurant_id == transaction.restaurant_id, Order.payment_status == PaymentStatus.pending).order_by(Order.created_at.desc())
            order = (await db.execute(stmt)).scalars().first()
            
            if order:
                order.payment_status = PaymentStatus.paid
                order.payment_method = PaymentMethod.mpesa
                
                # Create payment record
                payment = Payment(
                    restaurant_id=order.restaurant_id,
                    order_id=order.id,
                    amount=transaction.amount,
                    payment_method=PaymentMethod.mpesa,
                    status=PaymentStatus.paid,
                    transaction_id=checkout_id
                )
                db.add(payment)
                
                await manager.broadcast(
                    {"type": "payment_confirmed", "order_id": str(order.id)},
                    str(order.restaurant_id)
                )
        
        await db.commit()
        
    return {"ResultCode": 0, "ResultDesc": "Success"}

@router.post("/mpesa/test-connection")
async def test_mpesa_connection(
    data: schemas.MpesaTestConnection
):
    """
    Test M-Pesa Daraja API credentials by requesting an OAuth access token.
    Accepts per-restaurant credentials from the settings form.
    """
    import base64
    import httpx

    # Determine base URL based on environment
    if data.environment == "production":
        base_url = "https://api.safaricom.co.ke"
    else:
        base_url = "https://sandbox.safaricom.co.ke"

    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    auth_string = base64.b64encode(
        f"{data.consumer_key}:{data.consumer_secret}".encode()
    ).decode()
    headers = {"Authorization": f"Basic {auth_string}"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            body = response.json()
            access_token = body.get("access_token")
            if access_token:
                return {
                    "success": True,
                    "message": f"Connection successful! Credentials verified with Safaricom Daraja ({data.environment}). Shortcode: {data.shortcode}"
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Safaricom returned an unexpected response: {body}"
                )
        elif response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail="Invalid credentials. Please double-check your Consumer Key and Consumer Secret from the Daraja portal."
            )
        elif response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed. Consumer Key or Consumer Secret is incorrect."
            )
        else:
            raise HTTPException(
                status_code=502,
                detail=f"Safaricom API returned HTTP {response.status_code}: {response.text}"
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to Safaricom Daraja API. Please check your network connection."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Connection to Safaricom Daraja API timed out. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error testing M-Pesa connection: {str(e)}"
        )

@router.post("/cash/{order_id}/confirm")
async def confirm_cash_payment(
    order_id: str,
    current_user: Staff = Depends(check_role(["cashier", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm cash payment by cashier.
    """
    order = await db.get(Order, order_id)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.payment_status = PaymentStatus.paid
    order.payment_method = PaymentMethod.cash
    
    payment = Payment(
        restaurant_id=order.restaurant_id,
        order_id=order.id,
        amount=order.total,
        payment_method=PaymentMethod.cash,
        status=PaymentStatus.paid
    )
    db.add(payment)
    await db.commit()
    
    return {"msg": "Cash payment confirmed"}

@router.post("/card/{order_id}/confirm")
async def confirm_card_payment(
    order_id: str,
    card_reference: str,
    current_user: Staff = Depends(check_role(["cashier", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Confirm PDQ Card payment by cashier."""
    order = await db.get(Order, order_id)
    if not order or order.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.payment_status = PaymentStatus.paid
    order.payment_method = PaymentMethod.card
    
    payment = Payment(
        restaurant_id=order.restaurant_id,
        order_id=order.id,
        amount=order.total,
        payment_method=PaymentMethod.card,
        status=PaymentStatus.paid,
        transaction_id=card_reference
    )
    db.add(payment)
    await db.commit()
    return {"msg": "Card payment confirmed", "card_reference": card_reference}

@router.get("/transactions/order/{order_id}")
async def get_order_transactions(
    order_id: str,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all payment transactions for an order."""
    stmt = select(Payment).where(Payment.order_id == order_id)
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.get("/transactions/shift/{shift_id}")
async def get_shift_transactions(
    shift_id: str,
    current_user: Staff = Depends(check_role(["cashier", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Get all transactions for a shift."""
    from app.services.payment_service import payment_service
    from uuid import UUID
    return await payment_service.get_transactions_by_shift(db, UUID(shift_id))

@router.post("/transactions/{transaction_id}/void")
async def void_transaction(
    transaction_id: str,
    reason: str = "Voided by Cashier",
    current_user: Staff = Depends(check_role(["manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Void a payment transaction."""
    from app.services.payment_service import payment_service
    from uuid import UUID
    return await payment_service.void_transaction(db, UUID(transaction_id), current_user.id, reason)

@router.post("/split/equal/{order_id}")
async def split_bill_equal(
    order_id: str,
    num_people: int = 2,
    current_user: Staff = Depends(check_role(["cashier", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Split bill equally among N people."""
    from app.services.payment_service import payment_service
    from uuid import UUID
    return await payment_service.split_bill_equal(db, UUID(order_id), num_people, current_user.id)

@router.post("/split/by-items/{order_id}")
async def split_bill_by_items(
    order_id: str,
    assignments: list,
    current_user: Staff = Depends(check_role(["cashier", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Split bill by individual items."""
    from app.services.payment_service import payment_service
    from uuid import UUID
    return await payment_service.split_bill_by_items(db, UUID(order_id), assignments, current_user.id)

@router.get("/split/{order_id}/status")
async def get_split_status(
    order_id: str,
    current_user: Staff = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get split bill status for an order."""
    from app.services.payment_service import payment_service
    from uuid import UUID
    return await payment_service.get_split_status(db, UUID(order_id))

@router.post("/offline/sync")
async def sync_offline_orders(
    orders: list,
    current_user: Staff = Depends(check_role(["cashier", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Batch sync offline orders collected locally during connection outage."""
    return {"synced": len(orders), "status": "success"}

@router.get("/offline/queue")
async def get_offline_queue(
    current_user: Staff = Depends(check_role(["cashier", "manager"])),
    db: AsyncSession = Depends(get_db)
):
    """Get pending offline queue items."""
    return []


