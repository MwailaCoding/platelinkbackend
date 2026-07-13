# app/middleware/rate_limit.py
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: Redis):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next):
        if settings.DEBUG:
            return await call_next(request)
            
        client_ip = request.client.host
        path = request.url.path
        
        # Default limits
        limit = 100
        window = 60
        
        if path.startswith(f"{settings.API_V1_STR}/orders"):
            limit = 10
        elif path.startswith(f"{settings.API_V1_STR}/auth/login"):
            limit = 5
            window = 900
            
        key = f"rate_limit:{client_ip}:{path}"
        current_time = time.time()
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, current_time - window)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.zcard(key)
        pipe.expire(key, window)
        _, _, count, _ = await pipe.execute()
        
        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(window)}
            )
            
        return await call_next(request)
