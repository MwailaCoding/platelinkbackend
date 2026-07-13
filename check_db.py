import os
from sqlalchemy import create_engine, inspect

# Use the same default as migrate_db.py
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
engine = create_engine(database_url)

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Successfully connected to database: {engine.url.database}")
    print(f"Total tables found: {len(tables)}")
    print("-" * 30)
    for table in sorted(tables):
        # Count rows in each table
        with engine.connect() as conn:
            from sqlalchemy import text
            res = conn.execute(text(f"SELECT count(*) FROM {table}"))
            count = res.scalar()
            print(f"[{count:3} rows] - {table}")
    print("-" * 30)
except Exception as e:
    print(f"Error: {e}")
