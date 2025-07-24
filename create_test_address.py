#!/usr/bin/env python3
import requests
import json

def create_address_for_user():
    """Create address for the test user"""
    
    # Login first
    print("1. Logging in...")
    login_response = requests.post('https://backend.okpuja.com/api/accounts/login/', json={
        'email': 'asliprinceraj@gmail.com',
        'password': 'testpass123'
    })
    
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return None
    
    try:
        token = login_response.json()['access']
        print("✅ Login successful")
    except:
        print(f"Login response: {login_response.text}")
        return None
    
    # Check existing addresses
    print("2. Checking existing addresses...")
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    addresses_response = requests.get('https://backend.okpuja.com/api/accounts/addresses/', headers=headers)
    
    print(f"Addresses status: {addresses_response.status_code}")
    print(f"Addresses response: {addresses_response.text}")
    
    # Create address if needed
    print("3. Creating test address...")
    address_data = {
        'address_line_1': '123 Test Street',
        'address_line_2': 'Apartment 1', 
        'city': 'Patna',
        'state': 'Bihar',
        'pin_code': '800001',
        'country': 'India',
        'address_type': 'HOME',
        'landmark': 'Near Test Market'
    }
    
    create_response = requests.post('https://backend.okpuja.com/api/accounts/addresses/', 
                                  headers=headers, json=address_data)
    print(f"Create address status: {create_response.status_code}")
    print(f"Create response: {create_response.text}")
    
    if create_response.status_code in [200, 201]:
        try:
            address = create_response.json()
            print(f"✅ Address created with ID: {address.get('id')}")
            return address.get('id')
        except:
            print("Address created but couldn't parse response")
            return 1  # Assume first address
    else:
        print("❌ Failed to create address")
        return None

if __name__ == "__main__":
    address_id = create_address_for_user()
    if address_id:
        print(f"\n🎉 Address ID {address_id} is ready for testing!")
    else:
        print("\n❌ Could not create address")
