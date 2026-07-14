import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine('postgresql+asyncpg://postgres:2030@localhost:5432/platelink')

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name, image_url FROM menu_items"))
        for row in result:
            print(row)

asyncio.run(main())
