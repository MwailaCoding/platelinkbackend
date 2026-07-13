import os
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
engine = create_engine(database_url)

with engine.connect() as conn:
    res = conn.execute(text("SELECT full_name, role, assigned_tables FROM staff WHERE role = 'waiter'"))
    for row in res:
        print(f"Name: {row[0]:25} | Assigned Tables: {row[2]}")
