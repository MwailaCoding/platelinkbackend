"""FastAPI application entry point for PlateLink Backend API."""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from apps.api.app.api.v1.api import api_router
from apps.api.app.core.database import async_session_local
from apps.api.app.core.seed import seed_initial_data

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("platelink_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing PlateLink API Backend...")
    # Seed default permissions and system roles on startup if configured
    if os.getenv("SEED_ON_STARTUP", "false").lower() == "true":
        async with async_session_local() as db:
            await seed_initial_data(db)
    yield
    logger.info("Shutting down PlateLink API Backend.")

app = FastAPI(
    title=os.getenv("APP_NAME", "PlateLink API"),
    version="1.0.0",
    description="PlateLink Role-Based Access Control & Restaurant Management Platform API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PlateLink API", "version": "1.0.0"}
