import httpx

url = "http://localhost:8000/api/v1/staff/me"
try:
    response = httpx.get(url, follow_redirects=True)
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.text}")
except Exception as e:
    print(f"Error: {e}")
