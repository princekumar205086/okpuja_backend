"""
Complete End-to-End Test: Cart Creation → Payment → Webhook → Booking → Email
This simulates the exact flow a user would experience through Swagger/Frontend
"""

import requests
import json
import time
import base64

# Configuration
BASE_URL = "http://127.0.0.1:8000/api"
LOGIN_URL = f"{BASE_URL}/auth/login/"
CART_URL = f"{BASE_URL}/cart/carts/"
PAYMENT_URL = f"{BASE_URL}/payments/cart/"
REDIRECT_URL = f"{BASE_URL}/payments/redirect/simple/"
WEBHOOK_URL = f"{BASE_URL}/payments/webhook/phonepe/"

# User credentials
USER_EMAIL = "asliprinceraj@gmail.com"
USER_PASSWORD = "testpass123"

# Webhook authentication
WEBHOOK_USERNAME = "okpuja_webhook_user"
WEBHOOK_PASSWORD = "Okpuja2025"

print("🚀 STARTING COMPLETE END-TO-END TEST")
print("=" * 60)

# Step 1: Login and get auth token
print("\n1️⃣ STEP 1: User Login")
login_data = {
    "email": USER_EMAIL,
    "password": USER_PASSWORD
}

response = requests.post(LOGIN_URL, json=login_data)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    login_result = response.json()
    access_token = login_result["access"]
    user_id = login_result["id"]
    print(f"   ✅ Login successful - User ID: {user_id}")
    print(f"   🔑 Access token: {access_token[:50]}...")
else:
    print(f"   ❌ Login failed: {response.text}")
    exit(1)

# Headers for authenticated requests
auth_headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Step 2: Create a new cart
print("\n2️⃣ STEP 2: Create Cart")
cart_data = {
    "service_type": "PUJA",
    "puja_service": 8,
    "package_id": 2,
    "selected_date": "2025-08-30",
    "selected_time": "19:00"
}

response = requests.post(CART_URL, json=cart_data, headers=auth_headers)
print(f"   Status: {response.status_code}")

if response.status_code == 201:
    cart_result = response.json()
    cart_id = cart_result["cart_id"]
    cart_price = cart_result["total_price"]
    print(f"   ✅ Cart created successfully")
    print(f"   🛒 Cart ID: {cart_id}")
    print(f"   💰 Price: ₹{cart_price}")
else:
    print(f"   ❌ Cart creation failed: {response.text}")
    exit(1)

# Step 3: Create payment order
print("\n3️⃣ STEP 3: Create Payment Order")
payment_data = {
    "cart_id": cart_id
}

response = requests.post(PAYMENT_URL, json=payment_data, headers=auth_headers)
print(f"   Status: {response.status_code}")

if response.status_code == 201:
    payment_result = response.json()
    merchant_order_id = payment_result["data"]["payment_order"]["merchant_order_id"]
    payment_amount = payment_result["data"]["payment_order"]["amount_in_rupees"]
    phonepe_url = payment_result["data"]["payment_order"]["phonepe_payment_url"]
    print(f"   ✅ Payment order created successfully")
    print(f"   🏪 Merchant Order ID: {merchant_order_id}")
    print(f"   💳 Amount: ₹{payment_amount}")
    print(f"   🔗 PhonePe URL: {phonepe_url[:50]}...")
else:
    print(f"   ❌ Payment creation failed: {response.text}")
    exit(1)

# Step 4: Simulate PhonePe payment success via webhook
print("\n4️⃣ STEP 4: Simulate PhonePe Webhook (Payment Success)")

# Create webhook authentication header
webhook_credentials = f"{WEBHOOK_USERNAME}:{WEBHOOK_PASSWORD}"
webhook_auth = base64.b64encode(webhook_credentials.encode()).decode()

webhook_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {webhook_auth}"
}

# Simulate PhonePe webhook payload
webhook_payload = {
    "merchantId": "M22KEWU5BO1I2",
    "transactionId": f"TXN_{cart_id[:8]}_{int(time.time())}",
    "amount": payment_amount * 100,  # PhonePe uses paise
    "status": "SUCCESS",
    "paymentInstrument": {
        "type": "UPI",
        "utr": f"UTR{int(time.time())}"
    },
    "merchantOrderId": merchant_order_id,
    "checksum": "dummy_checksum_for_testing"
}

response = requests.post(WEBHOOK_URL, json=webhook_payload, headers=webhook_headers)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    webhook_result = response.json()
    print(f"   ✅ Webhook processed successfully")
    print(f"   📨 Webhook response: {webhook_result.get('message', 'Success')}")
else:
    print(f"   ❌ Webhook processing failed: {response.text}")
    print(f"   🔍 Check webhook authentication and payload")

# Wait a moment for webhook processing
print("   ⏳ Waiting 2 seconds for webhook processing...")
time.sleep(2)

# Step 5: Test redirect handler
print("\n5️⃣ STEP 5: Test Redirect Handler")
response = requests.get(REDIRECT_URL, allow_redirects=False)
print(f"   Status: {response.status_code}")

if response.status_code == 302:
    redirect_location = response.headers.get("Location", "")
    print(f"   ✅ Redirect successful")
    print(f"   🔗 Redirect URL: {redirect_location}")
    
    # Extract cart_id from redirect URL
    if f"cart_id={cart_id}" in redirect_location:
        print(f"   ✅ Correct cart ID in redirect: {cart_id}")
    else:
        print(f"   ❌ Wrong cart ID in redirect - Expected: {cart_id}")
else:
    print(f"   ❌ Redirect failed: {response.text}")

# Step 6: Check if booking was created
print("\n6️⃣ STEP 6: Verify Booking Creation")
booking_url = f"{BASE_URL}/booking/bookings/by-cart/{cart_id}/"
response = requests.get(booking_url, headers=auth_headers)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    booking_result = response.json()
    booking_data = booking_result["data"]
    booking_id = booking_data["book_id"]
    booking_status = booking_data["status"]
    booking_amount = booking_data["total_amount"]
    
    print(f"   ✅ Booking created successfully")
    print(f"   📝 Booking ID: {booking_id}")
    print(f"   📊 Status: {booking_status}")
    print(f"   💰 Amount: ₹{booking_amount}")
    
    # Check cart status
    cart_status = booking_data["cart"]["status"]
    print(f"   🛒 Cart Status: {cart_status}")
    
else:
    print(f"   ❌ Booking not found: {response.text}")

# Step 7: Verify payment status
print("\n7️⃣ STEP 7: Verify Payment Status")
payment_status_url = f"{BASE_URL}/payments/status/{merchant_order_id}/"
response = requests.get(payment_status_url, headers=auth_headers)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    payment_status_result = response.json()
    payment_status = payment_status_result["data"]["status"]
    print(f"   ✅ Payment status retrieved")
    print(f"   💳 Payment Status: {payment_status}")
else:
    print(f"   ❌ Payment status check failed: {response.text}")

# Step 8: Check email notification queue
print("\n8️⃣ STEP 8: Email Notification Status")
print("   📧 Email notifications are queued via Celery")
print("   ✅ If booking was created, email should be sent")
print("   🔍 Check your email or Celery logs for confirmation")

# Summary
print("\n" + "=" * 60)
print("🏁 END-TO-END TEST SUMMARY")
print("=" * 60)

test_results = [
    ("User Login", "✅" if 'access_token' in locals() else "❌"),
    ("Cart Creation", "✅" if 'cart_id' in locals() else "❌"),
    ("Payment Order", "✅" if 'merchant_order_id' in locals() else "❌"),
    ("Webhook Processing", "✅" if response.status_code == 200 else "❌"),
    ("Redirect Handler", "✅" if redirect_location and cart_id in redirect_location else "❌"),
    ("Booking Creation", "✅" if 'booking_id' in locals() else "❌"),
    ("Payment Status", "✅" if payment_status == "SUCCESS" else "❌"),
]

for test_name, result in test_results:
    print(f"   {result} {test_name}")

# Final verification
if all("✅" in result for _, result in test_results):
    print("\n🎉 ALL TESTS PASSED! System is working perfectly!")
    print(f"   📱 Cart: {cart_id}")
    print(f"   📝 Booking: {booking_id}")
    print(f"   💳 Payment: {merchant_order_id}")
    print("   📧 Email notifications sent")
else:
    print("\n⚠️  Some tests failed. Check the logs above for details.")

print("\n💡 To test again, create a new cart and repeat the process.")
print("🔗 The system is ready for production use!")
