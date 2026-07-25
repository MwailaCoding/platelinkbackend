# app/tasks/worker.py
import asyncio
import logging
from app.core.celery_app import celery_app
from app.services.email import EmailService
from app.services.mpesa import MpesaService
from app.utils.sms import send_sms
from app.db.session import async_session_local
from app.models import Order, Restaurant, MenuItem, CustomerSession, Table, SessionStatus, TableStatus, Payment, OrderStatus, PaymentStatus, Staff
from sqlalchemy import select, func
from datetime import datetime, date, timedelta

logger = logging.getLogger("platelink")

@celery_app.task(bind=True, max_retries=3)
def send_welcome_email_task(self, to_email: str, restaurant_name: str, owner_name: str, login_url: str):
    """
    Sends a welcome email to the restaurant owner.
    """
    try:
        subject = f"Welcome to PlateLink Africa - {restaurant_name}"
        html_content = f"""
        <html>
            <body>
                <h1>Welcome {owner_name}!</h1>
                <p>Thank you for choosing PlateLink Africa for {restaurant_name}.</p>
                <p>You can log in to your dashboard here: <a href="{login_url}">{login_url}</a></p>
                <p>Read our getting started guide: <a href="https://docs.platelink.africa/getting-started">Getting Started</a></p>
            </body>
        </html>
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(EmailService.send_email(to_email, subject, html_content))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@celery_app.task
def send_order_confirmation_sms(phone: str, order_number: str, total: float):
    asyncio.run(send_sms(phone, f"Order {order_number} confirmed. Total: KES {total}. Thank you!"))

@celery_app.task
def generate_daily_sales_report():
    async def _report():
        async with async_session_local() as db:
            today = date.today()
            # Iterate over all restaurants
            rest_stmt = select(Restaurant)
            restaurants = (await db.execute(rest_stmt)).scalars().all()
            
            for rest in restaurants:
                stmt = select(func.sum(Order.total)).where(Order.restaurant_id == rest.id, func.cast(Order.created_at, date) == today)
                total_sales = (await db.execute(stmt)).scalar() or 0
                
                stmt_staff = select(Staff).where(Staff.restaurant_id == rest.id, Staff.role.in_(["owner", "manager"]))
                managers = (await db.execute(stmt_staff)).scalars().all()
                for manager in managers:
                    if manager.email:
                        await EmailService.send_email(
                            manager.email,
                            f"Daily Sales Report - {today} - {rest.name}",
                            f"<h1>Daily Sales Report for {rest.name}</h1><p>Total sales for today: KES {total_sales}</p>"
                        )
    asyncio.run(_report())

@celery_app.task
def cleanup_expired_sessions():
    """
    Cleans up expired or old closed sessions and frees up tables.
    """
    async def _cleanup():
        async with async_session_local() as db:
            expired_time = datetime.utcnow() - timedelta(hours=24)
            stmt = select(CustomerSession).where(
                (CustomerSession.status == SessionStatus.expired) |
                ((CustomerSession.created_at < expired_time) & (CustomerSession.status == SessionStatus.closed))
            )
            result = await db.execute(stmt)
            sessions = result.scalars().all()
            
            deleted_count = 0
            tables_updated = 0
            for session in sessions:
                table_stmt = select(Table).where(Table.id == session.table_id, Table.current_session_id == session.id)
                table = (await db.execute(table_stmt)).scalar_one_or_none()
                if table:
                    table.status = TableStatus.available
                    table.occupied_since = None
                    table.current_session_id = None
                    tables_updated += 1
                await db.delete(session)
                deleted_count += 1
            await db.commit()
            return {"sessions_deleted": deleted_count, "tables_updated": tables_updated}
    return asyncio.run(_cleanup())

@celery_app.task
def process_refund_task(payment_id: str, amount: float, reason: str):
    """
    Processes a refund for a payment.
    """
    async def _process():
        async with async_session_local() as db:
            payment = await db.get(Payment, payment_id)
            if not payment: return
            
            if payment.payment_method.value == "mpesa":
                await MpesaService.reverse_transaction(payment.transaction_id, amount, reason)
            
            payment.status = PaymentStatus.refunded
            order = await db.get(Order, payment.order_id)
            if order:
                order.payment_status = PaymentStatus.refunded
                order.status = OrderStatus.cancelled
                # Send SMS
                if order.session:
                    await send_sms(order.session.customer_phone, f"Your refund of KES {amount} for order {order.order_number} has been processed.")
            
            await db.commit()
            logger.info(f"Refunded {amount} for {payment_id}: {reason}")
    asyncio.run(_process())

@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
def retry_pesapal_webhook_task(self, payload: dict):
    """
    Celery task to retry failed Pesapal webhooks with automatic exponential backoff.
    """
    async def _process():
        from app.services.pesapal_service import PesapalService
        from app.models import Order, Payment, Restaurant, PaymentStatus, OrderStatus
        from app.api.v1.websockets.connection_manager import manager as ws_manager
        from sqlalchemy import select
        
        order_tracking_id = payload.get("order_tracking_id")
        payment_status = payload.get("payment_status")
        
        async with async_session_local() as db:
            # Check idempotency
            stmt = select(Payment).where(Payment.transaction_id == order_tracking_id)
            payment = (await db.execute(stmt)).scalar_one_or_none()
            
            if payment and payment.status == PaymentStatus.paid:
                logger.info(f"Pesapal webhook {order_tracking_id} already completed. Skipping.")
                return
                
            if not payment:
                raise ValueError(f"Payment with tracking ID {order_tracking_id} not found in database.")
                
            order = await db.get(Order, payment.order_id)
            if not order:
                raise ValueError(f"Order {payment.order_id} not found in database.")
                
            if payment_status == "COMPLETED":
                payment.status = PaymentStatus.paid
                order.payment_status = PaymentStatus.paid
                
                # Calculate platform fee (1%)
                platform_fee = float(order.total) * 0.01
                net_amount = float(order.total) - platform_fee
                
                # Retrieve restaurant payout phone
                restaurant = await db.get(Restaurant, order.restaurant_id)
                recipient_phone = restaurant.phone if restaurant else None
                
                if recipient_phone:
                    try:
                        pesapal_service = PesapalService()
                        await pesapal_service.initiate_transfer(
                            recipient_phone=recipient_phone,
                            amount=net_amount,
                            narrative=f"Payout for Order {order.order_number}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to initiate Pesapal payout transfer: {e}")
                        raise e
                
                # Notify kitchen via Websocket
                await ws_manager.broadcast_to_kitchen(str(order.restaurant_id), {
                    "type": "new_order",
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "total": float(order.total)
                })
                
            await db.commit()
            
    try:
        asyncio.run(_process())
    except Exception as exc:
        logger.warning(f"Error processing Pesapal webhook, retrying: {exc}")
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 900))

@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
def retry_mpesa_webhook_task(self, payload: dict):
    """
    Celery task to retry failed M-Pesa webhooks with automatic exponential backoff.
    """
    async def _process():
        from app.models import Order, Payment, MpesaTransaction, PaymentStatus, OrderStatus
        from app.api.v1.websockets.connection_manager import manager as ws_manager
        from sqlalchemy import select
        
        checkout_request_id = payload.get("CheckoutRequestID")
        result_code = payload.get("ResultCode")
        result_desc = payload.get("ResultDesc")
        receipt_number = payload.get("MpesaReceiptNumber")
        
        async with async_session_local() as db:
            # Check idempotency
            stmt = select(MpesaTransaction).where(MpesaTransaction.checkout_request_id == checkout_request_id)
            tx = (await db.execute(stmt)).scalar_one_or_none()
            
            if tx and tx.result_code == 0:
                logger.info(f"Mpesa transaction {checkout_request_id} already processed. Skipping.")
                return
                
            if not tx:
                raise ValueError(f"M-Pesa transaction {checkout_request_id} not found in database.")
                
            tx.result_code = result_code
            tx.result_desc = result_desc
            tx.mpesa_receipt_number = receipt_number
            
            # Find Payment
            stmt_p = select(Payment).where(Payment.transaction_id == checkout_request_id)
            payment = (await db.execute(stmt_p)).scalar_one_or_none()
            
            if result_code == 0:
                if payment:
                    payment.status = PaymentStatus.paid
                    payment.mpesa_receipt_number = receipt_number
                    
                # Update Order
                order_id = payment.order_id if payment else None
                if order_id:
                    order = await db.get(Order, order_id)
                    if order:
                        order.payment_status = PaymentStatus.paid
                        
                        # Notify kitchen via WebSocket
                        await ws_manager.broadcast_to_kitchen(str(order.restaurant_id), {
                            "type": "new_order",
                            "order_id": str(order.id),
                            "order_number": order.order_number,
                            "total": float(order.total)
                        })
            else:
                if payment:
                    payment.status = PaymentStatus.failed
            
            await db.commit()
            
    try:
        asyncio.run(_process())
    except Exception as exc:
        logger.warning(f"Error processing M-Pesa webhook, retrying: {exc}")
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 900))

@celery_app.task(bind=True, max_retries=3)
def schedule_next_course(self, order_id: str, course_num: int):
    """Celery task to fire next course after delay"""
    async def _process():
        from app.models import Order, OrderItem, RestaurantSetting
        from sqlalchemy import select
        from app.api.v1.websockets.connection_manager import manager as ws_manager
        
        async with async_session_local() as db:
            order = await db.get(Order, order_id)
            if not order or order.pacing_preference != 'in_courses':
                return
            
            # Fire the course
            stmt = select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.course_number == course_num,
                OrderItem.is_fired == False
            )
            items = (await db.execute(stmt)).scalars().all()
            for item in items:
                item.is_fired = True
                item.fired_at = datetime.utcnow()
                
            await db.commit()
            
            if items:
                # Broadcast
                await ws_manager.broadcast_to_kitchen(str(order.restaurant_id), {
                    "type": "course.fired",
                    "order_id": str(order_id),
                    "course": course_num
                })
            
            # Schedule next if exists
            all_items_stmt = select(OrderItem).where(OrderItem.order_id == order_id)
            all_items = (await db.execute(all_items_stmt)).scalars().all()
            max_course = max([i.course_number for i in all_items]) if all_items else 3
            
            if course_num < max_course:
                # get delay
                delay_stmt = select(RestaurantSetting).where(
                    RestaurantSetting.restaurant_id == order.restaurant_id,
                    RestaurantSetting.key == 'auto_fire_delay_minutes'
                )
                delay_setting = (await db.execute(delay_stmt)).scalar_one_or_none()
                delay_minutes = 15
                if delay_setting and 'value' in delay_setting.value:
                    delay_minutes = int(delay_setting.value.get('value', 15))
                
                # We schedule the next one
                schedule_next_course.apply_async(
                    args=[order_id, course_num + 1],
                    countdown=delay_minutes * 60
                )
    try:
        asyncio.run(_process())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


