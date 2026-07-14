import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine('postgresql+asyncpg://postgres:2030@localhost:5432/platelink')

async def main():
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE menu_items SET image_url = 'https://www.culinaryhill.com/wp-content/uploads/2022/12/Surf-and-Turf-Culinary-Hill-1200x800-1.jpg' WHERE name LIKE '%Surf%'"))
        print("Updated Surf N Turf!")

asyncio.run(main())
