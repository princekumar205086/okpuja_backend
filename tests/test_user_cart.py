#!/usr/bin/env python3
"""
Simple test script to check user authentication and cart status
"""

import sys
import os
import django

# Add the project directory to the Python path
sys.path.append(r'C:\Users\Prince Raj\Desktop\nextjs project\okpuja_backend')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

# Setup Django
django.setup()

def test_user_and_cart():
    """Test user authentication and cart status"""
    from django.contrib.auth import get_user_model
    from cart.models import Cart
    from payment.models import Payment
    
    User = get_user_model()
    
    # Find the test user
    try:
        user = User.objects.get(email="asliprinceraj@gmail.com")
        print(f"✅ User found: {user.email} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ User not found with email: asliprinceraj@gmail.com")
        return False
    
    # Check cart with ID 19
    try:
        cart = Cart.objects.get(id=19)
        print(f"✅ Cart found: ID={cart.id}, User={cart.user.email}, Status={cart.status}")
        print(f"   Total Price: ₹{cart.total_price}")
        print(f"   Selected Date: {cart.selected_date}")
        print(f"   Selected Time: {cart.selected_time}")
        
        if cart.user != user:
            print(f"⚠️ Cart belongs to different user: {cart.user.email}")
            return False
            
        if cart.status != 'ACTIVE':
            print(f"⚠️ Cart is not active: {cart.status}")
            return False
            
    except Cart.DoesNotExist:
        print("❌ Cart not found with ID: 19")
        return False
    
    # Check for existing payments for this cart
    payments = Payment.objects.filter(cart=cart)
    if payments.exists():
        print(f"📋 Found {payments.count()} existing payment(s) for cart:")
        for payment in payments:
            print(f"   Payment ID: {payment.id}, Status: {payment.status}, Amount: ₹{payment.amount}")
    else:
        print("📋 No existing payments found for this cart")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing User Authentication and Cart Status")
    print("=" * 50)
    
    try:
        success = test_user_and_cart()
        if success:
            print("\n✅ All checks passed! Ready for payment processing.")
        else:
            print("\n❌ Some checks failed. Please resolve issues before proceeding.")
    except Exception as e:
        print(f"\n💥 Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
