#!/usr/bin/env python
"""
Test script for new cart deletion flow
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from payment.models import Payment, PaymentStatus
from accounts.models import User

def test_cart_deletion():
    print("Testing cart deletion functionality...")
    
    # Test 1: Check if cart with pending payments can be deleted
    print("\n1. Testing carts with pending payments:")
    carts_with_pending = []
    
    for cart in Cart.objects.all():
        payments = Payment.objects.filter(cart=cart)
        pending_payments = payments.filter(status=PaymentStatus.PENDING)
        
        if pending_payments.exists():
            carts_with_pending.append(cart)
            print(f"   Cart {cart.cart_id}: {pending_payments.count()} pending payments - Can delete: {cart.can_be_deleted()}")
    
    # Test 2: Check converted carts
    print("\n2. Testing converted carts:")
    converted_carts = Cart.objects.filter(status='CONVERTED')
    
    for cart in converted_carts:
        payments = Payment.objects.filter(cart=cart)
        successful_payments = payments.filter(status=PaymentStatus.SUCCESS)
        print(f"   Cart {cart.cart_id}: Status={cart.status}, Success payments={successful_payments.count()}, Can delete: {cart.can_be_deleted()}")
    
    # Test 3: Try deleting a safe cart
    print("\n3. Testing safe cart deletion:")
    safe_carts = [cart for cart in Cart.objects.all() if cart.can_be_deleted()]
    
    if safe_carts:
        test_cart = safe_carts[0]
        print(f"   Found safe cart to delete: {test_cart.cart_id}")
        print(f"   Payments before deletion: {Payment.objects.filter(cart=test_cart).count()}")
        
        # Show what would happen (don't actually delete in test)
        if test_cart.status == Cart.StatusChoices.CONVERTED:
            print("   Would clear payment references and delete cart")
        else:
            print("   Would delete cart directly")
    else:
        print("   No safe carts found for deletion test")
    
    # Test 4: Single cart logic
    print("\n4. Testing single cart logic:")
    users_with_multiple_active = []
    
    for user in User.objects.all():
        active_carts = Cart.objects.filter(user=user, status='ACTIVE')
        if active_carts.count() > 1:
            users_with_multiple_active.append(user)
            print(f"   User {user.email}: {active_carts.count()} active carts (should be max 1)")
    
    if not users_with_multiple_active:
        print("   All users have at most 1 active cart ✓")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_cart_deletion()
