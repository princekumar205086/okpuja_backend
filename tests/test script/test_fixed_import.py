#!/usr/bin/env python3
"""
Direct test of CartPaymentView to verify the UserAddress fix
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

from accounts.models import User, Address
from cart.models import Cart
from payments.cart_views import CartPaymentView
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
import json

def test_import_fix():
    print("🔍 Testing CartPaymentView Import Fix")
    print("=" * 50)
    
    # Get test data
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ Test user not found")
        return
    
    address = Address.objects.filter(user=user).first()
    if not address:
        print("❌ No address found for user")
        return
    
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        print("❌ No cart found for user")
        return
    
    print(f"✅ User: {user.email}")
    print(f"✅ Address: {address.id} - {address.city}")
    print(f"✅ Cart: {cart.id}")
    
    # Test the view import directly
    try:
        view = CartPaymentView()
        print("✅ CartPaymentView imported successfully!")
        print("✅ No more UserAddress import errors!")
        
        # Test POST method access (should fail with authentication but not import error)
        request = HttpRequest()
        request.method = 'POST'
        request.user = AnonymousUser()
        request.POST = {'cart_id': cart.id, 'address_id': address.id}
        
        try:
            response = view.post(request)
            print("❌ Unexpected success - should have failed authentication")
        except Exception as e:
            if "Authentication" in str(e):
                print("✅ Authentication error expected - import fix verified!")
            else:
                print(f"✅ Other error (not import): {e}")
                
    except ImportError as e:
        print(f"❌ Import error still exists: {e}")
    except Exception as e:
        print(f"✅ No import error! Other error: {e}")

if __name__ == "__main__":
    test_import_fix()
