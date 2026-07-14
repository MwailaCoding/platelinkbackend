import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SOURCE_URL = os.getenv('SOURCE_DB_URL', 'postgresql://postgres:2030@localhost:5432/platelink').replace('postgresql+asyncpg://', 'postgresql://')
TARGET_URL = os.getenv('TARGET_DB_URL', 'postgresql://platelink_user:PPMZUSp5yyIshueVDBbmU3RaKwGM7blR@dpg-d9al849kh4rs73fu4pv0-a.oregon-postgres.render.com/platelink')

MISSING_LOG_IDS = [
    '7851f60d-26f3-4721-8579-3203aa2838c8',
    '499588ce-7416-4697-9bf5-754faf6f2496',
    '23ea79ff-1818-4df2-8eb4-456a36642802',
]

async def main():
    s = await asyncpg.connect(SOURCE_URL)
    t = await asyncpg.connect(TARGET_URL, ssl='require')

    print("=" * 60)
    print("SYNCING missing activity_logs rows to Render")
    print("=" * 60)

    # Get all column names for activity_logs
    cols_info = await s.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'activity_logs' AND table_schema = 'public' "
        "ORDER BY ordinal_position"
    )
    columns = [r['column_name'] for r in cols_info]
    col_list = ', '.join(f'"{c}"' for c in columns)
    placeholders = ', '.join(f'${i+1}' for i in range(len(columns)))

    insert_sql = f'INSERT INTO activity_logs ({col_list}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING'

    inserted = 0
    for log_id in MISSING_LOG_IDS:
        row = await s.fetchrow(f'SELECT {col_list} FROM activity_logs WHERE id = $1', log_id)
        if row:
            await t.execute(insert_sql, *row)
            print(f"Inserted log ID={log_id} | action={row['action']} | created_at={row['created_at']}")
            inserted += 1
        else:
            print(f"Row not found in source: {log_id}")

    # Final count check
    s_count = await s.fetchval('SELECT COUNT(*) FROM activity_logs')
    t_count = await t.fetchval('SELECT COUNT(*) FROM activity_logs')
    print(f"\nFinal counts -> Source: {s_count} | Target: {t_count}")

    await s.close()
    await t.close()
    print(f"\nDone. Inserted {inserted} missing rows.")

if __name__ == '__main__':
    asyncio.run(main())
