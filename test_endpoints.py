# test_endpoints.py
import httpx
import asyncio
import uuid
import random

BASE_URL = "http://localhost:8000/api/v1"
SUBDOMAIN = f"testrest{random.randint(1000, 9999)}"
OWNER_NAME = "Test Owner"
PASSWORD = "password123"
EMAIL = f"owner@{SUBDOMAIN}.com"

async def test_all_endpoints():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"--- Testing PlateLink Africa Backend for subdomain: {SUBDOMAIN} ---")

        # 1. Auth: Register
        print("\n[1] Testing Auth: Register...")
        reg_data = {
            "restaurant_name": "Test Restaurant",
            "subdomain": SUBDOMAIN,
            "owner_name": OWNER_NAME,
            "email": EMAIL,
            "phone": "254700000000",
            "password": PASSWORD
        }
        res = await client.post(f"{BASE_URL}/auth/register", json=reg_data)
        if res.status_code != 200:
            print(f"FAILED: {res.text}")
            return
        print("SUCCESS: Registered")
        
        # 1b. Auth: Verify Email (Activation)
        print("\n[1b] Testing Auth: Verify Email...")
        verify_data = {"email": EMAIL, "otp_code": "123456"}
        res = await client.post(f"{BASE_URL}/auth/verify-email", json=verify_data)
        if res.status_code != 200:
            print(f"FAILED: {res.text}")
            return
        print("SUCCESS: Email verified and restaurant activated")

        # 2. Auth: Login
        print("\n[2] Testing Auth: Login...")
        login_data = {
            "email": EMAIL,
            "password": PASSWORD
        }
        res = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        if res.status_code != 200:
            print(f"FAILED: {res.text}")
            return
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("SUCCESS: Logged in")

        # 3. Restaurant: Get Settings
        print("\n[3] Testing Restaurant: Get Profile...")
        res = await client.get(f"{BASE_URL}/restaurants/me", headers=headers)
        restaurant_id = res.json()['id']
        print(f"SUCCESS: {res.json()['name']}")

        # 4. Staff: Create Waiter
        print("\n[4] Testing Staff: Create Waiter...")
        staff_data = {
            "full_name": "Test Waiter",
            "role": "waiter",
            "pin_code": "1234",
            "shift": "morning"
        }
        res = await client.post(f"{BASE_URL}/staff/", json=staff_data, headers=headers)
        if res.status_code != 200:
             print(f"FAILED: {res.text}")
        else:
            print(f"SUCCESS: Waiter {res.json()['full_name']} created")

        # 5. Tables: Bulk Create
        print("\n[5] Testing Tables: Bulk Create...")
        table_data = {
            "start_number": 1,
            "end_number": 5,
            "capacity": 4,
            "location": "Main Hall"
        }
        res = await client.post(f"{BASE_URL}/tables/bulk-create", json=table_data, headers=headers)
        print(f"SUCCESS: {res.json()['msg']}")

        # 6. Menu: Create Category
        print("\n[6] Testing Menu: Create Category...")
        cat_data = {"name": "Drinks", "display_order": 1}
        res = await client.post(f"{BASE_URL}/menu/categories", json=cat_data, headers=headers)
        cat_id = res.json()["id"]
        print(f"SUCCESS: Category {res.json()['name']} created")

        # 7. Menu: Create Item
        print("\n[7] Testing Menu: Create Item...")
        item_data = {
            "name": "Cold Soda",
            "price": 150.00,
            "category_id": cat_id,
            "is_available": True,
            "stock_quantity": 100,
            "preparation_time": 10
        }
        res = await client.post(f"{BASE_URL}/menu/items", json=item_data, headers=headers)
        item_id = res.json()["id"]
        print(f"SUCCESS: Item {res.json()['name']} created")

        # 8. Customer: Get Menu (Public)
        print("\n[8] Testing Customer: Get Menu...")
        res = await client.get(f"{BASE_URL}/customer/menu/{SUBDOMAIN}")
        print(f"SUCCESS: Found {len(res.json()['categories'])} categories")

        # 9. Tables: Get QR (Simulating scan)
        print("\n[9] Simulating QR Scan...")
        res = await client.get(f"{BASE_URL}/tables/", headers=headers)
        table = res.json()[0]
        qr_token = table["qr_code_token"]
        print(f"SUCCESS: Table {table['table_number']} QR token retrieved")

        # 10. Customer: Start Session
        print("\n[10] Testing Customer: Start Session...")
        res = await client.post(f"{BASE_URL}/customer/sessions/start", json={"qr_token": qr_token})
        session_token = res.json()["session_token"]
        print("SUCCESS: Session started")

        # 11. Customer: Place Order
        print("\n[11] Testing Customer: Place Order...")
        order_data = {
            "items": [
                {"menu_item_id": item_id, "quantity": 2, "special_instructions": "Very cold"}
            ],
            "payment_method": "mpesa"
        }
        res = await client.post(f"{BASE_URL}/customer/sessions/{session_token}/orders", json=order_data)
        if res.status_code != 200:
             print(f"FAILED: {res.text}")
        else:
            order_num = res.json()["order_number"]
            print(f"SUCCESS: Order {order_num} placed. Total: {res.json()['total']}")

        # 12. Kitchen: Get New Orders
        print("\n[12] Testing Kitchen: Accept Order...")
        res = await client.get(f"{BASE_URL}/kitchen/orders/new?restaurant_id={restaurant_id}", headers=headers)
        orders = res.json()
        if not orders or "detail" in orders:
            print(f"FAILED: Could not get kitchen orders: {orders}")
            return
        order_id = orders[0]["id"]
        res = await client.put(f"{BASE_URL}/kitchen/orders/{order_id}/accept?restaurant_id={restaurant_id}", headers=headers)
        print(f"SUCCESS: Order {order_id} accepted by kitchen")

        # 12b. Waiter: Mark Served
        print("\n[12b] Testing Waiter: Mark Served...")
        res = await client.put(f"{BASE_URL}/waiter/orders/{order_id}/served", headers=headers)
        if res.status_code != 200:
            print(f"FAILED: Mark served failed: {res.text}")
            return
        print("SUCCESS: Order marked as served")

        # 12c. Waiter: Add Note
        print("\n[12c] Testing Waiter: Add Note...")
        res = await client.post(f"{BASE_URL}/waiter/orders/{order_id}/notes", json={"note": "Extra cold soda please"}, headers=headers)
        if res.status_code != 200:
            print(f"FAILED: Add note failed: {res.text}")
            return
        print(f"SUCCESS: Note added: {res.json()['waiter_notes']}")

        # 12d. Waiter: Table Transfer
        print("\n[12d] Testing Waiter: Table Transfer...")
        res = await client.get(f"{BASE_URL}/tables/", headers=headers)
        tables_list = res.json()
        target_table_id = tables_list[1]["id"]
        res = await client.post(f"{BASE_URL}/waiter/orders/{order_id}/transfer", json={"target_table_id": target_table_id}, headers=headers)
        if res.status_code != 200:
            print(f"FAILED: Table transfer failed: {res.text}")
            return
        print(f"SUCCESS: Table transfer confirmed: {res.json()['msg']}")

        # 12e. Waiter: Split Check by Item
        print("\n[12e] Testing Waiter: Split Check by Item...")
        res = await client.get(f"{BASE_URL}/orders/{order_id}", headers=headers)
        retrieved_order = res.json()
        item_to_split = retrieved_order["items"][0]["id"]
        split_payload = {
            "splits": [
                {
                    "customer_name": "Guest A",
                    "item_ids": [item_to_split],
                    "subtotal": 150.00
                },
                {
                    "customer_name": "Guest B",
                    "item_ids": [],
                    "subtotal": 150.00
                }
            ]
        }
        res = await client.post(f"{BASE_URL}/waiter/bills/{order_id}/split-by-item", json=split_payload, headers=headers)
        if res.status_code != 200:
            print(f"FAILED: Split bill failed: {res.text}")
            return
        payments = res.json()["payments"]
        print(f"SUCCESS: Bill split into {len(payments)} payments")

        # 12f. Cashier: Confirm Split Cash Payment
        print("\n[12f] Testing Cashier: Confirm Cash Payment for Split...")
        res = await client.get(f"{BASE_URL}/staff/", headers=headers)
        staff_list = res.json()
        cashier_staff_id = staff_list[0]["id"]
        payment_id_to_pay = payments[0]["payment_id"]
        payment_amt_to_pay = payments[0]["amount"]
        cash_confirm_payload = {
            "staff_id": cashier_staff_id,
            "amount_received": payment_amt_to_pay + 50.0,
            "payment_id": payment_id_to_pay
        }
        res = await client.post(f"{BASE_URL}/payments/cash/{order_id}/confirm", json=cash_confirm_payload, headers=headers)
        if res.status_code != 200:
            print(f"FAILED: Cash payment confirmation failed: {res.text}")
            return
        print(f"SUCCESS: Settle split cash payment complete. Change due: {res.json()['change_amount']}")

        # 12g. Analytics: Waiter Sales Report
        print("\n[12g] Testing Analytics: Waiter Sales Report...")
        res = await client.get(f"{BASE_URL}/analytics/waiter-sales", headers=headers)
        if res.status_code != 200:
            print(f"FAILED: Waiter sales report failed: {res.text}")
            return
        print(f"SUCCESS: Waiter sales report loaded: {res.json()}")

        # 13. Analytics: Dashboard
        print("\n[13] Testing Analytics: Dashboard...")
        res = await client.get(f"{BASE_URL}/analytics/dashboard", headers=headers)
        print(f"SUCCESS: Today Sales: {res.json()['today_sales']}")

        print("\n--- ALL ENDPOINT SMOKE TESTS COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
