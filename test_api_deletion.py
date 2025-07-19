#!/usr/bin/env python
"""
Test the cart deletion API endpoint
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from cart.models import Cart
from payment.models import Payment

User = get_user_model()

def test_cart_deletion_api():
    print("Testing Cart Deletion API...")
    
    # Get a test user
    user = User.objects.first()
    if not user:
        print("No users found for testing")
        return
    
    client = Client()
    
    # Test getting carts (should work without auth for this test)
    print(f"\n1. Testing with user: {user.email}")
    
    # Get carts for user
    user_carts = Cart.objects.filter(user=user)
    print(f"   User has {user_carts.count()} carts")
    
    for cart in user_carts:
        payments = Payment.objects.filter(cart=cart)
        print(f"   Cart {cart.cart_id}: Status={cart.status}, Payments={payments.count()}, Can delete={cart.can_be_deleted()}")
        
        # Test deletion status endpoint
        if user_carts.count() > 0:
            test_cart = user_carts.first()
            print(f"\n2. Testing deletion status for cart {test_cart.cart_id}")
            
            from cart.views import CartViewSet
            from rest_framework.test import APIRequestFactory
            from rest_framework.request import Request
            
            factory = APIRequestFactory()
            request = factory.get('/api/cart/carts/{}/deletion_status/'.format(test_cart.id))
            request.user = user
            
            view = CartViewSet()
            view.request = Request(request)
            view.kwargs = {'pk': test_cart.id}
            
            try:
                response = view.deletion_status(Request(request), pk=test_cart.id)
                print(f"   Deletion status response: {response.data}")
            except Exception as e:
                print(f"   Error getting deletion status: {e}")
    
    print("\nAPI test completed!")

if __name__ == "__main__":
    test_cart_deletion_api()
