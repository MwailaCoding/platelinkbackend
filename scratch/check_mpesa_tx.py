import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, "c:\\Users\\HP\\OneDrive\\Desktop\\platelink")
load_dotenv("c:\\Users\\HP\\OneDrive\\Desktop\\platelink\\.env")

async def check_mpesa_tx():
    db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    print("Columns in 'mpesa_transactions' table:")
    rows = await conn.fetch(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = 'mpesa_transactions'"
    )
    for r in rows:
        print(f"  {r['column_name']} ({r['data_type']})")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_mpesa_tx())
