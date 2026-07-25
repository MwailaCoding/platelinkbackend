# app/tasks/celery.py
from celery import Celery
from app.core.config import settings

celery_app = Celery("platelink", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.task_routes = {
    "app.tasks.worker.send_email_task": "main-queue",
    "app.tasks.worker.process_mpesa_payment": "payment-queue",
}

# app/tasks/worker.py
import asyncio
from app.tasks.celery import celery_app
from app.services.email import EmailService
from app.services.mpesa import MpesaService

@celery_app.task
def send_email_task(to_email: str, subject: str, body: str):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(EmailService.send_email(to_email, subject, body))

@celery_app.task
def process_refund_task(order_id: str):
    # Logic for triggering refund
    pass
