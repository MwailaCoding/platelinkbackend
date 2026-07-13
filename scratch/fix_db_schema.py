import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, "c:\\Users\\HP\\OneDrive\\Desktop\\platelink")
load_dotenv("c:\\Users\\HP\\OneDrive\\Desktop\\platelink\\.env")

async def fix_schema():
    db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    print(f"Connecting to: {db_url}")
    conn = await asyncpg.connect(db_url)
    
    # Run migrations in a transaction block
    async with conn.transaction():
        print("Applying changes to 'payments' table...")
        
        # 1. Drop existing single-column FK constraint on order_id
        await conn.execute(
            "ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_order_id_fkey"
        )
        
        # 2. Add order_created_at column
        # Since payments has 0 rows, we can safely add it as NOT NULL
        await conn.execute(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS order_created_at TIMESTAMPTZ NOT NULL"
        )
        
        # 3. Add composite foreign key constraint
        await conn.execute(
            "ALTER TABLE payments ADD CONSTRAINT fk_payments_order_composite "
            "FOREIGN KEY (order_id, order_created_at) REFERENCES orders(id, created_at) ON DELETE CASCADE"
        )
        
        # 4. Add missing columns for Mpesa callback data
        await conn.execute(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS mpesa_result_code INTEGER"
        )
        await conn.execute(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS mpesa_result_description TEXT"
        )
        
        # 5. Add check constraint on amount
        await conn.execute(
            "ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_amount_check"
        )
        await conn.execute(
            "ALTER TABLE payments ADD CONSTRAINT payments_amount_check CHECK (amount > 0)"
        )
        
        print("Applying changes to 'mpesa_transactions' table...")
        
        # 6. Add missing columns to mpesa_transactions
        await conn.execute(
            "ALTER TABLE mpesa_transactions ADD COLUMN IF NOT EXISTS mpesa_receipt_number TEXT"
        )
        await conn.execute(
            "ALTER TABLE mpesa_transactions ADD COLUMN IF NOT EXISTS result_desc TEXT"
        )
        
    print("\nSUCCESS! Schema changes applied successfully.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_schema())
