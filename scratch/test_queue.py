import httpx

url = "http://localhost:8000/api/v1/orders/active/queue"
# We need an owner token to call this. We can login first as owner.
login_url = "http://localhost:8000/api/v1/auth/login"

try:
    # Login as owner
    login_res = httpx.post(login_url, json={
        "email": "owner@testrest7808.com", # or any owner email
        "password": "password123"
    })
    if login_res.status_code == 200:
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        res = httpx.get(url, headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Queue data: {res.text[:1000]}")
    else:
        # Try finding owner email from DB
        from sqlalchemy import create_engine, text
        import os
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:2030@localhost/platelink")
        engine = create_engine(database_url)
        with engine.connect() as conn:
            user_res = conn.execute(text("SELECT email FROM staff WHERE role = 'owner' LIMIT 1"))
            email = user_res.scalar()
        print(f"Found owner email in DB: {email}")
        login_res = httpx.post(login_url, json={
            "email": email,
            "password": "password123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        res = httpx.get(url, headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Queue data: {res.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
