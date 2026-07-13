import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, "c:\\Users\\HP\\OneDrive\\Desktop\\platelink")
load_dotenv("c:\\Users\\HP\\OneDrive\\Desktop\\platelink\\.env")

async def check_all_tables():
    db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    tables = await conn.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
        "ORDER BY table_name"
    )
    
    for t in tables:
        table_name = t['table_name']
        print(f"\nTable: {table_name}")
        columns = await conn.fetch(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = $1", table_name
        )
        for col in columns:
            print(f"  {col['column_name']} ({col['data_type']})")
            
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_all_tables())
