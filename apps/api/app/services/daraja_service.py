# app/services/daraja_service.py
import base64
import hashlib
import logging
from datetime import datetime
from typing import Optional, Union, Dict, Any
from uuid import UUID

import httpx
from cryptography.fernet import Fernet
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import RestaurantSetting

# Logger configuration
logger = logging.getLogger("app.services.daraja_service")


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class MpesaBaseError(Exception):
    """
    Base exception class for all M-Pesa (Daraja) related errors.
    """
    def __init__(
        self, 
        message: str, 
        error_code: Optional[Union[str, int]] = None, 
        raw_response: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.raw_response = raw_response


class MpesaAuthError(MpesaBaseError):
    """
    Raised when authentication with Safaricom Daraja gateway fails.
    """
    pass


class MpesaSTKError(MpesaBaseError):
    """
    Raised when an STK Push processing or execution request fails.
    """
    pass


class MpesaQueryError(MpesaBaseError):
    """
    Raised when querying the status of an STK Push transaction fails.
    """
    pass


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_phone_number(phone: str) -> bool:
    """
    Validates Kenyan phone numbers to match standard formats:
    - 07XXXXXXXX or 01XXXXXXXX (10 digits)
    - 2547XXXXXXXX or 2541XXXXXXXX (12 digits)
    - +2547XXXXXXXX or +2541XXXXXXXX (13 digits)
    - 7XXXXXXXX or 1XXXXXXXX (9 digits)
    
    Returns True if valid, False otherwise.
    """
    if not phone:
        return False
    
    # Strip whitespaces, hyphens, and the plus sign
    clean_phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    
    if not clean_phone.isdigit():
        return False
        
    length = len(clean_phone)
    if length == 10:
        return clean_phone.startswith("07") or clean_phone.startswith("01")
    elif length == 12:
        return clean_phone.startswith("2547") or clean_phone.startswith("2541")
    elif length == 9:
        return clean_phone.startswith("7") or clean_phone.startswith("1")
        
    return False


def format_phone_for_api(phone: str) -> str:
    """
    Formats a valid Kenyan phone number to the Safaricom API format (2547XXXXXXXX or 2541XXXXXXXX).
    Raises ValueError if phone number is invalid.
    """
    if not validate_phone_number(phone):
        raise ValueError(f"Invalid Kenyan phone number format: '{phone}'")
        
    clean_phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    
    if clean_phone.startswith("07") or clean_phone.startswith("01"):
        return f"254{clean_phone[1:]}"
    elif clean_phone.startswith("7") or clean_phone.startswith("1"):
        return f"254{clean_phone}"
    elif clean_phone.startswith("254"):
        return clean_phone
        
    return clean_phone


# =============================================================================
# DARAJA SERVICE
# =============================================================================

class DarajaService:
    """
    Direct M-Pesa (Daraja API) Service for PlateLink Africa.
    Supports secure multi-tenant settings (stored encrypted per restaurant) with env fallback,
    automated Redis token caching, STK push initiation, transaction queries, and C2B registration.
    """
    
    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        passkey: Optional[str] = None,
        shortcode: Optional[str] = None,
        environment: Optional[str] = None
    ) -> None:
        """
        Initializes DarajaService credentials. 
        Falls back to global settings or OS environment variables if parameters are omitted.
        """
        import os
        
        self.consumer_key = (
            consumer_key 
            or os.getenv("MPESA_CONSUMER_KEY") 
            or getattr(settings, "MPESA_CONSUMER_KEY", None)
        )
        self.consumer_secret = (
            consumer_secret 
            or os.getenv("MPESA_CONSUMER_SECRET") 
            or getattr(settings, "MPESA_CONSUMER_SECRET", None)
        )
        self.passkey = (
            passkey 
            or os.getenv("MPESA_PASSKEY") 
            or getattr(settings, "MPESA_PASSKEY", None)
        )
        self.shortcode = (
            shortcode 
            or os.getenv("MPESA_SHORTCODE") 
            or getattr(settings, "MPESA_SHORTCODE", None)
        )
        self.environment = (
            environment 
            or os.getenv("MPESA_ENVIRONMENT") 
            or getattr(settings, "MPESA_ENVIRONMENT", "sandbox")
        )
        
        self.redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

    @property
    def base_url(self) -> str:
        """
        Selects Safaricom endpoint base URL according to configuration environment.
        """
        env = str(self.environment).lower().strip()
        if env in ("live", "production"):
            return "https://api.safaricom.co.ke"
        return "https://sandbox.safaricom.co.ke"

    # =========================================================================
    # ENCRYPTION HELPERS
    # =========================================================================

    def _get_fernet(self) -> Fernet:
        """
        Generates a deterministic 32-byte Fernet key derived from settings.SECRET_KEY.
        This provides secure out-of-the-box symmetric decryption capability.
        """
        secret = getattr(settings, "SECRET_KEY", "default_secret_key_platelink_africa_mpesa")
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
        return Fernet(key)

    def _encrypt(self, value: str) -> str:
        """
        Encrypts plaintext string using the secret-derived Fernet instance.
        """
        if not value:
            return ""
        try:
            f = self._get_fernet()
            return f.encrypt(value.encode()).decode()
        except Exception as e:
            logger.error("Failed to encrypt configuration: %s", str(e))
            return value

    def _decrypt(self, encrypted_value: str) -> str:
        """
        Decrypts an encrypted configuration value.
        Falls back seamlessly to the raw value if it is not actually encrypted.
        """
        if not encrypted_value:
            return ""
        try:
            f = self._get_fernet()
            return f.decrypt(encrypted_value.encode()).decode()
        except Exception:
            # Fallback for plain-text values in local environment/testing
            return encrypted_value

    # =========================================================================
    # MULTI-TENANT DYNAMIC DATABASE LOADING
    # =========================================================================

    async def load_restaurant_config(self, db: AsyncSession, restaurant_id: UUID) -> "DarajaService":
        """
        Loads and decrypts restaurant-specific M-Pesa configurations from DB dynamically.
        Supports unified JSONB key structures and individual key value patterns.
        """
        try:
            result = await db.execute(
                select(RestaurantSetting).where(
                    RestaurantSetting.restaurant_id == restaurant_id
                )
            )
            settings_list = result.scalars().all()
            settings_dict = {s.key: s.value for s in settings_list}
            
            # Case 1: Decrypt configs packed in a single 'mpesa_config' dictionary structure
            if "mpesa_config" in settings_dict:
                config_data = settings_dict["mpesa_config"]
                if isinstance(config_data, dict):
                    self.consumer_key = self._decrypt(config_data.get("consumer_key", ""))
                    self.consumer_secret = self._decrypt(config_data.get("consumer_secret", ""))
                    self.passkey = self._decrypt(config_data.get("passkey", ""))
                    self.shortcode = config_data.get("shortcode", "")  # Often stored plain
                    self.environment = config_data.get("environment", "sandbox")
                    
                    # Decrypt shortcode just in case it was encrypted
                    if self.shortcode:
                        self.shortcode = self._decrypt(self.shortcode)
                    return self
            
            # Case 2: Individual keys fallback
            for key, val_data in settings_dict.items():
                val = val_data.get("value") if isinstance(val_data, dict) else val_data
                if not val:
                    continue
                    
                if key == "MPESA_CONSUMER_KEY":
                    self.consumer_key = self._decrypt(val)
                elif key == "MPESA_CONSUMER_SECRET":
                    self.consumer_secret = self._decrypt(val)
                elif key == "MPESA_PASSKEY":
                    self.passkey = self._decrypt(val)
                elif key == "MPESA_SHORTCODE":
                    self.shortcode = self._decrypt(val)
                elif key == "MPESA_ENVIRONMENT":
                    self.environment = val
                    
        except Exception as e:
            logger.exception(
                "Error dynamically loading M-Pesa credentials from DB for restaurant %s: %s", 
                restaurant_id, str(e)
            )
            # Falls back cleanly to current instance values
        return self

    # =========================================================================
    # CORE API METHODS
    # =========================================================================

    async def get_access_token(self, consumer_key: str, consumer_secret: str) -> str:
        """
        Requests an OAuth 2.0 access token from Safaricom.
        Caches the token in Redis to avoid redundant roundtrips (Expires 3600s).
        """
        if not consumer_key or not consumer_secret:
            raise MpesaAuthError("Authentication failed: Missing consumer_key or consumer_secret.")

        cache_key = f"mpesa_token:{consumer_key}"
        
        # Try to retrieve from Redis cache
        try:
            async with Redis.from_url(self.redis_url, decode_responses=True) as redis:
                cached_token = await redis.get(cache_key)
                if cached_token:
                    logger.info("M-Pesa Access Token successfully fetched from Redis cache.")
                    return cached_token
        except Exception as cache_err:
            logger.warning("Redis cache read failure: %s. Continuing with direct generation...", str(cache_err))

        # Direct API Request to Safaricom
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth_header = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15.0)
                
                if response.status_code != 200:
                    try:
                        raw_err = response.json()
                    except Exception:
                        raw_err = None
                    raise MpesaAuthError(
                        message=f"Safaricom OAuth request failed with code {response.status_code}",
                        error_code=response.status_code,
                        raw_response=raw_err or {"body": response.text}
                    )
                
                data = response.json()
                access_token = data.get("access_token")
                
                if not access_token:
                    raise MpesaAuthError(
                        message="Invalid response from Safaricom: missing 'access_token' field",
                        raw_response=data
                    )
                
                # Write to Redis cache
                try:
                    async with Redis.from_url(self.redis_url, decode_responses=True) as redis:
                        # Cache for 3600s
                        await redis.setex(cache_key, 3600, access_token)
                except Exception as cache_err:
                    logger.warning("Failed storing access token to Redis: %s", str(cache_err))
                
                return access_token
                
        except httpx.RequestError as exc:
            raise MpesaAuthError(message=f"Network error during M-Pesa token generation: {exc}")
        except Exception as e:
            if isinstance(e, MpesaAuthError):
                raise e
            raise MpesaAuthError(message=f"Unexpected error during token extraction: {e}")

    async def stk_push(
        self,
        access_token: str,
        shortcode: str,
        passkey: str,
        amount: float,
        phone_number: str,
        account_reference: str,
        callback_url: str
    ) -> Dict[str, Any]:
        """
        Initiates an M-Pesa Express (STK Push) transaction.
        Returns Safaricom's raw response containing CheckoutRequestID.
        """
        # Validate and format Kenyan phone format to 254XXXXXXXX
        try:
            formatted_phone = format_phone_for_api(phone_number)
        except ValueError as val_err:
            raise MpesaSTKError(message=str(val_err))
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        # Convert float amount safely (Safaricom Daraja accepts whole currency units)
        try:
            amt_str = str(int(amount))
        except (TypeError, ValueError):
            amt_str = str(amount)
            
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amt_str,
            "PartyA": formatted_phone,
            "PartyB": shortcode,
            "PhoneNumber": formatted_phone,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": "Food Order Payment"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                
                if response.status_code != 200:
                    try:
                        raw_err = response.json()
                    except Exception:
                        raw_err = None
                        
                    err_msg = raw_err.get("errorMessage", response.text) if raw_err else response.text
                    err_code = raw_err.get("errorCode", response.status_code) if raw_err else response.status_code
                    
                    raise MpesaSTKError(
                        message=f"STK Push processing failure: {err_msg}",
                        error_code=err_code,
                        raw_response=raw_err
                    )
                
                data = response.json()
                
                # Check for Safaricom business-level errors
                response_code = data.get("ResponseCode")
                if response_code != "0":
                    err_desc = data.get("ResponseDescription", "Transaction rejected by Safaricom.")
                    
                    # Handle specific error codes specified by prompt requirements
                    custom_msg = err_desc
                    if response_code == "1037":
                        custom_msg = "User cancelled the request (1037)"
                    elif response_code == "1032":
                        custom_msg = "Insufficient balance (1032)"
                        
                    raise MpesaSTKError(
                        message=f"STK Push declined: {custom_msg}",
                        error_code=response_code,
                        raw_response=data
                    )
                
                return data
                
        except httpx.RequestError as exc:
            raise MpesaSTKError(message=f"Network error during STK Push submission: {exc}")
        except Exception as e:
            if isinstance(e, MpesaSTKError):
                raise e
            raise MpesaSTKError(message=f"Unexpected error during STK Push: {e}")

    async def query_status(
        self, 
        access_token: str, 
        checkout_request_id: str,
        shortcode: Optional[str] = None,
        passkey: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Queries Safaricom M-Pesa STK Push transaction status.
        Falls back to service instance configurations if parameters are omitted.
        """
        active_shortcode = shortcode or self.shortcode
        active_passkey = passkey or self.passkey
        
        if not active_shortcode or not active_passkey:
            raise MpesaQueryError("BusinessShortCode and PassKey are required to execute a status query.")
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{active_shortcode}{active_passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "BusinessShortCode": active_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                
                if response.status_code != 200:
                    try:
                        raw_err = response.json()
                    except Exception:
                        raw_err = None
                        
                    err_msg = raw_err.get("errorMessage", response.text) if raw_err else response.text
                    err_code = raw_err.get("errorCode", response.status_code) if raw_err else response.status_code
                    
                    raise MpesaQueryError(
                        message=f"Query request rejected by Safaricom: {err_msg}",
                        error_code=err_code,
                        raw_response=raw_err
                    )
                
                data = response.json()
                
                # Sift through ResultCode or ResponseCode
                result_code = data.get("ResultCode")
                response_code = data.get("ResponseCode")
                
                code = str(result_code) if result_code is not None else (response_code if response_code is not None else None)
                
                if code is not None and code != "0":
                    err_desc = data.get("ResultDesc", data.get("ResponseDescription", "Transaction failed or is unconfirmed."))
                    
                    # Handle specific error codes specified by prompt requirements
                    custom_msg = err_desc
                    if code == "1037":
                        custom_msg = "User cancelled the request (1037)"
                    elif code == "1032":
                        custom_msg = "Insufficient balance (1032)"
                        
                    raise MpesaQueryError(
                        message=f"Transaction query indicates failure: {custom_msg}",
                        error_code=code,
                        raw_response=data
                    )
                
                return data
                
        except httpx.RequestError as exc:
            raise MpesaQueryError(message=f"Network error during transaction query: {exc}")
        except Exception as e:
            if isinstance(e, MpesaQueryError):
                raise e
            raise MpesaQueryError(message=f"Unexpected error during transaction status query: {e}")

    async def register_c2b_url(
        self,
        access_token: str,
        shortcode: str,
        confirmation_url: str,
        validation_url: str
    ) -> Dict[str, Any]:
        """
        Registers C2B Validation and Confirmation URLs with Safaricom M-Pesa.
        Useful for intercepting paybill/till payment receipts.
        """
        url = f"{self.base_url}/mpesa/c2b/v1/registerurl"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "ShortCode": shortcode,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                
                if response.status_code != 200:
                    try:
                        raw_err = response.json()
                    except Exception:
                        raw_err = None
                        
                    err_msg = raw_err.get("errorMessage", response.text) if raw_err else response.text
                    err_code = raw_err.get("errorCode", response.status_code) if raw_err else response.status_code
                    
                    raise MpesaSTKError(
                        message=f"C2B URL registration failed: {err_msg}",
                        error_code=err_code,
                        raw_response=raw_err
                    )
                
                return response.json()
                
        except httpx.RequestError as exc:
            raise MpesaSTKError(message=f"Network error during URL registration: {exc}")
        except Exception as e:
            if isinstance(e, MpesaSTKError):
                raise e
            raise MpesaSTKError(message=f"Unexpected error during C2B URL registration: {e}")
