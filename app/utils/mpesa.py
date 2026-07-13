# app/utils/mpesa.py
import re
import base64
from datetime import datetime
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("platelink.utils.mpesa")

def format_phone_for_mpesa(phone: str) -> str:
    """Convert Kenyan phone number to 254 format for M-Pesa API"""
    # Remove any spaces, dashes, or plus signs
    phone = re.sub(r'[\s\+\-\(\)]', '', phone)
    
    # If starts with 0, replace with 254
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    
    # If starts with 254, keep as is
    # If starts with 7 or 1, add 254
    elif phone.startswith('7') or phone.startswith('1'):
        phone = '254' + phone
        
    return phone


async def initiate_stk_push(
    amount: float,
    phone_number: str,
    account_reference: str,
    transaction_desc: str,
    callback_url: str
):
    """
    Initiates a real-time Safaricom M-Pesa STK Push.
    Supports sandbox vs production based on standard shortcode check.
    """
    # Get oauth access token
    url_generate = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    is_sandbox = "sandbox" in settings.MPESA_CALLBACK_URL or settings.MPESA_SHORTCODE == "174379"
    if is_sandbox:
        url_generate = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        
    auth = base64.b64encode(f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()).decode()
    headers_token = {"Authorization": f"Basic {auth}"}
    
    async with httpx.AsyncClient() as client:
        response_token = await client.get(url_generate, headers=headers_token)
        access_token = response_token.json().get("access_token")
        
    if not access_token:
        raise Exception("Failed to retrieve M-Pesa OAuth access token")
        
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()).decode()
    
    base_url = "https://sandbox.safaricom.co.ke" if is_sandbox else "https://api.safaricom.co.ke"
    url_push = f"{base_url}/mpesa/stkpush/v1/processrequest"
    
    headers_push = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }
    
    logger.info(f"Initiating STK Push to {phone_number} for KES {amount}. Callback: {callback_url}")
    
    async with httpx.AsyncClient() as client:
        response_push = await client.post(url_push, json=payload, headers=headers_push)
        return response_push.json()
