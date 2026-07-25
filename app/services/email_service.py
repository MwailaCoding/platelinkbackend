"""Email Service for sending clean, emoji-free transactional emails."""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT or 587
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL or "noreply@platelink.africa"
        self.from_name = settings.EMAILS_FROM_NAME or "PlateLink Africa"

    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Internal helper to send email via SMTP."""
        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            logger.warning(f"SMTP not configured. Suppressing email to {to_email}. Subject: {subject}")
            logger.info(f"[SIMULATED EMAIL TO {to_email}]\nSubject: {subject}\nContent:\n{html_content}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, [to_email], msg.as_string())

            logger.info(f"Email successfully sent to {to_email} with subject: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_verification_email(self, to_email: str, verification_code: str, verification_url: str) -> bool:
        """Send verification code & link to user."""
        subject = f"Verify your PlateLink account - Verification Code: {verification_code}"
        
        text_body = f"""
Verify Your Email Address - PlateLink Africa

Welcome to PlateLink Africa. Please verify your email address to activate your restaurant account.

Your Verification Code: {verification_code}

Or click the link below to verify automatically:
{verification_url}

This verification code will expire in 15 minutes.

PlateLink Africa
support@platelink.africa
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0A0F1D; color: #E2E8F0; margin: 0; padding: 40px 20px; }}
    .container {{ max-width: 580px; margin: 0 auto; background: #1C2541; border-radius: 16px; border: 1px solid #334155; padding: 32px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
    .logo-badge {{ display: inline-block; background: linear-gradient(135deg, #F97316, #F59E0B); color: #FFFFFF; font-weight: 900; font-size: 20px; width: 44px; height: 44px; line-height: 44px; text-align: center; border-radius: 12px; margin-bottom: 20px; }}
    h1 {{ color: #FFFFFF; font-size: 22px; font-weight: 800; margin-top: 0; }}
    p {{ font-size: 14px; line-height: 1.6; color: #94A3B8; }}
    .code-box {{ background: #0B132B; border: 1px solid #F97316; border-radius: 12px; text-align: center; padding: 20px; margin: 28px 0; }}
    .otp-code {{ font-family: 'Courier New', monospace; font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #F97316; }}
    .btn {{ display: inline-block; background: linear-gradient(90deg, #F97316, #F59E0B); color: #FFFFFF; font-weight: bold; text-decoration: none; padding: 14px 28px; border-radius: 12px; font-size: 14px; margin-top: 10px; }}
    .footer {{ border-top: 1px solid #334155; margin-top: 32px; padding-top: 20px; font-size: 12px; color: #64748B; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="logo-badge">P</div>
    <h1>Verify Your Email Address</h1>
    <p>Welcome to <strong>PlateLink Africa</strong>. Please verify your email address to complete your registration and activate your restaurant account.</p>
    
    <div class="code-box">
      <div class="otp-code">{verification_code}</div>
    </div>

    <p style="text-align: center;">Or click the button below to verify automatically:</p>
    
    <div style="text-align: center; margin: 20px 0;">
      <a href="{verification_url}" class="btn">Verify Email Address</a>
    </div>

    <p style="font-size: 12px; color: #64748B;">This code and verification link will expire in <strong>15 minutes</strong>. If you did not create a PlateLink account, please ignore this email.</p>
    
    <div class="footer">
      PlateLink Africa. Powering Restaurants Across Kenya and East Africa.<br>
      Need help? Contact support at <a href="mailto:support@platelink.africa" style="color: #F97316;">support@platelink.africa</a>
    </div>
  </div>
</body>
</html>"""

        return self._send_email(to_email, subject, html_body, text_body)

    def send_owner_welcome_email(
        self,
        to_email: str,
        owner_name: str,
        restaurant_name: str,
        scale: str,
        branch_structure: str,
        dashboard_url: str
    ) -> bool:
        """Send welcoming email to restaurant owner after onboarding."""
        subject = f"Welcome to PlateLink - {restaurant_name} Account Activated"
        
        text_body = f"""
Welcome to PlateLink, {owner_name}!

Congratulations! {restaurant_name} is now fully set up on PlateLink.

Setup Summary:
- Restaurant Name: {restaurant_name}
- Establishment Scale: {scale.upper()}
- Branch Structure: {branch_structure}
- M-Pesa Express: Connected

Access your Admin Dashboard here:
{dashboard_url}

Next Steps:
1. Print and place table QR stands.
2. Invite staff members from the Staff menu.
3. Perform a test order on mobile POS.

PlateLink Africa Support
support@platelink.africa
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0A0F1D; color: #E2E8F0; margin: 0; padding: 40px 20px; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #1C2541; border-radius: 16px; border: 1px solid #334155; padding: 36px; }}
    .hero-badge {{ background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #10B981; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; display: inline-block; margin-bottom: 16px; }}
    h1 {{ color: #FFFFFF; font-size: 24px; font-weight: 800; margin: 0 0 10px 0; }}
    p {{ font-size: 14px; line-height: 1.6; color: #94A3B8; }}
    .summary-card {{ background: #0B132B; border-radius: 12px; border: 1px solid #334155; padding: 20px; margin: 24px 0; }}
    .summary-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1E293B; font-size: 13px; }}
    .summary-row:last-child {{ border-bottom: none; }}
    .btn {{ display: inline-block; background: linear-gradient(90deg, #F97316, #F59E0B); color: #FFFFFF; font-weight: bold; text-decoration: none; padding: 14px 28px; border-radius: 12px; font-size: 14px; text-align: center; }}
    .footer {{ border-top: 1px solid #334155; margin-top: 32px; padding-top: 20px; font-size: 12px; color: #64748B; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <span class="hero-badge">Onboarding Complete</span>
    <h1>Welcome to PlateLink, {owner_name}</h1>
    <p>Congratulations! <strong>{restaurant_name}</strong> is now live on PlateLink. Your digital menu, POS system, and M-Pesa payment gateway are ready to accept customer orders.</p>

    <div class="summary-card">
      <h3 style="color: #FFFFFF; margin-top: 0; font-size: 14px; border-bottom: 1px solid #334155; padding-bottom: 8px;">Your Setup Summary</h3>
      <div class="summary-row">
        <span style="color: #64748B;">Restaurant Name:</span>
        <strong style="color: #FFFFFF;">{restaurant_name}</strong>
      </div>
      <div class="summary-row">
        <span style="color: #64748B;">Establishment Scale:</span>
        <strong style="color: #F97316; text-transform: uppercase;">{scale}</strong>
      </div>
      <div class="summary-row">
        <span style="color: #64748B;">Branch Structure:</span>
        <strong style="color: #10B981;">{branch_structure}</strong>
      </div>
      <div class="summary-row">
        <span style="color: #64748B;">M-Pesa Gateway:</span>
        <strong style="color: #10B981;">Connected</strong>
      </div>
    </div>

    <div style="text-align: center; margin: 28px 0;">
      <a href="{dashboard_url}" class="btn">Open Admin Dashboard</a>
    </div>

    <div style="background: rgba(249, 115, 22, 0.1); border-left: 4px solid #F97316; padding: 14px; border-radius: 8px; margin-top: 24px;">
      <strong style="color: #F97316; font-size: 13px;">Next Steps:</strong>
      <p style="margin: 4px 0 0 0; font-size: 12px; color: #CBD5E1;">1. Print and place table QR stands.<br>2. Invite staff members from the Staff menu.<br>3. Run a test order on mobile POS.</p>
    </div>

    <div class="footer">
      PlateLink Africa. Nairobi, Kenya.<br>
      Questions or technical support? Reply to this email or contact support@platelink.africa.
    </div>
  </div>
</body>
</html>"""

        return self._send_email(to_email, subject, html_body, text_body)

    def send_staff_invite_email(
        self,
        to_email: str,
        staff_name: str,
        restaurant_name: str,
        role_name: str,
        branch_name: str,
        pin_code: str,
        pos_url: str
    ) -> bool:
        """Send invitation email to newly invited staff member."""
        subject = f"Staff Invitation - Join {restaurant_name} on PlateLink"

        text_body = f"""
Welcome to the Team, {staff_name}!

You have been invited to join {restaurant_name} on the PlateLink POS & Ordering System.

Assigned Role: {role_name}
Assigned Branch: {branch_name}
Quick Access PIN: {pin_code}

Access the Mobile POS App here:
{pos_url}

Please keep your 4-digit PIN confidential.

PlateLink Africa
support@platelink.africa
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0A0F1D; color: #E2E8F0; margin: 0; padding: 40px 20px; }}
    .container {{ max-width: 580px; margin: 0 auto; background: #1C2541; border-radius: 16px; border: 1px solid #334155; padding: 32px; }}
    h1 {{ color: #FFFFFF; font-size: 22px; font-weight: 800; margin-top: 0; }}
    p {{ font-size: 14px; line-height: 1.6; color: #94A3B8; }}
    .role-card {{ background: #0B132B; border-radius: 12px; border: 1px solid #F97316; padding: 20px; margin: 24px 0; text-align: center; }}
    .role-title {{ font-size: 18px; font-weight: 800; color: #F97316; margin-bottom: 6px; }}
    .pin-badge {{ font-family: 'Courier New', monospace; font-size: 24px; font-weight: bold; background: #1E293B; color: #10B981; padding: 8px 20px; border-radius: 8px; display: inline-block; margin-top: 10px; }}
    .btn {{ display: inline-block; background: linear-gradient(90deg, #F97316, #F59E0B); color: #FFFFFF; font-weight: bold; text-decoration: none; padding: 14px 28px; border-radius: 12px; font-size: 14px; }}
    .footer {{ border-top: 1px solid #334155; margin-top: 32px; padding-top: 20px; font-size: 12px; color: #64748B; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Welcome to the Team, {staff_name}</h1>
    <p>You have been invited to join the team at <strong>{restaurant_name}</strong> on the PlateLink POS and Ordering System.</p>

    <div class="role-card">
      <div class="role-title">Assigned Role: {role_name}</div>
      <p style="margin: 0; font-size: 12px; color: #94A3B8;">Branch: {branch_name}</p>
      <div style="margin-top: 14px;">
        <span style="font-size: 11px; color: #64748B; display: block;">Your Quick Access PIN:</span>
        <span class="pin-badge">{pin_code}</span>
      </div>
    </div>

    <div style="text-align: center; margin: 28px 0;">
      <a href="{pos_url}" class="btn">Access Mobile POS App</a>
    </div>

    <p style="font-size: 12px; color: #64748B;">Please keep your PIN confidential. Do not share your login credentials with anyone.</p>

    <div class="footer">
      PlateLink Africa.<br>
      Need assistance? Contact your manager or email <a href="mailto:support@platelink.africa" style="color: #F97316;">support@platelink.africa</a>
    </div>
  </div>
</body>
</html>"""

        return self._send_email(to_email, subject, html_body, text_body)

email_service = EmailService()

class BrevoEmailService(EmailService):
    """Compatibility wrapper for BrevoEmailService expected by auth endpoints."""
    def send_verification_otp(self, email: str, otp: str, verification_url: Optional[str] = None) -> bool:
        url = verification_url or f"https://admin.platelink.africa/verify-email?email={email}&code={otp}"
        return self.send_verification_email(email, otp, url)

    def send_welcome_email(self, email: str, name: str, restaurant_name: str) -> bool:
        return self.send_owner_welcome_email(
            to_email=email,
            owner_name=name,
            restaurant_name=restaurant_name,
            scale="medium",
            branch_structure="Single Outlet",
            dashboard_url="https://admin.platelink.africa/dashboard"
        )

