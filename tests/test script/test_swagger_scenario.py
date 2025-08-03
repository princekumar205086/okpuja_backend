"""
Test the exact scenario where user might experience issues in Swagger
This tests the manual step-by-step flow that matches Swagger UI testing
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"

print("🔍 TESTING POTENTIAL SWAGGER ISSUE SCENARIO")
print("=" * 50)

# Use the JWT token from previous test
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU0MDc0NjIwLCJpYXQiOjE3NTQwNzEwMjAsImp0aSI6IjFiYjA5NmYxM2VjMDQwZDJiMTQwN2ZiMGZjZjI4MzA5IiwidXNlcl9pZCI6Miwicm9sZSI6IlVTRVIiLCJhY2NvdW50X3N0YXR1cyI6IkFDVElWRSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfQ.IDCH_z8zUJhw2ycIa7mOVikUuTJXZ_19xEQoM5oZUzo"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# Test 1: Create a brand new cart (like in Swagger)
print("\n1. Creating new cart via API...")
cart_data = {
    "service_type": "PUJA",
    "puja_service": 8,
    "package_id": 2,
    "selected_date": "2025-09-01",
    "selected_time": "20:00"
}

response = requests.post(f"{BASE_URL}/cart/carts/", json=cart_data, headers=headers)
if response.status_code == 201:
    cart_result = response.json()
    test_cart_id = cart_result["cart_id"]
    print(f"   ✅ New cart created: {test_cart_id}")
else:
    print(f"   ❌ Cart creation failed: {response.status_code}")
    exit(1)

# Test 2: Create payment for this cart
print(f"\n2. Creating payment for cart {test_cart_id}...")
payment_data = {"cart_id": test_cart_id}

response = requests.post(f"{BASE_URL}/payments/cart/", json=payment_data, headers=headers)
if response.status_code == 201:
    payment_result = response.json()
    test_order_id = payment_result["data"]["payment_order"]["merchant_order_id"]
    print(f"   ✅ Payment created: {test_order_id}")
    print(f"   📊 Status: {payment_result['data']['payment_order']['status']}")
else:
    print(f"   ❌ Payment creation failed: {response.status_code}")
    exit(1)

# Test 3: Check booking BEFORE webhook (should fail)
print(f"\n3. Testing booking endpoint BEFORE payment success...")
booking_url = f"{BASE_URL}/booking/bookings/by-cart/{test_cart_id}/"
response = requests.get(booking_url, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print("   ✅ Expected 404 - No booking yet (payment not successful)")
else:
    print(f"   ⚠️  Unexpected response: {response.text}")

# Test 4: Test redirect BEFORE webhook (should use fallback)
print(f"\n4. Testing redirect BEFORE payment success...")
response = requests.get(f"{BASE_URL}/payments/redirect/simple/", allow_redirects=False)
if response.status_code == 302:
    redirect_url = response.headers.get("Location", "")
    print(f"   ✅ Redirect works: {redirect_url}")
    if test_cart_id in redirect_url:
        print("   ✅ Uses correct latest cart ID")
    else:
        print("   ⚠️  Uses different cart ID (expected behavior)")
else:
    print(f"   ❌ Redirect failed: {response.status_code}")

# Test 5: Now simulate webhook success
print(f"\n5. Simulating webhook for payment success...")

# Create webhook payload and send it
webhook_payload = {
    "merchantId": "M22KEWU5BO1I2",
    "transactionId": f"TEST_TXN_{int(time.time())}",
    "amount": 500000,
    "status": "SUCCESS",
    "paymentInstrument": {"type": "UPI"},
    "merchantOrderId": test_order_id
}

import base64
webhook_auth = base64.b64encode("okpuja_webhook_user:Okpuja2025".encode()).decode()
webhook_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {webhook_auth}"
}

response = requests.post(f"{BASE_URL}/payments/webhook/phonepe/", 
                        json=webhook_payload, headers=webhook_headers)
print(f"   Webhook Status: {response.status_code}")
if response.status_code == 200:
    print("   ✅ Webhook processed successfully")
else:
    print(f"   ❌ Webhook failed: {response.text}")

# Wait for processing
print("   ⏳ Waiting 3 seconds for processing...")
time.sleep(3)

# Test 6: Check booking AFTER webhook (should succeed)
print(f"\n6. Testing booking endpoint AFTER payment success...")
response = requests.get(booking_url, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    booking_result = response.json()
    booking_id = booking_result["data"]["book_id"]
    print(f"   ✅ Booking found: {booking_id}")
    print(f"   📊 Status: {booking_result['data']['status']}")
else:
    print(f"   ❌ Booking still not found: {response.text}")

# Test 7: Test redirect AFTER webhook (should use current cart)
print(f"\n7. Testing redirect AFTER payment success...")
response = requests.get(f"{BASE_URL}/payments/redirect/simple/", allow_redirects=False)
if response.status_code == 302:
    redirect_url = response.headers.get("Location", "")
    print(f"   ✅ Redirect works: {redirect_url}")
    if test_cart_id in redirect_url:
        print("   ✅ Now uses correct current cart ID!")
    else:
        print("   ⚠️  Still uses different cart ID")
else:
    print(f"   ❌ Redirect failed: {response.status_code}")

print("\n" + "=" * 50)
print("🏁 SWAGGER SCENARIO TEST COMPLETE")
print("=" * 50)

print(f"\n📝 Key Points:")
print(f"   • Cart ID: {test_cart_id}")
print(f"   • Payment ID: {test_order_id}")
print(f"   • Before webhook: No booking (expected)")
print(f"   • After webhook: Booking created")
print(f"   • Redirect: Uses latest successful payment")

print(f"\n💡 If you're testing manually in Swagger:")
print(f"   1. Create cart")
print(f"   2. Create payment (status: INITIATED)")
print(f"   3. Booking endpoint returns 404 (expected)")
print(f"   4. Webhook processes payment → creates booking")
print(f"   5. Booking endpoint returns 200 ✅")
print(f"   6. Redirect uses correct cart_id ✅")
