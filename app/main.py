# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v1.routes.payments import router as payments_router
from app.api.v1.routes.webhooks import router as webhooks_router
from app.services.pesapal_service import PesapalService
import logging
from app.db.session import engine
from redis.asyncio import Redis
from sqlalchemy import text
from app.middleware.logging import RequestLoggingMiddleware
from app.api.v1.websockets.connection_manager import manager

logger = logging.getLogger("uvicorn.error")
pesapal_service = PesapalService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Check connections
    print("\n" + "="*50)
    print("PLATELINK AFRICA BACKEND STARTING UP")
    print("="*50)
    
    # 1. Check Database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database Connection: STABLE")
    except Exception as e:
        logger.error(f"Database Connection: FAILED -> {e}")
        
    # 2. Check Redis
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        logger.info("Redis Connection: STABLE")
        await redis.close()
    except Exception as e:
        logger.error(f"Redis Connection: FAILED -> {e}")

    # 3. Register Pesapal Webhook IPN
    try:
        if pesapal_service.consumer_key and pesapal_service.consumer_secret:
            ipn_id = await pesapal_service.register_ipn()
            logger.info(f"Pesapal Webhook IPN registered successfully on startup: {ipn_id}")
        else:
            logger.warning("Pesapal credentials not configured. Skipping startup IPN registration.")
    except Exception as e:
        logger.error(f"Pesapal Webhook IPN registration failed on startup: {e}")
        
    print("="*50 + "\n")
    yield
    # Shutdown: Close connections

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Parse ALLOWED_ORIGINS: "*" stays as-is; comma-separated URLs become a list
_raw_origins = settings.ALLOWED_ORIGINS.strip()
_allowed_origins = ["*"] if _raw_origins == "*" else [o.strip() for o in _raw_origins.split(",") if o.strip()]

# NOTE: allow_credentials=True is incompatible with allow_origins=["*"] per the CORS spec.
# When origins is "*", we must set allow_credentials=False. Use explicit origins for credentialed requests.
_allow_credentials = _allowed_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# Standard API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Explicit payment and webhook routers for fallback integration
app.include_router(payments_router, prefix="/api/v1", tags=["Payments"])
app.include_router(webhooks_router, prefix="/api/v1", tags=["Webhooks"])

@app.get("/health", tags=["Health"])
async def health_check():
    """Root health check — used by Render to verify the service is alive."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}


@app.get("/health/payments", tags=["Health"])
async def payments_health():
    pesapal_status = "unconfigured"
    if pesapal_service.consumer_key and pesapal_service.consumer_secret:
        try:
            token = await pesapal_service.get_access_token()
            pesapal_status = "healthy" if token else "error"
        except Exception as e:
            pesapal_status = f"unhealthy: {str(e)}"
            
    mpesa_status = "configured"
    if not settings.MPESA_CONSUMER_KEY or settings.MPESA_CONSUMER_KEY == "placeholder":
        mpesa_status = "unconfigured"

    return {
        "status": "healthy" if pesapal_status == "healthy" or mpesa_status == "configured" else "degraded",
        "services": {
            "pesapal": pesapal_status,
            "mpesa": mpesa_status
        }
    }

@app.websocket("/ws/payment/{transaction_id}")
async def websocket_payment_endpoint(websocket: WebSocket, transaction_id: str):
    room_id = f"payment_{transaction_id}"
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

@app.websocket("/ws/{restaurant_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, restaurant_id: str, role: str):
    room_id = f"{restaurant_id}_{role}"
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle heartbeat
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
