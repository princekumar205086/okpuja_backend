#!/usr/bin/env python
"""
Production Payment Test with Active Cart
Use existing active cart to test payment initiation
"""
import requests
import json

# Production API Configuration
PRODUCTION_BASE_URL = 'https://backend.okpuja.com/api'

# Test User Credentials
TEST_EMAIL = 'asliprinceraj@gmail.com'
TEST_PASSWORD = 'testpass123'

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

def get_active_cart(token):
    """Get the active cart for the user"""
    print("2. Getting active cart...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f'{PRODUCTION_BASE_URL}/cart/carts/active/', headers=headers)
    
    print(f"Active Cart Response Status: {response.status_code}")
    
    if response.status_code == 200:
        carts = response.json()
        print(f"Found {len(carts)} active carts")
        
        # Find cart with package and positive total
        best_cart = None
        for cart in carts:
            package = cart.get('package')
            total = float(cart.get('total_price', '0.00'))
            
            print(f"Cart {cart['id']}: Total=₹{total}, Package={bool(package)}")
            
            if package and total > 0:
                best_cart = cart
                break
        
        # If no cart with package found, use first cart with positive total
        if not best_cart:
            for cart in carts:
                total = float(cart.get('total_price', '0.00'))
                if total > 0:
                    best_cart = cart
                    break
        
        # If still no cart, use first one
        if not best_cart and carts:
            best_cart = carts[0]
        
        if not best_cart:
            print("❌ No carts found")
            return None, 0
            
        cart = best_cart
        print(f"✅ Using cart {cart['id']}!")
        print(f"   Service: {cart.get('puja_service', {}).get('title', 'Unknown')}")
        
        package = cart.get('package')
        if package:
            print(f"   Package: {package.get('id')} - ₹{package.get('price', '0')}")
        else:
            print(f"   Package: None")
        
        promo = cart.get('promo_code')
        if promo:
            print(f"   Promo: {promo.get('code')} ({promo.get('discount')}% off)")
        
        total = cart.get('total_price', '0.00')
        print(f"   Total: ₹{total}")
        
        if float(total) > 0:
            print(f"🎉 Cart has valid amount: ₹{total}")
            return cart['id'], float(total)
        else:
            print(f"❌ Cart total is ₹0")
            return None, 0
    else:
        print(f"❌ Failed to get active cart: {response.status_code}")
        return None, 0

def initiate_payment_with_active_cart(token, cart_id, amount):
    """Initiate payment using the active cart"""
    print(f"3. Initiating payment for active cart {cart_id} (₹{amount})...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    payment_data = {
        'cart_id': cart_id,
        'address_id': 2,  # Using address ID 2 as suggested
        'method': 'PHONEPE'
    }
    
    print(f"Payment Request Data: {json.dumps(payment_data, indent=2)}")
    
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
            print(f"\n🔗 COMPLETE PAYMENT:")
            print(f"   Open this URL in browser: {payment_url}")
            print(f"   Complete the payment to trigger booking creation")
        
        return payment
    elif response.status_code == 400:
        print(f"❌ PAYMENT INITIATION FAILED - 400 Bad Request")
        try:
            error_data = response.json()
            error_msg = error_data.get('error', 'Unknown error')
            error_details = error_data.get('details', 'No details')
            
            print(f"   Error: {error_msg}")
            print(f"   Details: {error_details}")
            
            # Analyze the error
            if 'min_value' in error_details:
                print(f"\n🔍 ANALYSIS: Amount validation failed")
                print(f"   This means the cart total is being calculated as ₹0 during payment processing")
                print(f"   Even though the cart shows ₹{amount}, something is wrong with the amount calculation")
            elif 'Payment initiation failed' in error_details:
                print(f"\n🔍 ANALYSIS: PhonePe gateway error")
                print(f"   The amount is valid but PhonePe API is failing")
                print(f"   Check PhonePe credentials and API configuration")
            elif 'address_id' in error_details:
                print(f"\n🔍 ANALYSIS: Address validation failed")
                print(f"   User might not have address ID 1 or address is invalid")
            
        except Exception as e:
            print(f"   Could not parse error response: {e}")
            print(f"   Raw response: {response.text}")
        
        return None
    else:
        print(f"❌ PAYMENT INITIATION FAILED - {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def check_user_addresses(token):
    """Check what addresses the user has"""
    print("🏠 Using address ID 2 (as suggested)...")
    return 2  # User mentioned we can use address ID 2

def main():
    """Run production payment test with active cart"""
    print("🧪 PRODUCTION PAYMENT TEST - Using Active Cart")
    print("=" * 60)
    print(f"API: {PRODUCTION_BASE_URL}")
    print(f"User: {TEST_EMAIL}")
    print("=" * 60)
    
    # Step 1: Get access token
    token = get_access_token()
    if not token:
        return
    
    # Step 2: Get active cart
    cart_id, amount = get_active_cart(token)
    if not cart_id:
        print("\n❌ FAILED: No active cart found or cart has ₹0 total")
        return
    
    # Step 3: Check user addresses
    address_id = check_user_addresses(token)
    if not address_id:
        print("\n❌ FAILED: User has no addresses")
        print("   Create an address first or use a different address_id")
        return
    
    print(f"\n✅ Using address ID: {address_id}")
    
    # Step 4: Initiate payment with correct address
    payment_data = {
        'cart_id': cart_id,
        'address_id': address_id,  # Use actual address ID
        'method': 'PHONEPE'
    }
    
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"4. Final payment attempt with address {address_id}...")
    response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/process-cart/', 
                           json=payment_data, 
                           headers=headers)
    
    print(f"Final Payment Status: {response.status_code}")
    print(f"Final Payment Response: {response.text}")
    
    if response.status_code == 201:
        payment = response.json()
        print(f"\n🎉 SUCCESS: Production payment flow is working!")
        print(f"✅ Active cart: Found (₹{amount})")
        print(f"✅ Address: Valid ({address_id})")
        print(f"✅ Payment initiation: Successful")
        print(f"✅ PhonePe integration: Working")
        
        payment_url = payment.get('payment_url')
        if payment_url:
            print(f"\n🔗 NEXT STEP:")
            print(f"   1. Open: {payment_url}")
            print(f"   2. Complete payment")
            print(f"   3. Webhook will create booking automatically")
    else:
        print(f"\n❌ STILL FAILING: {response.status_code}")
        print(f"   This needs investigation of the payment processing logic")

if __name__ == "__main__":
    main()
