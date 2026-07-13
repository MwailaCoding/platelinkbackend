# init_db.py
import asyncio
from app.db.session import engine
from app.models import Base

async def init_models():
    async with engine.begin() as conn:
        # Import all models to ensure they are registered with Base
        from app.models import (
            Restaurant, Staff, Table, CustomerSession, Category, 
            MenuItem, Order, OrderItem, Payment, ActivityLog
        )
        print("Creating tables in database...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_models())
