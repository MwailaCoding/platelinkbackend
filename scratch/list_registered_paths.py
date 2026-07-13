import httpx
import json

try:
    r = httpx.get("http://localhost:8000/api/v1/openapi.json")
    if r.status_code == 200:
        paths = list(r.json().get("paths", {}).keys())
        print("Registered paths:")
        for path in sorted(paths):
            print(f"  {path}")
    else:
        print(f"Failed to fetch openapi.json: HTTP {r.status_code}")
except Exception as e:
    print(f"Error fetching openapi.json: {e}")
