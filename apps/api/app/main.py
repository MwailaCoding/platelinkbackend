"""FastAPI application entry point for PlateLink Backend API."""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import text

from apps.api.app.api.v1.api import api_router
from apps.api.app.core.database import engine, async_session_local
from apps.api.app.core.seed import seed_initial_data
from apps.api.app.models.base import Base
# Import all models to ensure they are registered on Base.metadata
import apps.api.app.models  # noqa: F401

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("platelink_api")

async def apply_schema_migrations(conn):
    """Safely apply missing columns to existing PostgreSQL tables on Render."""
    migration_sqls = [
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'restaurantsize') THEN CREATE TYPE restaurantsize AS ENUM ('small', 'medium', 'large', 'enterprise'); END IF; END $$;",
        "ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS size restaurantsize NOT NULL DEFAULT 'medium';",
        "ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS is_multi_branch BOOLEAN NOT NULL DEFAULT FALSE;",
        "ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS type VARCHAR(50) NOT NULL DEFAULT 'casual_dining';",
        "ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS parent_restaurant_id UUID REFERENCES restaurants(id) ON DELETE SET NULL;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS pin VARCHAR(4);",
    ]
    for sql in migration_sqls:
        try:
            await conn.execute(text(sql))
        except Exception as e:
            logger.warning(f"Migration statement notice: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing PlateLink API Backend...")
    
    # 1. Automatically create missing tables and apply missing columns on startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await apply_schema_migrations(conn)
        logger.info("Database tables and schema migrations verified successfully.")
    except Exception as err:
        logger.error(f"Error initializing database schema: {err}")

    # 2. Seed default permissions and system roles on startup
    try:
        async with async_session_local() as db:
            await seed_initial_data(db)
        logger.info("Initial data seeded successfully.")
    except Exception as err:
        logger.error(f"Error seeding initial data: {err}")

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
