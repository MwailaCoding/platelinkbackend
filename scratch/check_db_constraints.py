import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, "c:\\Users\\HP\\OneDrive\\Desktop\\platelink")
load_dotenv("c:\\Users\\HP\\OneDrive\\Desktop\\platelink\\.env")

async def check_constraints():
    db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    print("Constraints on 'payments' table:")
    rows = await conn.fetch(
        "SELECT conname, pg_get_constraintdef(c.oid) as def "
        "FROM pg_constraint c "
        "WHERE conrelid = 'payments'::regclass"
    )
    for r in rows:
        print(f"  {r['conname']}: {r['def']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_constraints())
