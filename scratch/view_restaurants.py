import os
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
engine = create_engine(database_url)

with engine.connect() as conn:
    res = conn.execute(text("SELECT id, name, slug, subdomain, is_active FROM restaurants"))
    rows = res.fetchall()
    print("RESTAURANTS IN DATABASE:")
    for row in rows:
        print(f"ID: {row[0]} | Name: {row[1]} | Slug: {row[2]} | Subdomain: {row[3]} | Active: {row[4]}")
