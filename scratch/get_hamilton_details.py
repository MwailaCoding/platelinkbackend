import os
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
engine = create_engine(database_url)

with engine.connect() as conn:
    rest_res = conn.execute(text("SELECT id, name FROM restaurants WHERE slug = 'hamiltons-cafe'"))
    restaurant = rest_res.fetchone()
    if restaurant:
        rest_id, name = restaurant
        tables_res = conn.execute(text("SELECT table_number, qr_code_token FROM tables WHERE restaurant_id = :rest_id LIMIT 10"), {"rest_id": rest_id})
        print(f"Tables for {name}:")
        for number, token in tables_res:
            print(f"- Table {number}: Token is '{token}'")
