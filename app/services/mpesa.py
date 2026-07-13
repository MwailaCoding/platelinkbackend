# app/services/mpesa.py
import base64
from datetime import datetime
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("platelink")

class MpesaService:
    @staticmethod
    async def get_access_token():
        url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.json().get("access_token")

    @staticmethod
    async def stk_push(phone_number: str, amount: int, order_id: str):
        access_token = await MpesaService.get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()).decode()
        
        url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": f"Order {order_id}",
            "TransactionDesc": "Payment for PlateLink Order"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.json()

    @staticmethod
    async def reverse_transaction(transaction_id: str, amount: float, reason: str):
        """
        Calls Safaricom M-Pesa Reversal API.
        """
        access_token = await MpesaService.get_access_token()
        url = "https://api.safaricom.co.ke/mpesa/reversal/v1/request"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "Initiator": settings.MPESA_INITIATOR_NAME,
            "SecurityCredential": settings.MPESA_SECURITY_CREDENTIAL,
            "CommandID": "TransactionReversal",
            "TransactionID": transaction_id,
            "Amount": amount,
            "ReceiverParty": settings.MPESA_SHORTCODE,
            "RecieverIdentifierType": "11",
            "ResultURL": settings.MPESA_CALLBACK_URL,
            "QueueTimeOutURL": settings.MPESA_CALLBACK_URL,
            "Remarks": reason,
            "Occasion": "Refund"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.json()
