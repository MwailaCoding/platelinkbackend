import os
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
engine = create_engine(database_url)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hashed_pin = pwd_context.hash("1234")

with engine.connect() as conn:
    # Get all active restaurants
    res = conn.execute(text("SELECT id, name FROM restaurants"))
    restaurants = list(res)
    
    print(f"Creating chef for {len(restaurants)} restaurants...")
    for r_id, r_name in restaurants:
        # Check if a chef already exists
        check = conn.execute(text("SELECT COUNT(*) FROM staff WHERE restaurant_id = :r_id AND role = 'chef'"), {"r_id": r_id})
        count = check.scalar()
        if count == 0:
            conn.execute(text("""
                INSERT INTO staff (restaurant_id, full_name, role, shift, pin_code, is_active, is_verified)
                VALUES (:restaurant_id, :full_name, 'chef', 'full', :pin_code, true, true)
            """), {
                "restaurant_id": r_id,
                "full_name": f"Chef for {r_name}",
                "pin_code": hashed_pin
            })
            print(f"Created Chef for '{r_name}' with PIN '1234'")
        else:
            print(f"Chef already exists for '{r_name}'")
    conn.commit()
print("Done!")
