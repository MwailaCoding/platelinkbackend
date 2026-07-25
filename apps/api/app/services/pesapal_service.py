# app/services/pesapal_service.py
import os
import httpx
import logging
import asyncio
from typing import Dict, Any, Optional
from redis.asyncio import Redis

from app.core.config import settings

# Initialize logging for the Pesapal service
logger = logging.getLogger("app.services.pesapal_service")

class PesapalError(Exception):
    """Base exception for all Pesapal integration errors."""
    pass

class PesapalAuthError(PesapalError):
    """Raised when authentication with the Pesapal API fails."""
    pass

class PesapalAPIError(PesapalError):
    """Raised when standard transaction or registration calls to the Pesapal API fail."""
    pass

class PesapalTransferError(PesapalError):
    """Raised when payout or money transfer requests fail."""
    pass

class PesapalService:
    """
    Complete production-ready Pesapal Payment Service for PlateLink Africa.
    Handles authentication caching in Redis, dynamic IPN webhook registration,
    order submission, status verification, and merchant payout transfers with
    robust logging, auto-retries, and customized error handling.
    """
    
    def __init__(self) -> None:
        # Load keys and credentials from environment variables or application settings
        self.consumer_key: Optional[str] = os.getenv("PESAPAL_CONSUMER_KEY") or getattr(settings, "PESAPAL_CONSUMER_KEY", None)
        self.consumer_secret: Optional[str] = os.getenv("PESAPAL_CONSUMER_SECRET") or getattr(settings, "PESAPAL_CONSUMER_SECRET", None)
        self.environment: str = os.getenv("PESAPAL_ENVIRONMENT") or getattr(settings, "PESAPAL_ENVIRONMENT", None) or "sandbox"
        
        # Determine API base URL
        env_url = os.getenv("PESAPAL_API_URL") or getattr(settings, "PESAPAL_API_URL", None)
        if env_url:
            self.api_url = env_url.rstrip("/")
        else:
            self.api_url = (
                "https://pay.pesapal.com/v3"
                if self.environment.lower() == "live"
                else "https://cybqa.pesapal.com/pesapalv3"
            )
            
        self.callback_url: str = (
            os.getenv("PESAPAL_CALLBACK_URL") 
            or getattr(settings, "PESAPAL_CALLBACK_URL", None) 
            or "https://api.platelink.com/webhooks/pesapal"
        )
        
        self.ipn_id: Optional[str] = os.getenv("PESAPAL_IPN_ID") or getattr(settings, "PESAPAL_IPN_ID", None)
        self.redis_url: str = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        if not self.consumer_key or not self.consumer_secret:
            logger.warning(
                "Pesapal service initialized without PESAPAL_CONSUMER_KEY or PESAPAL_CONSUMER_SECRET. "
                "API operations will fail until credentials are provided."
            )

    def _normalize_phone_number(self, phone: str) -> str:
        """
        Helper method to normalize East African phone numbers to standard 254XXXXXXXXX format.
        """
        cleaned = "".join(filter(str.isdigit, phone))
        if cleaned.startswith("0"):
            return "254" + cleaned[1:]
        elif cleaned.startswith("7") or cleaned.startswith("1"):
            return "254" + cleaned
        return cleaned

    def _update_env_file(self, ipn_id: str) -> None:
        """
        Helper method to write or update PESAPAL_IPN_ID in the .env file for durability.
        """
        env_path = os.path.join(os.getcwd(), ".env")
        if not os.path.exists(env_path):
            env_path = "c:\\Users\\HP\\OneDrive\\Desktop\\platelink\\.env"
            
        try:
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("PESAPAL_IPN_ID="):
                        lines[i] = f"PESAPAL_IPN_ID={ipn_id}\n"
                        updated = True
                        break
                
                if not updated:
                    if lines and not lines[-1].endswith("\n"):
                        lines.append("\n")
                    lines.append("\n# Pesapal Webhook IPN ID\n")
                    lines.append(f"PESAPAL_IPN_ID={ipn_id}\n")
                    
                with open(env_path, "w") as f:
                    f.writelines(lines)
                
                logger.info(f"Successfully wrote PESAPAL_IPN_ID={ipn_id} to .env file at {env_path}")
            else:
                logger.warning(f"Unable to write to .env file because it was not found at path {env_path}")
        except Exception as e:
            logger.error(f"Failed to dynamically write PESAPAL_IPN_ID to .env file: {e}")

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        exception_cls: type[PesapalError] = PesapalAPIError,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        requires_auth: bool = False,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Low-level utility to perform HTTP requests with automatic retry logic (max 3 retries),
        exponential backoff, and verbose logging of all requests and responses.
        """
        logger.info(f"Pesapal Request - Method: {method} | URL: {url} | Params: {params} | Payload: {payload}")
        
        current_delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                request_headers = headers.copy() if headers else {}
                if requires_auth:
                    auth_headers = await self._get_auth_headers()
                    request_headers.update(auth_headers)

                async with httpx.AsyncClient() as client:
                    if method.upper() == "POST":
                        response = await client.post(url, json=payload, params=params, headers=request_headers, timeout=15.0)
                    elif method.upper() == "GET":
                        response = await client.get(url, params=params, headers=request_headers, timeout=15.0)
                    else:
                        response = await client.request(method, url, json=payload, params=params, headers=request_headers, timeout=15.0)
                    
                    logger.info(
                        f"Pesapal Response [Attempt {attempt}/{max_retries}] - Status: {response.status_code} | "
                        f"Response Content: {response.text}"
                    )
                    
                    response.raise_for_status()
                    
                    try:
                        res_data = response.json()
                        if isinstance(res_data, dict):
                            error_info = res_data.get("error")
                            if error_info is not None:
                                err_code = error_info.get("code") if isinstance(error_info, dict) else "unknown_error"
                                err_msg = error_info.get("message") if isinstance(error_info, dict) else str(error_info)
                                status_code = res_data.get("status", "unknown")
                                raise exception_cls(
                                    f"Pesapal API error: code='{err_code}', message='{err_msg}', status='{status_code}'"
                                )
                        return res_data
                    except ValueError as val_err:
                        raise exception_cls(
                            f"Invalid JSON returned from Pesapal API: {response.text}"
                        ) from val_err
                        
            except (httpx.HTTPStatusError, httpx.RequestError) as http_exc:
                logger.warning(
                    f"Pesapal HTTP error on attempt {attempt}/{max_retries} for URL {url}: {http_exc}"
                )
                
                # Check for 401 Unauthorized and clear Redis cache key so the next retry gets a fresh token
                if isinstance(http_exc, httpx.HTTPStatusError) and http_exc.response.status_code == 401 and requires_auth:
                    logger.warning("Pesapal request returned 401 Unauthorized. Invalidating cached access token in Redis.")
                    try:
                        redis_client = Redis.from_url(self.redis_url, decode_responses=True)
                        await redis_client.delete("pesapal_access_token")
                        await redis_client.close()
                    except Exception as cache_err:
                        logger.warning(f"Failed to clear expired Pesapal token from Redis: {cache_err}")

                if attempt == max_retries:
                    error_msg = f"Pesapal request failed after {max_retries} attempts: {http_exc}"
                    if isinstance(http_exc, httpx.HTTPStatusError):
                        error_msg += f" | Response Status: {http_exc.response.status_code} | Response Body: {http_exc.response.text}"
                    raise exception_cls(error_msg) from http_exc
                
                logger.info(f"Retrying in {current_delay} seconds...")
                await asyncio.sleep(current_delay)
                current_delay *= 2
                
            except Exception as exc:
                logger.error(f"Unexpected internal exception occurred during Pesapal call: {exc}")
                raise exception_cls(f"Unexpected internal service error: {str(exc)}") from exc
        
        raise exception_cls(f"Pesapal API request failed after {max_retries} retries due to unexplained circumstances.")

    async def _get_auth_headers(self) -> Dict[str, str]:
        """
        Internal helper to retrieve auth headers using a cached or freshly retrieved access token.
        """
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def get_access_token(self) -> str:
        """
        Obtains a bearer access token from Pesapal, cached in Redis for 3600 seconds.
        """
        cache_key = "pesapal_access_token"
        
        # 1. Attempt to fetch token from Redis cache
        try:
            redis_client = Redis.from_url(self.redis_url, decode_responses=True)
            cached_token = await redis_client.get(cache_key)
            if cached_token:
                logger.info("Retrieved active Pesapal access token from Redis cache.")
                await redis_client.close()
                return cached_token
            await redis_client.close()
        except Exception as e:
            logger.warning(f"Could not check Redis cache for Pesapal token: {e}")

        # 2. Call Pesapal RequestToken API if cache miss
        url = f"{self.api_url}/api/Auth/RequestToken"
        payload = {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        logger.info("Requesting fresh Pesapal access token.")
        res_data = await self._request_with_retry(
            "POST", url, payload=payload, headers=headers, exception_cls=PesapalAuthError
        )
        
        token = res_data.get("token")
        if not token:
            raise PesapalAuthError(
                f"Pesapal Auth succeeded but did not return 'token'. Response: {res_data}"
            )
            
        # 3. Cache token in Redis (Token expires in 5 minutes / 300s, cache for 4 minutes / 240s)
        try:
            redis_client = Redis.from_url(self.redis_url, decode_responses=True)
            await redis_client.setex(cache_key, 240, token)
            await redis_client.close()
            logger.info("Successfully cached fresh Pesapal token in Redis for 240s.")
        except Exception as e:
            logger.warning(f"Failed to save Pesapal token to Redis cache: {e}")
            
        return token

    async def register_ipn(self) -> str:
        """
        Registers the Instant Payment Notification (IPN) webhook URL with Pesapal.
        Returns the registered IPN ID and stores it locally and in the .env file.
        """
        url = f"{self.api_url}/api/URLSetup/RegisterIPN"
        payload = {
            "url": self.callback_url,
            "ipn_notification_type": "GET"
        }
        
        logger.info(f"Registering callback IPN webhook URL: {self.callback_url}")
        res_data = await self._request_with_retry(
            "POST", url, payload=payload, requires_auth=True, exception_cls=PesapalAPIError
        )
        
        ipn_id = res_data.get("ipn_id")
        if not ipn_id:
            raise PesapalAPIError(
                f"IPN registration succeeded but did not return an 'ipn_id'. Response: {res_data}"
            )
            
        # Dynamically set active state and store back to .env
        self.ipn_id = ipn_id
        os.environ["PESAPAL_IPN_ID"] = ipn_id
        self._update_env_file(ipn_id)
        
        return ipn_id

    async def submit_order(
        self, order_id: str, amount: float, phone_number: str, email: str, description: str
    ) -> Dict[str, Any]:
        """
        Submits an order to Pesapal to generate a secure checkout payment link.
        Automatically registers the IPN URL dynamically if PESAPAL_IPN_ID is not configured.
        """
        # Ensure we have a valid IPN ID first
        if not self.ipn_id:
            logger.info("PESAPAL_IPN_ID not found in configuration. Auto-registering IPN webhook dynamically...")
            try:
                self.ipn_id = await self.register_ipn()
            except Exception as e:
                logger.error(f"Dynamic webhook auto-registration failed during submit_order: {e}")
                raise PesapalAPIError(
                    f"Order submission blocked. Webhook IPN ID is required and dynamic registration failed: {e}"
                )

        # Normalize phone number to East African format for M-Pesa compatibility
        normalized_phone = self._normalize_phone_number(phone_number)
        
        url = f"{self.api_url}/api/Transactions/SubmitOrderRequest"
        
        payload = {
            "id": order_id,
            "currency": "KES",
            "amount": amount,
            "description": description,
            "callback_url": self.callback_url,
            "notification_id": self.ipn_id,
            "notification_type": "all",
            "billing_address": {
                "phone_number": normalized_phone,
                "email_address": email
            }
        }
        
        res_data = await self._request_with_retry(
            "POST", url, payload=payload, requires_auth=True, exception_cls=PesapalAPIError
        )
        
        redirect_url = res_data.get("redirect_url")
        order_tracking_id = res_data.get("order_tracking_id")
        
        if not redirect_url or not order_tracking_id:
            raise PesapalAPIError(
                f"Pesapal Order submission returned incomplete response. "
                f"Missing redirect_url or order_tracking_id. Response: {res_data}"
            )
            
        return {
            "redirect_url": redirect_url,
            "order_tracking_id": order_tracking_id
        }

    async def get_transaction_status(self, order_tracking_id: str) -> Dict[str, Any]:
        """
        Checks the status of a transaction on Pesapal using its unique tracking ID.
        """
        url = f"{self.api_url}/api/Transactions/GetTransactionStatus"
        params = {"orderTrackingId": order_tracking_id}
        
        logger.info(f"Querying transaction status for tracking ID: {order_tracking_id}")
        res_data = await self._request_with_retry(
            "GET", url, params=params, requires_auth=True, exception_cls=PesapalAPIError
        )
        
        status_description = res_data.get("payment_status_description")
        amount = res_data.get("amount")
        payment_method = res_data.get("payment_method")
        
        # Build core mapping response
        result = {
            "payment_status_description": status_description,
            "amount": amount,
            "payment_method": payment_method
        }
        
        # Include all other fields from the API response for complete detail preservation
        for key, val in res_data.items():
            if key not in result:
                result[key] = val
                
        return result

    async def initiate_transfer(self, recipient_phone: str, amount: float, narrative: str) -> Dict[str, Any]:
        """
        Initiates a funds payout transfer (e.g. B2B payout) to an M-Pesa recipient.
        """
        url = f"{self.api_url}/api/Transfers/SubmitTransferRequest"
        normalized_phone = self._normalize_phone_number(recipient_phone)
        
        payload = {
            "amount": amount,
            "currency": "KES",
            "recipient_type": "MPESA",
            "recipient_account": normalized_phone,
            "narrative": narrative
        }
        
        logger.info(f"Initiating payout transfer of KES {amount} to {normalized_phone}.")
        res_data = await self._request_with_retry(
            "POST", url, payload=payload, requires_auth=True, exception_cls=PesapalTransferError
        )
        
        transfer_id = res_data.get("transfer_id")
        status = res_data.get("status") or "PENDING"
        
        if not transfer_id:
            raise PesapalTransferError(
                f"Pesapal transfer request succeeded but did not return 'transfer_id'. Response: {res_data}"
            )
            
        return {
            "transfer_id": transfer_id,
            "status": status
        }
