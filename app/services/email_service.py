# app/services/email_service.py
import os
import secrets
import logging
from typing import Optional, Dict, Any
from fastapi import BackgroundTasks
import httpx
from redis.asyncio import Redis

from app.core.config import settings

# Initialize logging for the email service
logger = logging.getLogger("app.services.email_service")

class BrevoEmailService:
    """
    Complete production email service for PlateLink Africa using Brevo Transactional Email API.
    Supports OTP generation, storage/verification in Redis, rate limiting, and premium inline HTML templates.
    """
    
    def __init__(self) -> None:
        # Load API key and sender information from environment variables or settings
        self.api_key = os.getenv("BREVO_API_KEY") or getattr(settings, "BREVO_API_KEY", None)
        self.sender_email = os.getenv("BREVO_SENDER_EMAIL") or getattr(settings, "BREVO_SENDER_EMAIL", None) or "no-reply@platelink.africa"
        self.sender_name = os.getenv("BREVO_SENDER_NAME") or getattr(settings, "BREVO_SENDER_NAME", None) or "PlateLink Africa"
        self.redis_url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        if not self.api_key or self.api_key == "placeholder_api_key":
            logger.warning("BREVO_API_KEY is not configured or is a placeholder. Emails will not be sent.")

    async def _send_email_api(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        template_id: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Private helper method to execute the raw HTTP POST request to Brevo API.
        """
        # Check if we should use standard SMTP fallback directly
        use_smtp = not self.api_key or self.api_key == "placeholder_api_key" or "suspend" in self.api_key or not (self.api_key.startswith("xkeysib") or self.api_key.startswith("xsmtpsib"))

        if use_smtp:
            if settings.SMTP_HOST:
                logger.info("Brevo API key not available or invalid. Falling back to SMTP for %s", to_email)
                try:
                    from app.services.email import EmailService
                    await EmailService.send_email(to_email, subject, html_content)
                    return True
                except Exception as e:
                    logger.error("SMTP fallback failed to send email: %s", str(e))
                    return False
            logger.error("Brevo API key is not configured and no SMTP host fallback is available.")
            return False

        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Build payload matching Brevo API specification
        payload: Dict[str, Any] = {
            "to": [{"email": to_email, "name": to_name}]
        }

        if template_id is not None:
            payload["templateId"] = template_id
            if params:
                payload["params"] = params
            if subject:
                payload["subject"] = subject
        else:
            payload["subject"] = subject
            payload["htmlContent"] = html_content
            payload["sender"] = {
                "name": self.sender_name,
                "email": self.sender_email
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
                if response.status_code in (200, 201, 202):
                    logger.info("Email successfully sent to %s via Brevo. Response: %s", to_email, response.text)
                    return True
                else:
                    logger.error(
                        "Failed to send email to %s via Brevo. Status: %s, Response: %s",
                        to_email, response.status_code, response.text
                    )
                    # Trigger SMTP fallback on Brevo API failure
                    if settings.SMTP_HOST:
                        logger.info("Brevo API failed. Falling back to standard SMTP for %s", to_email)
                        try:
                            from app.services.email import EmailService
                            await EmailService.send_email(to_email, subject, html_content)
                            return True
                        except Exception as smtp_exc:
                            logger.error("SMTP fallback failed after Brevo failure: %s", str(smtp_exc))
                    return False
        except httpx.RequestError as exc:
            logger.error("HTTP error occurred while calling Brevo API for %s: %s", to_email, str(exc))
            # Trigger SMTP fallback on Brevo HTTP error
            if settings.SMTP_HOST:
                logger.info("Brevo API HTTP error. Falling back to standard SMTP for %s", to_email)
                try:
                    from app.services.email import EmailService
                    await EmailService.send_email(to_email, subject, html_content)
                    return True
                except Exception as smtp_exc:
                    logger.error("SMTP fallback failed after Brevo HTTP error: %s", str(smtp_exc))
            return False
        except Exception as exc:
            logger.exception("Unexpected error occurred while sending email to %s: %s", to_email, str(exc))
            # Trigger SMTP fallback on other errors
            if settings.SMTP_HOST:
                logger.info("Brevo unexpected error. Falling back to standard SMTP for %s", to_email)
                try:
                    from app.services.email import EmailService
                    await EmailService.send_email(to_email, subject, html_content)
                    return True
                except Exception as smtp_exc:
                    logger.error("SMTP fallback failed after unexpected error: %s", str(smtp_exc))
            return False

    async def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        template_id: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Public send_email method supporting synchronous or asynchronous execution (via BackgroundTasks).
        """
        if background_tasks:
            background_tasks.add_task(
                self._send_email_api,
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_content=html_content,
                template_id=template_id,
                params=params,
            )
            logger.info("Email task successfully queued to BackgroundTasks for %s.", to_email)
            return True
        else:
            return await self._send_email_api(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_content=html_content,
                template_id=template_id,
                params=params,
            )

    # =========================================================================
    # OTP MECHANICS
    # =========================================================================

    @staticmethod
    def generate_otp() -> str:
        """
        Generate a cryptographically secure 6-digit random code.
        """
        return f"{secrets.randbelow(900000) + 100000}"

    async def check_rate_limit(self, email: str) -> bool:
        """
        Rate limiting: Max 5 verification emails per email address per hour.
        Returns True if within limit, False if rate limit is exceeded.
        """
        limit_key = f"otp_limit:{email}"
        try:
            redis_client = Redis.from_url(self.redis_url, decode_responses=True)
            current_count = await redis_client.get(limit_key)
            
            if current_count is not None and int(current_count) >= 5:
                logger.warning("Rate limit exceeded for verification email to %s. Active requests in last hour: %s", email, current_count)
                await redis_client.close()
                return False

            if current_count is None:
                await redis_client.setex(limit_key, 3600, 1)
            else:
                await redis_client.incr(limit_key)
                
            await redis_client.close()
            return True
        except Exception as exc:
            # Log failure but fail-open so email delivery is not blocked in production due to Redis failures
            logger.error("Redis rate limit validation failed for %s: %s. Proceeding without rate limit.", email, str(exc))
            return True

    async def store_otp(self, email: str, code: str) -> bool:
        """
        Store OTP in Redis with key `otp:{email}` and TTL of 15 minutes (900 seconds).
        """
        redis_key = f"otp:{email}"
        try:
            redis_client = Redis.from_url(self.redis_url, decode_responses=True)
            await redis_client.setex(redis_key, 900, code)
            await redis_client.close()
            logger.info("Successfully stored OTP for %s in Redis (15 mins TTL).", email)
            return True
        except Exception as exc:
            logger.exception("Failed to store OTP in Redis for %s: %s", email, str(exc))
            return False

    async def verify_otp(self, email: str, code: str) -> bool:
        """
        Verify code against the stored value in Redis.
        If code is valid, deletes the key to prevent reuse and returns True.
        """
        redis_key = f"otp:{email}"
        try:
            redis_client = Redis.from_url(self.redis_url, decode_responses=True)
            stored_code = await redis_client.get(redis_key)
            
            if stored_code and stored_code == code:
                await redis_client.delete(redis_key)
                await redis_client.close()
                logger.info("OTP verification successful for %s. Key cleared.", email)
                return True
                
            await redis_client.close()
            logger.warning("OTP verification failed or expired for %s.", email)
            return False
        except Exception as exc:
            logger.exception("Error verifying OTP in Redis for %s: %s", email, str(exc))
            return False

    # =========================================================================
    # TRANSACTIONAL EMAIL TEMPLATES & SEND METHODS
    # =========================================================================

    async def send_verification_email(
        self,
        email: str,
        name: str,
        otp_code: str,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Verify email address with a 6-digit OTP code (valid 15 minutes).
        Includes built-in rate-limiting verification check.
        """
        is_allowed = await self.check_rate_limit(email)
        if not is_allowed:
            return False

        # Store OTP code first so it's ready for verification
        await self.store_otp(email, otp_code)

        subject = "PlateLink Africa - Verify Your Email Address"
        html_content = self._get_verification_html(name, otp_code)

        return await self.send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
            background_tasks=background_tasks,
        )

    async def send_welcome_email(
        self,
        email: str,
        name: str,
        restaurant_name: str,
        dashboard_url: str,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Send welcome onboarding email to newly registered restaurants.
        """
        subject = f"Welcome to PlateLink Africa, {restaurant_name}! 🎉"
        html_content = self._get_welcome_html(name, restaurant_name, dashboard_url)

        return await self.send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
            background_tasks=background_tasks,
        )

    async def send_order_confirmation_email(
        self,
        email: str,
        name: str,
        order_number: str,
        restaurant_name: str,
        total: float,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Send a beautifully formatted order confirmation email with order details.
        """
        subject = f"Your PlateLink order at {restaurant_name} is confirmed! 🍽️"
        html_content = self._get_order_confirmation_html(name, order_number, restaurant_name, total)

        return await self.send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
            background_tasks=background_tasks,
        )

    async def send_receipt_email(
        self,
        email: str,
        name: str,
        order_number: str,
        receipt_url: str,
        amount: float,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Send receipt email containing total payment confirmation and PDF download link.
        """
        subject = f"Payment Receipt for Order #{order_number} 🧾"
        html_content = self._get_receipt_html(name, order_number, receipt_url, amount)

        return await self.send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
            background_tasks=background_tasks,
        )

    async def send_password_reset_email(
        self,
        email: str,
        name: str,
        reset_token: str,  # Kept in signature for consistency and potential tracking
        reset_url: str,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """
        Send a password reset verification link valid for 1 hour.
        """
        subject = "PlateLink Africa - Reset Your Account Password"
        html_content = self._get_password_reset_html(name, reset_url)

        return await self.send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
            background_tasks=background_tasks,
        )

    # =========================================================================
    # INLINE HTML TEMPLATE GENERATORS
    # =========================================================================

    def _get_verification_html(self, name: str, otp_code: str) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #F8FAFC; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 580px; background-color: #FFFFFF; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05); border: 1px solid #E2E8F0;">
                    <!-- Header with brand gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="color: #FFFFFF; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; font-family: 'Inter', sans-serif;">PlateLink <span style="color: #F97316;">Africa</span></h1>
                            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 14px; font-weight: 500;">Connecting Culinary Excellence</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 35px;">
                            <h2 style="color: #0F172A; margin-top: 0; margin-bottom: 20px; font-size: 20px; font-weight: 700;">Verify Your Email Address</h2>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 30px;">Hello {name},<br><br>Thank you for signing up with PlateLink Africa. To complete your verification process, please use the 6-digit One-Time Password (OTP) below:</p>
                            
                            <!-- OTP Box -->
                            <div style="background-color: #F8FAFC; border-radius: 12px; border: 1px dashed #CBD5E1; padding: 24px; text-align: center; margin-bottom: 30px;">
                                <span style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #F97316; margin-left: 8px;">{otp_code}</span>
                            </div>
                            
                            <p style="color: #475569; font-size: 14px; line-height: 22px; margin-bottom: 20px;">This OTP is extremely secure and is <strong>valid for 15 minutes</strong>. For security reasons, please do not share this code with anyone.</p>
                            <p style="color: #64748B; font-size: 13px; line-height: 20px; margin-bottom: 0;">If you did not request this verification code, you can safely ignore this email.</p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F1F5F9; padding: 24px 35px; text-align: center; border-top: 1px solid #E2E8F0;">
                            <p style="color: #94A3B8; font-size: 12px; margin: 0 0 8px 0;">&copy; 2026 PlateLink Africa. All rights reserved.</p>
                            <p style="color: #94A3B8; font-size: 11px; margin: 0;">This is an automated operational message. Please do not reply directly to this email.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    def _get_welcome_html(self, name: str, restaurant_name: str, dashboard_url: str) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to PlateLink Africa</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #F8FAFC; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 580px; background-color: #FFFFFF; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05); border: 1px solid #E2E8F0;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="color: #FFFFFF; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; font-family: 'Inter', sans-serif;">PlateLink <span style="color: #10B981;">Africa</span></h1>
                            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 14px; font-weight: 500;">Welcome to the Future of Culinary Integration</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 35px;">
                            <h2 style="color: #0F172A; margin-top: 0; margin-bottom: 20px; font-size: 22px; font-weight: 700; text-align: center;">Welcome to the Family! 🎉</h2>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 25px;">Hello {name},</p>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 25px;">We are absolutely thrilled to welcome <strong>{restaurant_name}</strong> to PlateLink Africa! Our platform is designed to seamlessly connect your restaurant with modern digital distribution channels, optimize your operations, and boost your sales.</p>
                            
                            <!-- Call to action card -->
                            <div style="background-color: #ECFDF5; border-radius: 12px; border: 1px solid #A7F3D0; padding: 24px; text-align: center; margin-bottom: 30px;">
                                <h3 style="color: #065F46; margin: 0 0 10px 0; font-size: 16px; font-weight: 700;">Access Your Dashboard</h3>
                                <p style="color: #047857; margin: 0 0 20px 0; font-size: 14px; line-height: 20px;">Your onboarding credentials are active. Log in to configure your digital menu, view analytical reports, and start receiving orders.</p>
                                <a href="{dashboard_url}" style="background-color: #10B981; color: #FFFFFF; text-decoration: none; padding: 12px 28px; font-size: 14px; font-weight: 700; border-radius: 8px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2);">Go to Dashboard</a>
                            </div>

                            <!-- Onboarding Checklist -->
                            <h3 style="color: #0F172A; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">Your Onboarding Checklist:</h3>
                            <ul style="color: #475569; font-size: 14px; line-height: 24px; padding-left: 20px; margin-bottom: 30px;">
                                <li style="margin-bottom: 8px;"><strong>Digital Menu Setup:</strong> Add your signature dishes, descriptions, and high-quality images.</li>
                                <li style="margin-bottom: 8px;"><strong>Payment Integration:</strong> Link your M-Pesa merchant till or paybill number for automated payouts.</li>
                                <li style="margin-bottom: 8px;"><strong>Operational Hours:</strong> Define your active hours so customers know when they can order.</li>
                                <li><strong>Staff Roles:</strong> Assign staff accounts for kitchen managers, cashiers, and dispatchers.</li>
                            </ul>

                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 0;">If you ever have any questions, our dedicated support team is available 24/7. Just reach out via the chat interface in your dashboard.</p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F1F5F9; padding: 24px 35px; text-align: center; border-top: 1px solid #E2E8F0;">
                            <p style="color: #94A3B8; font-size: 12px; margin: 0 0 8px 0;">&copy; 2026 PlateLink Africa. All rights reserved.</p>
                            <p style="color: #94A3B8; font-size: 11px; margin: 0;">You are receiving this because your restaurant was registered on PlateLink Africa.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    def _get_order_confirmation_html(self, name: str, order_number: str, restaurant_name: str, total: float) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Confirmed</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #F8FAFC; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 580px; background-color: #FFFFFF; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05); border: 1px solid #E2E8F0;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="color: #FFFFFF; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; font-family: 'Inter', sans-serif;">PlateLink <span style="color: #3B82F6;">Africa</span></h1>
                            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 14px; font-weight: 500;">Culinary Experience Confirmed</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 35px;">
                            <h2 style="color: #0F172A; margin-top: 0; margin-bottom: 10px; font-size: 20px; font-weight: 700;">Order Confirmed! 🍽️</h2>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 25px;">Hello {name},</p>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 25px;">Great news! Your order has been successfully placed at <strong>{restaurant_name}</strong> and is currently being prepared with care by their culinary team.</p>
                            
                            <!-- Order Summary Box -->
                            <div style="background-color: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0; padding: 24px; margin-bottom: 30px;">
                                <h3 style="color: #0F172A; margin: 0 0 15px 0; font-size: 15px; font-weight: 700; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px;">Order Details</h3>
                                <table width="100%" cellspacing="0" cellpadding="0" style="font-size: 14px;">
                                    <tr>
                                        <td style="color: #64748B; padding: 6px 0;">Order Number:</td>
                                        <td style="color: #0F172A; font-weight: 700; text-align: right; padding: 6px 0;">{order_number}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748B; padding: 6px 0;">Restaurant:</td>
                                        <td style="color: #0F172A; text-align: right; padding: 6px 0;">{restaurant_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748B; padding: 12px 0 6px 0; border-top: 1px dashed #E2E8F0; font-weight: 700;">Total Paid:</td>
                                        <td style="color: #3B82F6; font-weight: 800; font-size: 16px; text-align: right; padding: 12px 0 6px 0; border-top: 1px dashed #E2E8F0;">KES {total:,.2f}</td>
                                    </tr>
                                </table>
                            </div>

                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 20px;">You will receive another notification when your order is ready for pickup or dispatch. You can track real-time progress on your PlateLink web app.</p>
                            <p style="color: #64748B; font-size: 13px; line-height: 20px; margin-bottom: 0;">Need to modify or cancel your order? Please contact the restaurant directly as soon as possible referencing your Order Number.</p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F1F5F9; padding: 24px 35px; text-align: center; border-top: 1px solid #E2E8F0;">
                            <p style="color: #94A3B8; font-size: 12px; margin: 0 0 8px 0;">&copy; 2026 PlateLink Africa. All rights reserved.</p>
                            <p style="color: #94A3B8; font-size: 11px; margin: 0;">Thank you for dining with us!</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    def _get_receipt_html(self, name: str, order_number: str, receipt_url: str, amount: float) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Receipt</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #F8FAFC; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 580px; background-color: #FFFFFF; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05); border: 1px solid #E2E8F0;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="color: #FFFFFF; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; font-family: 'Inter', sans-serif;">PlateLink <span style="color: #10B981;">Africa</span></h1>
                            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 14px; font-weight: 500;">Payment Confirmed</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 35px;">
                            <h2 style="color: #0F172A; margin-top: 0; margin-bottom: 10px; font-size: 20px; font-weight: 700; text-align: center;">Payment Receipt 🧾</h2>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 25px;">Hello {name},</p>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 25px;">This email serves as confirmation of your successful payment for order <strong>#{order_number}</strong>. We appreciate your business.</p>
                            
                            <!-- Amount Card -->
                            <div style="background-color: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0; padding: 24px; text-align: center; margin-bottom: 30px;">
                                <span style="color: #64748B; font-size: 14px; font-weight: 500; display: block; margin-bottom: 6px;">Total Paid</span>
                                <span style="font-size: 32px; font-weight: 800; color: #10B981;">KES {amount:,.2f}</span>
                                <span style="color: #94A3B8; font-size: 12px; display: block; margin-top: 8px;">Paid via M-Pesa Express</span>
                            </div>

                            <!-- CTA to View/Download PDF Receipt -->
                            <div style="text-align: center; margin-bottom: 30px;">
                                <a href="{receipt_url}" style="background-color: #0F172A; color: #FFFFFF; text-decoration: none; padding: 12px 28px; font-size: 14px; font-weight: 700; border-radius: 8px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.15);">Download PDF Receipt</a>
                            </div>

                            <p style="color: #475569; font-size: 14px; line-height: 22px; margin-bottom: 0;">A detailed statement and billing overview are also accessible inside your account profile under 'Order History'.</p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F1F5F9; padding: 24px 35px; text-align: center; border-top: 1px solid #E2E8F0;">
                            <p style="color: #94A3B8; font-size: 12px; margin: 0 0 8px 0;">&copy; 2026 PlateLink Africa. All rights reserved.</p>
                            <p style="color: #94A3B8; font-size: 11px; margin: 0;">For billing questions, please reach out to support@platelink.africa</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    def _get_password_reset_html(self, name: str, reset_url: str) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #F8FAFC; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 580px; background-color: #FFFFFF; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05); border: 1px solid #E2E8F0;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="color: #FFFFFF; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; font-family: 'Inter', sans-serif;">PlateLink <span style="color: #EF4444;">Africa</span></h1>
                            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 14px; font-weight: 500;">Account Security Portal</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 35px;">
                            <h2 style="color: #0F172A; margin-top: 0; margin-bottom: 20px; font-size: 20px; font-weight: 700;">Reset Your Password</h2>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 25px;">Hello {name},</p>
                            <p style="color: #475569; font-size: 15px; line-height: 24px; margin-bottom: 25px;">We received a request to reset the password associated with your PlateLink Africa account. To secure your account, click the button below:</p>
                            
                            <!-- CTA Button -->
                            <div style="text-align: center; margin-bottom: 30px;">
                                <a href="{reset_url}" style="background-color: #EF4444; color: #FFFFFF; text-decoration: none; padding: 12px 30px; font-size: 14px; font-weight: 700; border-radius: 8px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.25);">Reset Password</a>
                            </div>

                            <p style="color: #475569; font-size: 14px; line-height: 22px; margin-bottom: 20px;">This password reset link is temporary and will <strong>expire in 1 hour</strong> for security reasons. If the button doesn't work, copy and paste the following URL into your browser:</p>
                            <p style="word-break: break-all; color: #3B82F6; font-size: 13px; margin-bottom: 30px;"><a href="{reset_url}" style="color: #3B82F6; text-decoration: underline;">{reset_url}</a></p>
                            
                            <hr style="border: 0; border-top: 1px solid #E2E8F0; margin-bottom: 25px;">
                            
                            <p style="color: #64748B; font-size: 13px; line-height: 20px; margin-bottom: 0;"><strong>Security Warning:</strong> If you did not request a password reset, your account is still secure. No action is required and you can safely ignore this email.</p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F1F5F9; padding: 24px 35px; text-align: center; border-top: 1px solid #E2E8F0;">
                            <p style="color: #94A3B8; font-size: 12px; margin: 0 0 8px 0;">&copy; 2026 PlateLink Africa. All rights reserved.</p>
                            <p style="color: #94A3B8; font-size: 11px; margin: 0;">This email was sent to you because you registered an account with PlateLink.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

# =============================================================================
# STANDALONE GLOBAL HELPER FUNCTIONS
# =============================================================================

def generate_otp() -> str:
    """
    Generate a cryptographically secure 6-digit random code.
    Accessible globally without instantiating BrevoEmailService.
    """
    return BrevoEmailService.generate_otp()

async def verify_otp(email: str, code: str) -> bool:
    """
    Verify code against the stored value in Redis.
    Accessible globally without instantiating BrevoEmailService.
    """
    service = BrevoEmailService()
    return await service.verify_otp(email, code)
