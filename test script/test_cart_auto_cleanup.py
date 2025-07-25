#!/usr/bin/env python
"""
Test script for cart auto-cleanup functionality
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.utils import timezone
from cart.models import Cart
from payment.models import Payment, PaymentStatus
from accounts.models import User

def test_cart_auto_cleanup():
    print("Testing Cart Auto-Cleanup functionality...")
    
    # Find carts with pending payments
    carts_with_pending = []
    
    for cart in Cart.objects.all():
        payments = Payment.objects.filter(cart=cart, status=PaymentStatus.PENDING)
        if payments.exists():
            carts_with_pending.append((cart, payments))
    
    print(f"\nFound {len(carts_with_pending)} carts with pending payments")
    
    for cart, payments in carts_with_pending[:3]:  # Test first 3
        print(f"\n=== Testing Cart {cart.cart_id} ===")
        
        # Show current payment ages
        for payment in payments:
            age_minutes = int((timezone.now() - payment.created_at).total_seconds() / 60)
            print(f"  Payment {payment.transaction_id}: {age_minutes} minutes old")
        
        # Test deletion info
        deletion_info = cart.get_deletion_info()
        print(f"  Can delete: {deletion_info['can_delete']}")
        print(f"  Reason: {deletion_info['reason']}")
        
        if deletion_info['reason'] == 'pending_payment_wait':
            print(f"  Wait time: {deletion_info['wait_time_minutes']} minutes")
            print(f"  Message: {deletion_info['message']}")
        
        # Test auto-cleanup
        cleanup_result = cart.auto_cleanup_old_payments()
        if cleanup_result['cleaned_up']:
            print(f"  ✓ Auto-cleanup: {cleanup_result['message']}")
        else:
            print(f"  - No cleanup needed")
        
        # Check deletion status after cleanup
        updated_deletion_info = cart.get_deletion_info()
        print(f"  After cleanup - Can delete: {updated_deletion_info['can_delete']}")

def simulate_old_payment():
    """Create a test scenario with an old pending payment"""
    print("\n=== Creating Test Scenario ===")
    
    # Find a cart to use for testing
    test_cart = Cart.objects.filter(status='ACTIVE').first()
    if not test_cart:
        print("No active cart found for testing")
        return
    
    # Simulate creating an old payment by temporarily modifying a payment's timestamp
    test_payment = Payment.objects.filter(cart=test_cart, status=PaymentStatus.PENDING).first()
    if test_payment:
        original_time = test_payment.created_at
        
        # Make payment appear 35 minutes old
        old_time = timezone.now() - timedelta(minutes=35)
        Payment.objects.filter(id=test_payment.id).update(created_at=old_time)
        
        print(f"Made payment {test_payment.transaction_id} appear 35 minutes old")
        
        # Test the cleanup
        deletion_info = test_cart.get_deletion_info()
        print(f"Can delete now: {deletion_info['can_delete']}")
        print(f"Reason: {deletion_info['reason']}")
        
        cleanup_result = test_cart.auto_cleanup_old_payments()
        if cleanup_result['cleaned_up']:
            print(f"✓ Cleanup successful: {cleanup_result['message']}")
        
        # Restore original timestamp for safety
        Payment.objects.filter(id=test_payment.id).update(created_at=original_time)
        print("Restored original payment timestamp")

def test_error_messages():
    """Test different error message scenarios"""
    print("\n=== Testing Error Messages ===")
    
    # Find cart with recent pending payment
    recent_cart = None
    for cart in Cart.objects.all():
        payments = Payment.objects.filter(cart=cart, status=PaymentStatus.PENDING)
        if payments.exists():
            newest_payment = payments.order_by('-created_at').first()
            age_minutes = int((timezone.now() - newest_payment.created_at).total_seconds() / 60)
            if age_minutes < 30:
                recent_cart = cart
                break
    
    if recent_cart:
        deletion_info = recent_cart.get_deletion_info()
        print(f"Cart {recent_cart.cart_id}:")
        print(f"  Message: {deletion_info.get('message', 'N/A')}")
        print(f"  Wait time: {deletion_info.get('wait_time_minutes', 'N/A')} minutes")
        print(f"  Payment age: {deletion_info.get('latest_payment_age_minutes', 'N/A')} minutes")
    else:
        print("No cart with recent pending payments found")

if __name__ == "__main__":
    test_cart_auto_cleanup()
    simulate_old_payment()
    test_error_messages()
    print("\nTesting completed!")
