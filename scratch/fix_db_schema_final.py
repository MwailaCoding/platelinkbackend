import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, "c:\\Users\\HP\\OneDrive\\Desktop\\platelink")
load_dotenv("c:\\Users\\HP\\OneDrive\\Desktop\\platelink\\.env")

async def fix_schema_final():
    db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    print(f"Connecting to: {db_url}")
    conn = await asyncpg.connect(db_url)
    
    # Run alterations in a transaction block
    async with conn.transaction():
        print("Applying schema corrections to 'payments' table...")
        
        # 1. Add missing M-Pesa result columns to payments table
        await conn.execute(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS mpesa_result_code INTEGER"
        )
        await conn.execute(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS mpesa_result_description TEXT"
        )
        
        # 2. Add amount constraint to payments table if missing
        await conn.execute(
            "ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_amount_check"
        )
        await conn.execute(
            "ALTER TABLE payments ADD CONSTRAINT payments_amount_check CHECK (amount > 0)"
        )
        
        print("Applying schema corrections to 'mpesa_transactions' table...")
        
        # 3. Add missing columns to mpesa_transactions table
        await conn.execute(
            "ALTER TABLE mpesa_transactions ADD COLUMN IF NOT EXISTS mpesa_receipt_number TEXT"
        )
        await conn.execute(
            "ALTER TABLE mpesa_transactions ADD COLUMN IF NOT EXISTS result_desc TEXT"
        )
        
    print("\nSUCCESS! Database schema corrections completed.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_schema_final())
