import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SOURCE_URL = os.getenv('SOURCE_DB_URL', 'postgresql://postgres:2030@localhost:5432/platelink')
TARGET_URL = os.getenv('TARGET_DB_URL', 'postgresql://platelink_user:PPMZUSp5yyIshueVDBbmU3RaKwGM7blR@dpg-d9al849kh4rs73fu4pv0-a.oregon-postgres.render.com/platelink')

async def diff():
    s_conn = await asyncpg.connect(SOURCE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    t_conn = await asyncpg.connect(TARGET_URL, ssl='require')

    s_rows = await s_conn.fetch('SELECT * FROM menu_items ORDER BY id')
    t_rows = await t_conn.fetch('SELECT * FROM menu_items ORDER BY id')

    print(f"Source count: {len(s_rows)}, Target count: {len(t_rows)}")
    
    s_dict = {r['id']: dict(r) for r in s_rows}
    t_dict = {r['id']: dict(r) for r in t_rows}

    # Compare keys
    s_keys = set(s_dict.keys())
    t_keys = set(t_dict.keys())

    if s_keys != t_keys:
        print("Missing in target:", s_keys - t_keys)
        print("Extra in target:", t_keys - s_keys)

    # Compare field by field for matching keys
    common_keys = s_keys.intersection(t_keys)
    for kid in common_keys:
        s_row = s_dict[kid]
        t_row = t_dict[kid]
        
        diffs = {}
        for col in s_row.keys():
            s_val = s_row[col]
            t_val = t_row.get(col)
            
            # Normalize for comparison
            if s_val != t_val:
                diffs[col] = (s_val, t_val)
                
        if diffs:
            print(f"\nItem ID {kid} ('{s_row.get('name')}') differs:")
            for col, (sv, tv) in diffs.items():
                print(f"  Column '{col}': Source='{sv}' ({type(sv)}), Target='{tv}' ({type(tv)})")

    await s_conn.close()
    await t_conn.close()

if __name__ == '__main__':
    asyncio.run(diff())
