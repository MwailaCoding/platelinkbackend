import httpx
import asyncio

async def main():
    # Login to get token
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:8000/api/v1/auth/login", data={"username": "owner@platelink.com", "password": "password123"})
        token = res.json()["access_token"]
        
        # Get items to find Surf N Turf
        headers = {"Authorization": f"Bearer {token}"}
        items = await client.get("http://localhost:8000/api/v1/menu/items", headers=headers)
        item = next(i for i in items.json() if "Surf" in i["name"])
        
        # Try updating
        payload = {
            "name": item["name"],
            "description": item["description"],
            "price": str(item["price"]),
            "category_id": item["category_id"],
            "is_available": True,
            "preparation_time": 15,
            "image_url": "https://www.culinaryhill.com/wp-content/uploads/2022/12/Surf-and-Turf-Culinary-Hill-1200x800-1.jpg"
        }
        
        print(f"Updating {item['id']}")
        update_res = await client.put(f"http://localhost:8000/api/v1/menu/items/{item['id']}", json=payload, headers=headers)
        print("Status:", update_res.status_code)
        print("Response:", update_res.json())
        
        # Verify
        check = await client.get("http://localhost:8000/api/v1/menu/items", headers=headers)
        updated = next(i for i in check.json() if i["id"] == item["id"])
        print("Final image_url:", updated.get("image_url"))

asyncio.run(main())
