# app/utils/sms.py
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("platelink")

async def send_sms(phone: str, message: str):
    """
    Sends an SMS using Africa's Talking API.
    """
    if not settings.SMS_API_KEY:
        logger.warning("SMS_API_KEY not set, skipping SMS")
        return
        
    url = "https://api.africastalking.com/version1/messaging"
    headers = {
        "ApiKey": settings.SMS_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "username": "platelink",
        "to": phone,
        "message": message,
        "from": settings.SMS_SENDER_ID
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=data, headers=headers)
            logger.info(f"SMS sent to {phone}: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
