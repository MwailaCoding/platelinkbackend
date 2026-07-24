"""Email sending service with SMTP and HTML templates support."""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
APP_NAME = os.getenv("APP_NAME", "PlateLink")

async def send_email(
    to: str,
    subject: str,
    body: str,
    html_content: Optional[str] = None
) -> bool:
    """Send email via SMTP."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.info(f"[EMAIL MOCK] To: {to} | Subject: {subject}\nBody:\n{body}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{APP_NAME} <{SMTP_USER}>"
        msg["To"] = to

        msg.attach(MIMEText(body, "plain"))
        if html_content:
            msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to, msg.as_string())

        logger.info(f"Email sent successfully to {to}")
        return True
    except Exception as err:
        logger.error(f"Failed to send email to {to}: {err}")
        return False

async def send_invitation_email(
    to: str,
    first_name: str,
    last_name: str,
    restaurant_name: str,
    role_name: str,
    invite_url: str,
    pin: str
) -> bool:
    """Send staff invitation email."""
    subject = f"Invitation to join {restaurant_name} on {APP_NAME}"
    body = (
        f"Hi {first_name} {last_name},\n\n"
        f"You have been invited to join {restaurant_name} as a {role_name}.\n\n"
        f"Your login PIN is: {pin}\n"
        f"Please click the link below to accept your invitation and activate your account:\n"
        f"{invite_url}\n\n"
        f"Best regards,\n"
        f"The {restaurant_name} Team"
    )
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Invitation to join {restaurant_name}</h2>
        <p>Hi <strong>{first_name} {last_name}</strong>,</p>
        <p>You have been invited to join <strong>{restaurant_name}</strong> as a <strong>{role_name}</strong>.</p>
        <p>Your 4-digit staff PIN is: <strong style="font-size: 18px; color: #4F46E5;">{pin}</strong></p>
        <p><a href="{invite_url}" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Accept Invitation</a></p>
        <br/>
        <p>Best regards,<br/>{restaurant_name} Team</p>
      </body>
    </html>
    """
    return await send_email(to, subject, body, html)

async def send_welcome_email(
    to: str,
    first_name: str,
    last_name: str,
    restaurant_name: str,
    login_url: str,
    pin: str
) -> bool:
    """Send welcome email to activated staff member."""
    subject = f"Welcome to {restaurant_name} on {APP_NAME}"
    body = (
        f"Hi {first_name} {last_name},\n\n"
        f"Welcome to {restaurant_name}! Your staff account is active.\n"
        f"Your login PIN is: {pin}\n\n"
        f"Login here: {login_url}\n"
    )
    return await send_email(to, subject, body)
