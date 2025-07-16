#!/usr/bin/env python3
import requests
import json

def test_cart_details_production():
    """Check the exact cart details in production"""
    
    print("🧪 CHECKING PRODUCTION CART DETAILS")
    print("=" * 50)
    
    # Login
    login_response = requests.post('https://api.okpuja.com/api/auth/login/', json={
        'email': 'asliprinceraj@gmail.com', 
        'password': 'testpass123'
    })
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get cart 28 details
    print("Fetching cart 28 details from production...")
    cart_response = requests.get('https://api.okpuja.com/api/cart/carts/28/', headers=headers)
    
    if cart_response.status_code == 200:
        cart = cart_response.json()
        print(f"✅ Cart details:")
        print(f"   ID: {cart.get('id')}")
        print(f"   Status: {cart.get('status')}")
        print(f"   User: {cart.get('user')}")
        print(f"   Service Type: {cart.get('service_type')}")
        print(f"   Total Price: ₹{cart.get('total_price')}")
        print(f"   Puja Service: {cart.get('puja_service', {}).get('title')} (ID: {cart.get('puja_service', {}).get('id')})")
        
        package = cart.get('package')
        if package:
            print(f"   Package: ID={package.get('id')}, Price=₹{package.get('price')}")
        else:
            print(f"   Package: None")
            
        promo = cart.get('promo_code')
        if promo:
            print(f"   Promo: {promo.get('code')} ({promo.get('discount')}% off)")
        else:
            print(f"   Promo: None")
        
        # Check if this is the issue - cart amount validation
        if float(cart.get('total_price', 0)) <= 0:
            print(f"❌ ISSUE FOUND: Cart total is ₹{cart.get('total_price')} which is invalid for payment")
        else:
            print(f"✅ Cart total is valid: ₹{cart.get('total_price')}")
            
        print(f"\n📋 Full cart data:")
        print(json.dumps(cart, indent=2))
        
    else:
        print(f"❌ Failed to get cart: {cart_response.status_code} - {cart_response.text}")

if __name__ == "__main__":
    test_cart_details_production()
