import os
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
engine = create_engine(database_url)

with engine.connect() as conn:
    print("RESTAURANTS:")
    print("-" * 50)
    res = conn.execute(text("SELECT id, name, prefix FROM restaurants"))
    for row in res:
        print(f"ID: {row[0]} | Name: {row[1]} | Prefix: {row[2]}")
    print("\nSTAFF:")
    print("-" * 80)
    res = conn.execute(text("""
        SELECT s.full_name, s.role, s.pin_code, r.name 
        FROM staff s 
        JOIN restaurants r ON s.restaurant_id = r.id
        WHERE s.role IN ('waiter', 'chef', 'manager', 'cashier')
    """))
    for row in res:
        print(f"Name: {row[0]:25} | Role: {row[1]:10} | PIN: {row[2]} | Restaurant: {row[3]}")
