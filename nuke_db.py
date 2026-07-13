# nuke_db.py
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def nuke():
    async with engine.begin() as conn:
        print("Nuking public schema...")
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    print("Database nuked.")

if __name__ == "__main__":
    asyncio.run(nuke())
