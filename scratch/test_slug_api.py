import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get("http://localhost:8000/api/v1/restaurants/slug/hamiltons-cafe")
            print(f"STATUS CODE: {r.status_code}")
            print(f"RESPONSE JSON: {r.json()}")
        except Exception as e:
            print(f"Error calling API: {e}")

asyncio.run(test())
