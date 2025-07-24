#!/usr/bin/env python
"""
Production Cart Debug Script
Debug cart creation and pricing issues
"""
import requests
import json
from datetime import datetime, timedelta

# Production API Configuration
PRODUCTION_BASE_URL = 'https://backend.okpuja.com/api'

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

def list_puja_services(token):
    """List available puja services"""
    print("📋 Listing available puja services...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{PRODUCTION_BASE_URL}/puja/services/', headers=headers)
    
    if response.status_code == 200:
        services = response.json()
        if isinstance(services, dict) and 'results' in services:
            services = services['results']
        
        print(f"Found {len(services)} services:")
        for service in services[:5]:  # Show first 5
            print(f"   ID: {service.get('id')} - {service.get('title')} - Type: {service.get('type')}")
        return services
    else:
        print(f"❌ Failed to get services: {response.status_code}")
        return []

def list_packages(token):
    """List available packages"""
    print("📦 Listing available packages...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{PRODUCTION_BASE_URL}/puja/packages/', headers=headers)
    
    if response.status_code == 200:
        packages = response.json()
        if isinstance(packages, dict) and 'results' in packages:
            packages = packages['results']
        
        print(f"Found {len(packages)} packages:")
        for package in packages[:10]:  # Show first 10
            service_id = package.get('service', {}).get('id') if isinstance(package.get('service'), dict) else package.get('service')
            print(f"   ID: {package.get('id')} - {package.get('name')} - ₹{package.get('price', 0)} - Service: {service_id}")
        return packages
    else:
        print(f"❌ Failed to get packages: {response.status_code}")
        return []

def test_cart_creation_variations(token, services, packages):
    """Test different cart creation approaches"""
    print("🧪 Testing cart creation variations...")
    
    headers = {'Authorization': f'Bearer {token}'}
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Find a service with a package
    test_cases = []
    
    # Case 1: Service 8 with its packages
    service_8_packages = [p for p in packages if p.get('service') == 8 or (isinstance(p.get('service'), dict) and p.get('service', {}).get('id') == 8)]
    if service_8_packages:
        test_cases.append({
            'name': 'Service 8 with its package',
            'service_id': 8,
            'package_id': service_8_packages[0]['id'],
            'expected_price': service_8_packages[0]['price']
        })
    
    # Case 2: Any service with any package
    if packages and services:
        test_cases.append({
            'name': 'First available service and package',
            'service_id': services[0]['id'],
            'package_id': packages[0]['id'],
            'expected_price': packages[0]['price']
        })
    
    # Case 3: Service 8 without package
    test_cases.append({
        'name': 'Service 8 without package',
        'service_id': 8,
        'package_id': None,
        'expected_price': 0
    })
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        cart_data = {
            'puja_service': test_case['service_id'],
            'quantity': 1,
            'selected_date': tomorrow,
            'selected_time': '10:00:00',
            'special_instructions': f'Test case {i}'
        }
        
        if test_case['package_id']:
            cart_data['package'] = test_case['package_id']
        
        print(f"Creating cart with data: {cart_data}")
        
        response = requests.post(f'{PRODUCTION_BASE_URL}/cart/carts/', 
                               json=cart_data, 
                               headers=headers)
        
        if response.status_code == 201:
            cart = response.json()
            print(f"✅ Cart created: ID={cart['id']}, Total=₹{cart.get('total_amount', 0)}")
            
            if float(cart.get('total_amount', 0)) > 0:
                print(f"🎉 Found working configuration!")
                return cart['id'], test_case
        else:
            print(f"❌ Cart creation failed: {response.status_code} - {response.text}")
    
    return None, None

def main():
    print("🔍 Production Cart & Pricing Debug")
    print("=" * 50)
    
    # Get token
    token = get_access_token()
    if not token:
        print("❌ Failed to get access token")
        return
    
    print("✅ Got access token")
    
    # List services and packages
    services = list_puja_services(token)
    packages = list_packages(token)
    
    # Test cart creation
    working_cart_id, working_config = test_cart_creation_variations(token, services, packages)
    
    if working_cart_id:
        print(f"\n🎯 Working Configuration Found:")
        print(f"   Service ID: {working_config['service_id']}")
        print(f"   Package ID: {working_config['package_id']}")
        print(f"   Cart ID: {working_cart_id}")
        
        # Now test payment with working cart
        print(f"\n💳 Testing payment with working cart...")
        
        headers = {'Authorization': f'Bearer {token}'}
        payment_data = {
            'cart_id': working_cart_id,
            'address_id': 1,
            'method': 'PHONEPE'
        }
        
        response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/process-cart/', 
                               json=payment_data, 
                               headers=headers)
        
        print(f"Payment Response: {response.status_code}")
        print(f"Payment Body: {response.text}")
        
        if response.status_code == 201:
            print("🎉 Payment initiation successful!")
        else:
            print("❌ Payment initiation still failing")
    else:
        print("\n❌ No working cart configuration found")

if __name__ == "__main__":
    main()
