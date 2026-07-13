# app/services/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

class EmailService:
    @staticmethod
    async def send_email(to_email: str, subject: str, body: str):
        if not settings.SMTP_HOST:
            return
        
        msg = MIMEMultipart()
        msg['From'] = settings.EMAILS_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

    @staticmethod
    async def send_verification_code(email: str, code: str):
        subject = "PlateLink Africa - Verification Code"
        body = f"Your verification code is: <b>{code}</b>. It expires in 15 minutes."
        await EmailService.send_email(email, subject, body)
