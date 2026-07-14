import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SOURCE_URL = os.getenv('SOURCE_DB_URL', 'postgresql://postgres:2030@localhost:5432/platelink').replace('postgresql+asyncpg://', 'postgresql://')
TARGET_URL = os.getenv('TARGET_DB_URL', 'postgresql://platelink_user:PPMZUSp5yyIshueVDBbmU3RaKwGM7blR@dpg-d9al849kh4rs73fu4pv0-a.oregon-postgres.render.com/platelink')

ITEMS_TO_FIX = [
    '19698748-4474-4fc3-b9c3-0294de3f65e3',
    'f7e53e0c-1cd5-4716-bf71-6db968bfdbb8',
    'f03211af-137a-482d-b1e3-6cdad9a69722',
]

async def main():
    s = await asyncpg.connect(SOURCE_URL)
    t = await asyncpg.connect(TARGET_URL, ssl='require')

    print("=" * 60)
    print("FIXING menu_items")
    print("=" * 60)

    for item_id in ITEMS_TO_FIX:
        src = await s.fetchrow(
            'SELECT name, description, price, preparation_time FROM menu_items WHERE id = $1',
            item_id
        )
        if src:
            await t.execute(
                'UPDATE menu_items SET description = $1, price = $2, preparation_time = $3 WHERE id = $4',
                src['description'], src['price'], src['preparation_time'], item_id
            )
            print(f"Fixed '{src['name']}': price={src['price']}, desc={repr(src['description'])}, prep_time={src['preparation_time']}")

    print("\n" + "=" * 60)
    print("DIAGNOSING activity_logs")
    print("=" * 60)

    s_count = await s.fetchval('SELECT COUNT(*) FROM activity_logs')
    t_count = await t.fetchval('SELECT COUNT(*) FROM activity_logs')
    print(f"Source: {s_count} rows | Target: {t_count} rows | Difference: {s_count - t_count}")

    s_ids = set(r['id'] for r in await s.fetch('SELECT id FROM activity_logs'))
    t_ids = set(r['id'] for r in await t.fetch('SELECT id FROM activity_logs'))
    missing = s_ids - t_ids
    extra = t_ids - s_ids

    print(f"\nMissing in target ({len(missing)} rows):")
    for mid in missing:
        row = await s.fetchrow(
            'SELECT id, action, created_at, restaurant_id FROM activity_logs WHERE id = $1', mid
        )
        print(f"  ID={row['id']} | action={row['action']} | created_at={row['created_at']} | restaurant_id={row['restaurant_id']}")

    if extra:
        print(f"\nExtra in target ({len(extra)} rows):")
        for eid in extra:
            row = await t.fetchrow(
                'SELECT id, action, created_at FROM activity_logs WHERE id = $1', eid
            )
            print(f"  ID={row['id']} | action={row['action']} | created_at={row['created_at']}")

    await s.close()
    await t.close()
    print("\nDone.")

if __name__ == '__main__':
    asyncio.run(main())
