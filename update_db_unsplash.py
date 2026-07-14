import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine('postgresql+asyncpg://postgres:2030@localhost:5432/platelink')

async def main():
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE menu_items SET image_url = 'https://images.unsplash.com/photo-1544025162-811114bd4b27?q=80&w=2000&auto=format&fit=crop' WHERE name LIKE '%Surf%'"))
        print("Updated Surf N Turf with reliable Unsplash image!")

asyncio.run(main())
