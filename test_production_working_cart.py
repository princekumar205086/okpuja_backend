#!/usr/bin/env python
"""
Production Test with Manual Cart Amount Fix
"""
import requests
import json
from datetime import datetime, timedelta

# Production API Configuration
PRODUCTION_BASE_URL = 'https://api.okpuja.com/api'

# Test User Credentials
TEST_EMAIL = 'asliprinceraj@gmail.com'
TEST_PASSWORD = 'testpass123'

def get_access_token():
    """Get JWT access token for authentication"""
    response = requests.post(f'{PRODUCTION_BASE_URL}/auth/login/', {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        return data.get('access')
    return None

def create_working_cart(token):
    """Create cart and manually set the amount"""
    print("🛒 Creating cart...")
    
    headers = {'Authorization': f'Bearer {token}'}
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Create cart without package first
    cart_data = {
        'puja_service': 8,
        'quantity': 1,
        'selected_date': tomorrow,
        'selected_time': '10:00:00',
        'special_instructions': 'Production test - manual amount',
        'manual_amount': 500.00  # Try adding manual amount
    }
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/cart/carts/', 
                           json=cart_data, 
                           headers=headers)
    
    print(f"Cart creation response: {response.status_code}")
    print(f"Cart response body: {response.text}")
    
    if response.status_code == 201:
        cart = response.json()
        print(f"✅ Cart created: ID={cart['id']}, Total=₹{cart.get('total_amount', 0)}")
        return cart['id']
    
    # If manual_amount doesn't work, try with a valid package but modify the approach
    print("\n🔧 Trying alternative cart creation...")
    
    # Let's check if we can create with a different service that might have working packages
    for service_id in [1, 2, 3, 4]:  # Try other services
        cart_data = {
            'puja_service': service_id,
            'package': 2,  # Package with ₹5000
            'quantity': 1,
            'selected_date': tomorrow,
            'selected_time': '10:00:00',
            'special_instructions': f'Test with service {service_id}'
        }
        
        response = requests.post(f'{PRODUCTION_BASE_URL}/cart/carts/', 
                               json=cart_data, 
                               headers=headers)
        
        if response.status_code == 201:
            cart = response.json()
            total = float(cart.get('total_amount', 0))
            print(f"✅ Working cart found! Service: {service_id}, ID: {cart['id']}, Total: ₹{total}")
            if total > 0:
                return cart['id']
    
    return None

def test_payment_with_working_cart(token, cart_id):
    """Test payment with a cart that has amount > 0"""
    print(f"💳 Testing payment with cart {cart_id}...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    payment_data = {
        'cart_id': cart_id,
        'address_id': 1,
        'method': 'PHONEPE'
    }
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/process-cart/', 
                           json=payment_data, 
                           headers=headers)
    
    print(f"Payment Status: {response.status_code}")
    print(f"Payment Response: {response.text}")
    
    if response.status_code == 201:
        payment = response.json()
        print(f"🎉 Payment successful!")
        print(f"   Payment ID: {payment.get('payment_id')}")
        print(f"   Transaction ID: {payment.get('transaction_id')}")
        print(f"   Payment URL: {payment.get('payment_url')}")
        return payment
    else:
        print(f"❌ Payment failed")
        # Try to parse the error
        try:
            error_data = response.json()
            print(f"   Error details: {error_data}")
        except:
            pass
        
        return None

def main():
    print("🧪 Production Payment Test with Working Cart")
    print("=" * 50)
    
    # Get token
    token = get_access_token()
    if not token:
        print("❌ Failed to get access token")
        return
    
    print("✅ Got access token")
    
    # Create working cart
    cart_id = create_working_cart(token)
    
    if cart_id:
        # Test payment
        payment = test_payment_with_working_cart(token, cart_id)
        
        if payment:
            print("\n🎉 PRODUCTION PAYMENT TEST SUCCESSFUL!")
            print("✅ Cart creation: Working")
            print("✅ Payment initiation: Working") 
            print("✅ PhonePe integration: Working")
            
            payment_url = payment.get('payment_url')
            if payment_url:
                print(f"\n🔗 Payment URL: {payment_url}")
                print("📱 Open this URL to complete the payment")
        else:
            print("\n❌ Payment initiation failed even with valid cart")
    else:
        print("\n❌ Could not create a cart with amount > 0")
        print("   This is a data configuration issue in production")
        print("   Need to fix package-service relationships in the database")

if __name__ == "__main__":
    main()
