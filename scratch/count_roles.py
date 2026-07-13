import os
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
engine = create_engine(database_url)

with engine.connect() as conn:
    print("STAFF ROLES:")
    print("-" * 50)
    res = conn.execute(text("SELECT role, COUNT(*) FROM staff GROUP BY role"))
    for row in res:
        print(f"Role: {row[0]} | Count: {row[1]}")
