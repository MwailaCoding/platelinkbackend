import os
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
engine = create_engine(database_url)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

common_pins = ["1234", "0000", "1111", "2222", "1212", "4321", "2580", "5678", "2323", "9999", "1314", "4321"]

with engine.connect() as conn:
    res = conn.execute(text("""
        SELECT s.id, s.full_name, s.role, s.pin_code, r.name 
        FROM staff s 
        JOIN restaurants r ON s.restaurant_id = r.id
    """))
    staff_members = list(res)

print(f"Checking {len(common_pins)} common PINs for {len(staff_members)} staff members...")

found = False
for staff in staff_members:
    s_id, name, role, hashed, rest_name = staff
    for pin in common_pins:
        try:
            if pwd_context.verify(pin, hashed):
                print(f"MATCH FOUND: Staff '{name}' ({role}) at '{rest_name}' has PIN '{pin}'")
                found = True
                break
        except Exception:
            pass

if not found:
    print("No matches found among common PINs. We can set a staff PIN to '1234' for testing if you want.")
