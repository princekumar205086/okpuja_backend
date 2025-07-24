#!/usr/bin/env python
"""
Production Test Script for OkPuja Cart-to-Booking Flow
Tests against production API with real user credentials
"""
import requests
import json
import time

# Production API Configuration
PRODUCTION_BASE_URL = 'https://backend.okpuja.com/api'

# Test User Credentials
TEST_EMAIL = 'asliprinceraj@gmail.com'
TEST_PASSWORD = 'testpass123'

# Test Data
PUJA_SERVICE_ID = 8
PACKAGE_ID = 2

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

def get_available_packages(token, puja_service_id):
    """Get available packages for a puja service"""
    print(f"2a. Getting available packages for service {puja_service_id}...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f'{PRODUCTION_BASE_URL}/puja/services/{puja_service_id}/', 
                          headers=headers)
    
    if response.status_code == 200:
        service = response.json()
        packages = service.get('packages', [])
        print(f"✅ Found {len(packages)} packages:")
        for pkg in packages:
            print(f"   Package ID: {pkg.get('id')} - {pkg.get('name')} - ₹{pkg.get('price', 0)}")
        return packages
    else:
        print(f"❌ Failed to get packages: {response.status_code} - {response.text}")
        return []

def create_production_cart(token):
    """Create cart with specific puja service and package"""
    print("2. Creating cart with production data...")
    
    # First, get available packages
    packages = get_available_packages(token, PUJA_SERVICE_ID)
    
    # Use the first available package if PACKAGE_ID doesn't work
    package_id = PACKAGE_ID
    if packages:
        # Check if our PACKAGE_ID exists, otherwise use first available
        package_ids = [pkg['id'] for pkg in packages]
        if PACKAGE_ID not in package_ids:
            package_id = packages[0]['id']
            print(f"   Using package ID {package_id} instead of {PACKAGE_ID}")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get tomorrow's date for booking
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    cart_data = {
        'puja_service': PUJA_SERVICE_ID,
        'package': package_id,
        'quantity': 1,
        'selected_date': tomorrow,
        'selected_time': '10:00:00',
        'special_instructions': 'Test booking from API - Production test'
    }
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/cart/carts/', 
                           json=cart_data, 
                           headers=headers)
    
    if response.status_code == 201:
        cart = response.json()
        print(f"✅ Cart created with ID: {cart['id']}")
        print(f"   Service ID: {cart.get('puja_service', {}).get('id', 'Unknown')}")
        print(f"   Package ID: {cart.get('package', {}).get('id', 'Unknown') if cart.get('package') else 'None'}")
        print(f"   Date: {cart.get('selected_date', 'Unknown')}")
        print(f"   Time: {cart.get('selected_time', 'Unknown')}")
        print(f"   Total: ₹{cart.get('total_amount', '0.00')}")
        return cart['id']
    else:
        print(f"❌ Cart creation failed: {response.status_code} - {response.text}")
        return None

def initiate_production_payment(token, cart_id):
    """Initiate payment for cart in production"""
    print("3. Initiating payment in production...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    payment_data = {
        'cart_id': cart_id,
        'address_id': 1,  # Assuming user has address ID 1
        'method': 'PHONEPE'
    }
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/process-cart/', 
                           json=payment_data, 
                           headers=headers)
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 201:
        payment = response.json()
        print(f"✅ Payment initiated with ID: {payment['payment_id']}")
        print(f"   Transaction ID: {payment['transaction_id']}")
        print(f"   Payment URL: {payment.get('payment_url', 'No URL provided')}")
        return payment['payment_id'], payment.get('payment_url')
    else:
        print(f"❌ Payment initiation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Raw response: {response.text}")
        return None, None

def check_payment_status(token, payment_id):
    """Check payment status in production"""
    print(f"4. Checking payment status...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f'{PRODUCTION_BASE_URL}/payments/payments/{payment_id}/', 
                          headers=headers)
    
    if response.status_code == 200:
        payment = response.json()
        print(f"✅ Payment Status: {payment.get('status', 'Unknown')}")
        return payment
    else:
        print(f"❌ Payment status check failed: {response.status_code} - {response.text}")
        return None

def simulate_payment_success(token, payment_id):
    """Simulate payment success for testing (if endpoint exists)"""
    print("5. Simulating payment success...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/{payment_id}/simulate-success/', 
                           headers=headers)
    
    if response.status_code == 200:
        print("✅ Payment success simulated")
        return True
    else:
        print(f"❌ Payment simulation failed or endpoint not available: {response.status_code}")
        return False

def check_bookings(token):
    """Check if booking was created"""
    print("6. Checking for created booking...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f'{PRODUCTION_BASE_URL}/booking/bookings/', headers=headers)
    
    if response.status_code == 200:
        bookings = response.json()
        if isinstance(bookings, dict) and 'results' in bookings:
            bookings = bookings['results']
        
        if bookings:
            latest_booking = bookings[0] if isinstance(bookings, list) else bookings
            print(f"✅ Booking found:")
            print(f"   Booking ID: {latest_booking.get('book_id', 'Unknown')}")
            print(f"   Status: {latest_booking.get('status', 'Unknown')}")
            print(f"   Service: {latest_booking.get('puja_service', 'Unknown')}")
            return latest_booking
        else:
            print("❌ No bookings found")
            return None
    else:
        print(f"❌ Booking check failed: {response.status_code} - {response.text}")
        return None

def main():
    """Run complete production test"""
    print("🧪 Testing Production Cart-to-Booking Flow...")
    print(f"Production API: {PRODUCTION_BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    print(f"Puja Service ID: {PUJA_SERVICE_ID}")
    print(f"Package ID: {PACKAGE_ID}")
    print("-" * 60)
    
    # Step 1: Get access token
    token = get_access_token()
    if not token:
        return
    
    # Step 2: Create cart
    cart_id = create_production_cart(token)
    if not cart_id:
        return
    
    # Step 3: Initiate payment
    payment_id, payment_url = initiate_production_payment(token, cart_id)
    if not payment_id:
        return
    
    # Step 4: Check payment status
    payment = check_payment_status(token, payment_id)
    
    # Step 5: Try to simulate success (for testing)
    if payment:
        simulate_payment_success(token, payment_id)
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Step 6: Check for booking
        booking = check_bookings(token)
        
        if booking:
            print("\n🎉 Production test completed successfully!")
            print("📧 Check email for booking confirmation")
        else:
            print("\n⚠️ Payment initiated but booking not created automatically")
            print("   This might be expected if payment webhook hasn't been triggered")
    
    print(f"\n📋 Summary:")
    print(f"   Payment URL: {payment_url}")
    print(f"   Test this URL in browser to complete payment")

if __name__ == "__main__":
    main()
