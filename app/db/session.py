# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

def _get_connect_args() -> dict:
    """Return SSL connect args for non-localhost databases (e.g. Render PostgreSQL)."""
    url = settings.DATABASE_URL
    is_local = "localhost" in url or "127.0.0.1" in url
    return {} if is_local else {"ssl": "require"}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=5,          # Reduced from 20 — Render free tier has connection limits
    max_overflow=5,       # Reduced from 10
    pool_pre_ping=True,   # Recover from dropped idle connections (important on Render)
    connect_args=_get_connect_args(),
)

async_session_local = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with async_session_local() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

