import httpx
import json

url = "http://localhost:8000/api/v1/openapi.json"
try:
    response = httpx.get(url)
    print(f"Status Code: {response.status_code}")
    try:
        schema = response.json()
        print("Keys:", list(schema.keys()))
        if "paths" in schema:
            paths = ["/api/v1/kitchen/orders/{order_id}/accept", "/api/v1/waiter/orders/{order_id}/served", "/api/v1/waiter/calls/{call_id}/acknowledge"]
            for path in paths:
                if path in schema["paths"]:
                    print(f"Path: {path}")
                    print(json.dumps(schema["paths"][path], indent=2))
                    print("-" * 50)
                else:
                    print(f"Path not found: {path}")
        else:
            print("No paths key in response")
    except Exception as je:
        print(f"JSON Error: {je}")
        print(response.text[:500])
except Exception as e:
    print(f"Error: {e}")
