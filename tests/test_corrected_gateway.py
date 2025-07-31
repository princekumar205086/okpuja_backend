#!/usr/bin/env python3
"""
Simple test for the corrected PhonePe V2 implementation
"""

import sys
import os
import django
import json

# Add the project directory to the Python path
sys.path.append(r'C:\Users\Prince Raj\Desktop\nextjs project\okpuja_backend')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

# Setup Django
django.setup()

def test_phonepe_gateway():
    """Test the corrected PhonePe V2 gateway initialization"""
    try:
        from payment.gateways_v2_corrected import get_payment_gateway_v2_corrected
        
        print("🧪 Testing PhonePe V2 Corrected Gateway")
        print("=" * 50)
        
        # Initialize gateway
        gateway = get_payment_gateway_v2_corrected('phonepe')
        print(f"✅ Gateway initialized successfully")
        print(f"   Merchant ID: {gateway.merchant_id}")
        print(f"   Base URL: {gateway.base_url}")
        print(f"   Timeout: {gateway.timeout}s")
        print(f"   Max Retries: {gateway.max_retries}")
        print(f"   SSL Verify: {gateway.ssl_verify}")
        print(f"   Production: {gateway.is_production}")
        
        # Test merchant transaction ID generation
        transaction_id = gateway.generate_merchant_transaction_id()
        print(f"   Generated Transaction ID: {transaction_id}")
        
        # Test checksum generation
        test_payload = '{"test": "data"}'
        test_endpoint = "/pg/v1/pay"
        checksum = gateway.generate_checksum(test_payload, test_endpoint)
        print(f"   Generated Checksum: {checksum[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Gateway test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_user_and_cart():
    """Test user and cart data"""
    try:
        from django.contrib.auth import get_user_model
        from cart.models import Cart
        
        User = get_user_model()
        
        print("\n🔍 Testing User and Cart Data")
        print("=" * 50)
        
        # Find user
        user = User.objects.filter(email="asliprinceraj@gmail.com").first()
        if user:
            print(f"✅ User found: {user.email} (ID: {user.id})")
        else:
            print("❌ User not found")
            return False
        
        # Find cart
        cart = Cart.objects.filter(id=19).first()
        if cart:
            print(f"✅ Cart found: ID={cart.id}")
            print(f"   Owner: {cart.user.email}")
            print(f"   Status: {cart.status}")
            print(f"   Total Price: ₹{cart.total_price}")
            print(f"   Selected Date: {cart.selected_date}")
            print(f"   Selected Time: {cart.selected_time}")
            
            if cart.user != user:
                print(f"⚠️ Cart belongs to different user: {cart.user.email}")
                return False
                
            if cart.status != 'ACTIVE':
                print(f"⚠️ Cart is not active: {cart.status}")
                return False
        else:
            print("❌ Cart not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ User/Cart test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 PhonePe V2 Corrected Implementation Test")
    print("📅 " + str(datetime.now() if 'datetime' in globals() else 'Test Date'))
    print()
    
    # Test 1: Gateway initialization
    gateway_ok = test_phonepe_gateway()
    
    # Test 2: User and cart data
    data_ok = test_user_and_cart()
    
    print("\n" + "=" * 50)
    
    if gateway_ok and data_ok:
        print("✅ All tests passed! Ready for payment processing.")
        print("\n📋 Next Steps:")
        print("1. Use the corrected gateway in your payment requests")
        print("2. Test with the actual API endpoint")
        print("3. Check PhonePe webhook integration")
    else:
        print("❌ Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    from datetime import datetime
    main()
