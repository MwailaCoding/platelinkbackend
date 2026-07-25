# app/middleware/rate_limit.py
import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: Redis, limit: int = 100, window: int = 60):
        super().__init__(app)
        self.redis = redis_client
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next):
        if settings.DEBUG:
            return await call_next(request)
            
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        current_time = int(time.time())
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, current_time - self.window)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.zcard(key)
        pipe.expire(key, self.window)
        _, _, count, _ = await pipe.execute()
        
        if count > self.limit:
            raise HTTPException(status_code=429, detail="Too many requests")
            
        return await call_next(request)

# app/middleware/logging.py
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api_logger")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        logger.info(
            f"Method: {request.method} | Path: {request.url.path} | "
            f"Status: {response.status_code} | Duration: {duration:.4f}s"
        )
        return response
