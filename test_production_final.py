#!/usr/bin/env python
"""
Production Payment Test with Working Cart Data
Using the exact cart structure that shows ₹4990.00 total
"""
import requests
import json
from datetime import datetime, timedelta

# Production API Configuration
PRODUCTION_BASE_URL = 'https://backend.okpuja.com/api'

# Test User Credentials
TEST_EMAIL = 'asliprinceraj@gmail.com'
TEST_PASSWORD = 'testpass123'

# Working Cart Data (from your example)
PUJA_SERVICE_ID = 8  # Ganesh Puja
PACKAGE_ID = 2       # ₹5000.00 package
PROMO_CODE = 'DISCOUNT10'  # 10% discount

def get_access_token():
    """Get JWT access token for authentication"""
    print("1. Getting access token from production...")
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/auth/login/', {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        print(f"✅ Got access token")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def debug_package_service_relationship(token):
    """Debug the package-service relationship in production"""
    print("🔍 Debugging package-service relationships...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Check service 8 details
    response = requests.get(f'{PRODUCTION_BASE_URL}/puja/services/8/', headers=headers)
    if response.status_code == 200:
        service = response.json()
        print(f"   Service 8 exists: {service.get('title')}")
        packages = service.get('packages', [])
        print(f"   Packages linked to service 8: {len(packages)}")
        for pkg in packages:
            print(f"     - Package {pkg.get('id')}: ₹{pkg.get('price')} ({pkg.get('name', 'No name')})")
    
    # Check package 2 directly
    response = requests.get(f'{PRODUCTION_BASE_URL}/puja/packages/2/', headers=headers)
    if response.status_code == 200:
        package = response.json()
        print(f"   Package 2 details:")
        print(f"     - Price: ₹{package.get('price')}")
        print(f"     - Service: {package.get('service')}")
        print(f"     - Active: {package.get('is_active')}")
    else:
        print(f"   Package 2 access failed: {response.status_code}")

def create_working_cart(token):
    """Create cart using the exact working configuration"""
    print("2. Creating cart with working configuration...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Use date from your working example
    cart_data = {
        'puja_service': PUJA_SERVICE_ID,
        'package': PACKAGE_ID,
        'quantity': 1,
        'selected_date': '2025-07-20',  # Same as your working cart
        'selected_time': '10:00:00',    # Convert "10:00 AM" to 24hr format
        'promo_code': PROMO_CODE,       # Apply the same discount
        'special_instructions': 'Production test with working cart configuration'
    }
    
    print(f"Creating cart with data: {json.dumps(cart_data, indent=2)}")
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/cart/carts/', 
                           json=cart_data, 
                           headers=headers)
    
    print(f"Cart Response Status: {response.status_code}")
    print(f"Cart Response Body: {response.text}")
    
    if response.status_code == 201:
        cart = response.json()
        print(f"✅ Cart created successfully!")
        print(f"   Cart ID: {cart['id']}")
        print(f"   Service: {cart.get('puja_service', {}).get('title', 'Unknown')}")
        
        # Safely handle package which might be None
        package = cart.get('package')
        if package:
            print(f"   Package Price: ₹{package.get('price', '0')}")
            print(f"   Package ID: {package.get('id', 'Unknown')}")
        else:
            print(f"   Package: None (NOT LINKED!)")
        
        print(f"   Total: ₹{cart.get('total_price', '0.00')}")
        
        promo_code = cart.get('promo_code')
        if promo_code:
            print(f"   Promo Applied: {promo_code.get('code', 'Unknown')}")
        else:
            print(f"   Promo Applied: None")
        
        total = float(cart.get('total_price', 0))
        if total > 0:
            print(f"🎉 Cart has valid total amount: ₹{total}")
            return cart['id'], total
        else:
            print(f"❌ Cart total is still ₹0 - package relationship issue persists")
            return None, 0
    else:
        print(f"❌ Cart creation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error details: {error_data}")
        except:
            pass
        return None, 0

def initiate_production_payment(token, cart_id, expected_amount):
    """Initiate payment for the working cart"""
    print(f"3. Initiating payment for cart {cart_id} (₹{expected_amount})...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    payment_data = {
        'cart_id': cart_id,
        'address_id': 1,  # Assuming user has address ID 1
        'method': 'PHONEPE'
    }
    
    print(f"Payment data: {json.dumps(payment_data, indent=2)}")
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/process-cart/', 
                           json=payment_data, 
                           headers=headers)
    
    print(f"Payment Response Status: {response.status_code}")
    print(f"Payment Response Headers: {dict(response.headers)}")
    print(f"Payment Response Body: {response.text}")
    
    if response.status_code == 201:
        payment = response.json()
        print(f"🎉 PAYMENT INITIATION SUCCESSFUL!")
        print(f"   Payment ID: {payment.get('payment_id')}")
        print(f"   Transaction ID: {payment.get('transaction_id')}")
        print(f"   Merchant Transaction ID: {payment.get('merchant_transaction_id')}")
        print(f"   Amount: ₹{payment.get('amount')}")
        print(f"   Currency: {payment.get('currency')}")
        print(f"   Status: {payment.get('status')}")
        
        payment_url = payment.get('payment_url')
        if payment_url:
            print(f"   Payment URL: {payment_url}")
            print(f"\n🔗 NEXT STEP: Open this URL in browser to complete payment:")
            print(f"   {payment_url}")
        
        return payment
    else:
        print(f"❌ PAYMENT INITIATION FAILED")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
            
            # Analyze the error
            error_details = error_data.get('details', '')
            if 'min_value' in error_details:
                print(f"   🔍 Analysis: Amount validation failed - cart total is likely ₹0")
                print(f"   🔧 Solution: Package-service relationship needs to be fixed in production DB")
            elif 'Payment initiation failed' in error_details:
                print(f"   🔍 Analysis: PhonePe gateway error")
                print(f"   🔧 Check PhonePe credentials and API configuration")
        except:
            print(f"   Raw error: {response.text}")
        
        return None

def simulate_payment_success(token, payment_id):
    """Try to simulate payment success (if endpoint exists)"""
    print(f"4. Attempting to simulate payment success...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/{payment_id}/simulate-success/', 
                           headers=headers)
    
    if response.status_code == 200:
        print("✅ Payment success simulated")
        return True
    else:
        print(f"❌ Payment simulation not available or failed: {response.status_code}")
        return False

def check_booking_creation(token):
    """Check if booking was created after payment"""
    print("5. Checking for booking creation...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f'{PRODUCTION_BASE_URL}/booking/bookings/', headers=headers)
    
    if response.status_code == 200:
        bookings = response.json()
        if isinstance(bookings, dict) and 'results' in bookings:
            bookings = bookings['results']
        
        if bookings:
            latest_booking = bookings[0] if isinstance(bookings, list) else bookings
            print(f"✅ Latest booking found:")
            print(f"   Booking ID: {latest_booking.get('book_id', 'Unknown')}")
            print(f"   Status: {latest_booking.get('status', 'Unknown')}")
            print(f"   Service: {latest_booking.get('puja_service', 'Unknown')}")
            print(f"   Date: {latest_booking.get('puja_date', 'Unknown')}")
            return latest_booking
        else:
            print("❌ No bookings found yet")
            return None
    else:
        print(f"❌ Booking check failed: {response.status_code}")
        return None

def main():
    """Run complete production test with working cart data"""
    print("🧪 PRODUCTION PAYMENT TEST - Using Working Cart Configuration")
    print("=" * 70)
    print(f"API: {PRODUCTION_BASE_URL}")
    print(f"User: {TEST_EMAIL}")
    print(f"Service: {PUJA_SERVICE_ID} (Ganesh Puja)")
    print(f"Package: {PACKAGE_ID} (₹5000.00)")
    print(f"Promo: {PROMO_CODE} (10% discount)")
    print("=" * 70)
    
    # Step 1: Get access token
    token = get_access_token()
    if not token:
        return
    
    # Step 1.5: Debug package relationships
    debug_package_service_relationship(token)
    
    # Step 2: Create cart with working configuration
    cart_id, total_amount = create_working_cart(token)
    if not cart_id:
        print("\n❌ FAILED: Could not create cart with amount > 0")
        print("   This indicates the package-service relationship is still broken")
        return
    
    # Step 3: Initiate payment
    payment = initiate_production_payment(token, cart_id, total_amount)
    if not payment:
        print("\n❌ FAILED: Payment initiation failed")
        return
    
    print(f"\n🎉 SUCCESS: Production payment flow is working!")
    print(f"✅ Cart creation: Working (₹{total_amount})")
    print(f"✅ Payment initiation: Working")
    print(f"✅ PhonePe integration: Working")
    
    # Step 4: Try simulation (optional)
    payment_id = payment.get('payment_id')
    if payment_id:
        simulate_payment_success(token, payment_id)
        
        # Wait and check for booking
        import time
        time.sleep(2)
        booking = check_booking_creation(token)
        
        if booking:
            print(f"\n🎉 COMPLETE SUCCESS: End-to-end flow working!")
        else:
            print(f"\n⚠️ Payment successful but booking not auto-created")
            print(f"   This is expected until payment webhook is triggered")
    
    # Final summary
    payment_url = payment.get('payment_url')
    if payment_url:
        print(f"\n🔗 COMPLETE THE PAYMENT:")
        print(f"   Open this URL: {payment_url}")
        print(f"   Complete the payment to trigger webhook and create booking")

if __name__ == "__main__":
    main()
