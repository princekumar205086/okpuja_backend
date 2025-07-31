#!/usr/bin/env python3
"""
Comprehensive Payment Test for Local Development
1. Login with asliprinceraj@gmail.com / testpass123
2. Create cart with puja service and package
3. Process payment with cart ID
"""

import requests
import json
from datetime import datetime, date, timedelta

# Configuration for localhost testing
API_BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{API_BASE_URL}/api/accounts/auth/login/"
CART_CREATE_ENDPOINT = f"{API_BASE_URL}/api/cart/carts/"
PAYMENT_ENDPOINT = f"{API_BASE_URL}/api/payments/payments/process-cart/"
PUJA_SERVICES_ENDPOINT = f"{API_BASE_URL}/api/puja/services/"
DEBUG_ENDPOINT = f"{API_BASE_URL}/api/payments/payments/debug-connectivity/"

# Test credentials
TEST_EMAIL = "asliprinceraj@gmail.com"
TEST_PASSWORD = "testpass123"

def login_user():
    """Login and get authentication token"""
    print("🔑 Step 1: Logging in...")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(LOGIN_ENDPOINT, json=login_data, timeout=30)
        print(f"   Login Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access')
            
            if access_token:
                print(f"   ✅ Login successful")
                print(f"   Token: {access_token[:20]}...")
                return access_token
            else:
                print(f"   ❌ No access token in response: {result}")
                return None
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Login error: {str(e)}")
        return None

def get_puja_services(token):
    """Get available puja services"""
    print("\n🔍 Step 2: Getting available puja services...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(PUJA_SERVICES_ENDPOINT, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            services = response.json()
            
            if isinstance(services, dict) and 'results' in services:
                services_list = services['results']
            elif isinstance(services, list):
                services_list = services
            else:
                services_list = []
            
            if services_list:
                print(f"   ✅ Found {len(services_list)} puja services")
                for i, service in enumerate(services_list[:3]):  # Show first 3
                    print(f"   Service {i+1}: ID={service.get('id')}, Name={service.get('name')}")
                    packages = service.get('packages', [])
                    if packages:
                        for j, package in enumerate(packages[:2]):  # Show first 2 packages
                            print(f"     Package {j+1}: ID={package.get('id')}, Name={package.get('name')}, Price=₹{package.get('price')}")
                
                # Return the first service and its first package for testing
                first_service = services_list[0]
                first_package = first_service.get('packages', [{}])[0] if first_service.get('packages') else {}
                
                return {
                    'service_id': first_service.get('id'),
                    'service_name': first_service.get('name'),
                    'package_id': first_package.get('id'),
                    'package_name': first_package.get('name'),
                    'package_price': first_package.get('price')
                }
            else:
                print("   ⚠️ No puja services found")
                return None
        else:
            print(f"   ❌ Failed to get services: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error getting services: {str(e)}")
        return None

def create_cart(token, service_info):
    """Create a cart with puja service and package"""
    print(f"\n🛒 Step 3: Creating cart...")
    print(f"   Service: {service_info['service_name']} (ID: {service_info['service_id']})")
    print(f"   Package: {service_info['package_name']} (ID: {service_info['package_id']})")
    print(f"   Price: ₹{service_info['package_price']}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Calculate a future date for booking
    future_date = (datetime.now() + timedelta(days=7)).date()
    
    cart_data = {
        "service_type": "PUJA",
        "puja_service": service_info['service_id'],
        "package": service_info['package_id'],
        "selected_date": future_date.isoformat(),
        "selected_time": "10:00"
    }
    
    print(f"   Cart data: {cart_data}")
    
    try:
        response = requests.post(CART_CREATE_ENDPOINT, json=cart_data, headers=headers, timeout=30)
        print(f"   Cart creation status: {response.status_code}")
        
        if response.status_code == 201:
            cart = response.json()
            cart_id = cart.get('id')
            total_price = cart.get('total_price')
            
            print(f"   ✅ Cart created successfully!")
            print(f"   Cart ID: {cart_id}")
            print(f"   Total Price: ₹{total_price}")
            print(f"   Status: {cart.get('status')}")
            
            return {
                'cart_id': cart_id,
                'total_price': total_price,
                'cart_data': cart
            }
        else:
            print(f"   ❌ Cart creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Cart creation error: {str(e)}")
        return None

def test_payment_connectivity(token):
    """Test PhonePe connectivity"""
    print("\n🔍 Step 4: Testing PhonePe connectivity...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(DEBUG_ENDPOINT, headers=headers, timeout=30)
        print(f"   Debug status: {response.status_code}")
        
        if response.status_code == 200:
            debug_info = response.json()
            
            # Check network connectivity
            network_tests = debug_info.get('network_tests', {})
            phonepe_reachable = any(
                test.get('reachable', False) 
                for url, test in network_tests.items() 
                if 'phonepe.com' in url
            )
            
            if phonepe_reachable:
                print("   ✅ PhonePe API is reachable")
            else:
                print("   ⚠️ PhonePe API connectivity issues")
            
            # Check gateway initialization
            if debug_info.get('api_test', {}).get('gateway_init') == 'SUCCESS':
                print("   ✅ PhonePe Gateway initialized successfully")
                return True
            else:
                print("   ⚠️ PhonePe Gateway initialization issues")
                return False
        else:
            print(f"   ⚠️ Debug endpoint issue: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ⚠️ Debug connectivity error: {str(e)}")
        return False

def process_payment(token, cart_info):
    """Process payment for the cart"""
    print(f"\n💳 Step 5: Processing payment for cart {cart_info['cart_id']}...")
    print(f"   Amount: ₹{cart_info['total_price']}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payment_data = {
        "cart_id": cart_info['cart_id'],
        "method": "PHONEPE"
    }
    
    try:
        response = requests.post(PAYMENT_ENDPOINT, json=payment_data, headers=headers, timeout=60)
        print(f"   Payment status: {response.status_code}")
        
        if response.status_code == 201:
            # Success response
            result = response.json()
            print("   ✅ Payment processing successful!")
            print(f"   Payment ID: {result.get('payment_id')}")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            print(f"   Merchant Transaction ID: {result.get('merchant_transaction_id')}")
            print(f"   Amount: ₹{result.get('amount')}")
            print(f"   Status: {result.get('status')}")
            
            payment_url = result.get('payment_url') or result.get('checkout_url')
            if payment_url:
                print(f"   🔗 Payment URL: {payment_url}")
                print("\n   📋 Next Steps:")
                print("   1. Copy the payment URL above")
                print("   2. Open it in your browser")
                print("   3. Complete the test payment using PhonePe Test App")
                print("   4. Check webhook status on your server")
            else:
                print("   ⚠️ No payment URL received")
                
            return {
                'success': True,
                'payment_id': result.get('payment_id'),
                'payment_url': payment_url,
                'transaction_id': result.get('transaction_id')
            }
            
        elif response.status_code == 400:
            # Client error with detailed response
            result = response.json()
            print(f"   ❌ Payment failed: {result.get('error_category', 'UNKNOWN')}")
            print(f"   Message: {result.get('user_message', 'Payment processing failed')}")
            
            # Check for debug options (development mode)
            debug_options = result.get('debug_options', {})
            if debug_options:
                print("\n   🔧 Debug Options Available:")
                simulate_url = debug_options.get('simulate_payment_url')
                if simulate_url:
                    print(f"   Simulate Success URL: {simulate_url}")
                    
                    # Try payment simulation
                    print("\n   🎯 Attempting payment simulation...")
                    simulate_response = requests.post(
                        f"{API_BASE_URL}{simulate_url}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if simulate_response.status_code == 200:
                        sim_result = simulate_response.json()
                        print("   ✅ Payment simulation successful!")
                        print(f"   Payment ID: {sim_result.get('payment_id')}")
                        print(f"   Status: {sim_result.get('status')}")
                        if sim_result.get('booking_created'):
                            print(f"   Booking Created: {sim_result.get('booking_id')}")
                        return {
                            'success': True,
                            'simulated': True,
                            'payment_id': sim_result.get('payment_id'),
                            'booking_id': sim_result.get('booking_id')
                        }
                    else:
                        print(f"   ❌ Payment simulation failed: {simulate_response.status_code}")
            
            return {'success': False, 'error': result}
            
        else:
            print(f"   ❌ Unexpected error: {response.status_code}")
            try:
                error_result = response.json()
                print(f"   Error details: {error_result}")
            except:
                print(f"   Raw response: {response.text}")
            return {'success': False, 'error': 'Unexpected error'}
            
    except Exception as e:
        print(f"   ❌ Payment request error: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main test function"""
    print("🧪 Comprehensive Payment Test for Local Development")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"👤 Test User: {TEST_EMAIL}")
    print("=" * 60)
    
    # Step 1: Login
    token = login_user()
    if not token:
        print("\n❌ Test failed at login step")
        return False
    
    # Step 2: Get puja services
    service_info = get_puja_services(token)
    if not service_info:
        print("\n❌ Test failed at service retrieval step")
        return False
    
    # Step 3: Create cart
    cart_info = create_cart(token, service_info)
    if not cart_info:
        print("\n❌ Test failed at cart creation step")
        return False
    
    # Step 4: Test PhonePe connectivity
    connectivity_ok = test_payment_connectivity(token)
    
    # Step 5: Process payment
    payment_result = process_payment(token, cart_info)
    
    print("\n" + "=" * 60)
    if payment_result.get('success'):
        print("✅ Payment test completed successfully!")
        if payment_result.get('simulated'):
            print("🎯 Payment was simulated for development testing")
        print(f"\n📋 Summary:")
        print(f"   Cart ID: {cart_info['cart_id']}")
        print(f"   Payment ID: {payment_result.get('payment_id')}")
        if payment_result.get('booking_id'):
            print(f"   Booking ID: {payment_result.get('booking_id')}")
        print(f"   Amount: ₹{cart_info['total_price']}")
    else:
        print("❌ Payment test failed!")
        print(f"   Error: {payment_result.get('error', 'Unknown error')}")
    
    print(f"\n🔧 Development Notes:")
    print(f"   - Test user: {TEST_EMAIL}")
    print(f"   - Server: localhost:8000")
    print(f"   - PhonePe connectivity: {'OK' if connectivity_ok else 'Issues detected'}")
    print(f"   - Cart created with ID: {cart_info['cart_id'] if cart_info else 'N/A'}")

if __name__ == "__main__":
    main()
