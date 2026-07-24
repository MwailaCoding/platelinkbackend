"""SMS notification service."""
import logging

logger = logging.getLogger(__name__)

async def send_sms(to: str, message: str) -> bool:
    """Send SMS notification to recipient phone number."""
    logger.info(f"[SMS MOCK] To: {to} | Message: {message}")
    return True

async def send_invitation_sms(
    to: str,
    first_name: str,
    restaurant_name: str,
    pin: str
) -> bool:
    """Send staff invitation SMS."""
    message = f"Hi {first_name}, you have been invited to join {restaurant_name} on PlateLink. Your PIN is: {pin}"
    return await send_sms(to, message)
