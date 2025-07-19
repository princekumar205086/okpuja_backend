#!/usr/bin/env python
"""
Demo script to show the enhanced cart deletion error messages
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
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from cart.models import Cart
from payment.models import Payment, PaymentStatus

User = get_user_model()

def demo_enhanced_error_messages():
    """Demonstrate the enhanced error messages for cart deletion"""
    print("=== Cart Deletion Error Message Demo ===\n")
    
    # Find a cart with pending payments
    test_cart = None
    for cart in Cart.objects.all():
        payments = Payment.objects.filter(cart=cart, status=PaymentStatus.PENDING)
        if payments.exists():
            test_cart = cart
            break
    
    if not test_cart:
        print("No cart with pending payments found for demo")
        # Create a test scenario
        user = User.objects.first()
        if user:
            test_cart = Cart.objects.filter(user=user).first()
            if test_cart:
                # Create a recent pending payment for demo
                Payment.objects.create(
                    cart=test_cart,
                    user=user,
                    transaction_id="DEMO123",
                    merchant_transaction_id="DEMO_MERCHANT_123",
                    amount=1000.00,
                    status=PaymentStatus.PENDING
                )
                print("Created demo pending payment for testing")
    
    if not test_cart:
        print("Could not create test scenario")
        return
    
    print(f"Testing with Cart: {test_cart.cart_id}")
    
    # Test 1: Get deletion status
    print("\n1. Testing deletion status endpoint:")
    deletion_info = test_cart.get_deletion_info()
    print(f"   Can delete: {deletion_info['can_delete']}")
    print(f"   Reason: {deletion_info['reason']}")
    
    if deletion_info['reason'] == 'pending_payment_wait':
        print(f"   Wait time: {deletion_info['wait_time_minutes']} minutes")
        print(f"   Message: {deletion_info['message']}")
        print(f"   Retry after: {deletion_info['retry_after']}")
    
    # Test 2: Simulate API deletion attempt
    print("\n2. Simulating DELETE request response:")
    
    # Mock the API response structure
    if not deletion_info["can_delete"] and deletion_info["reason"] == "pending_payment_wait":
        api_response = {
            'error': 'Cannot delete cart with recent pending payments',
            'detail': deletion_info["message"],
            'can_delete': False,
            'wait_time_minutes': deletion_info["wait_time_minutes"],
            'retry_after': deletion_info["retry_after"],
            'payment_count': deletion_info["payment_count"],
            'latest_payment_age_minutes': deletion_info["latest_payment_age_minutes"]
        }
        
        print("   HTTP 400 Bad Request")
        print("   Response body:")
        import json
        print(json.dumps(api_response, indent=4))
    
    # Test 3: Simulate old payment scenario
    print("\n3. Testing auto-cleanup scenario:")
    
    # Temporarily age a payment
    payments = Payment.objects.filter(cart=test_cart, status=PaymentStatus.PENDING)
    if payments.exists():
        test_payment = payments.first()
        original_time = test_payment.created_at
        
        # Make payment 35 minutes old
        old_time = timezone.now() - timedelta(minutes=35)
        Payment.objects.filter(id=test_payment.id).update(created_at=old_time)
        
        print(f"   Made payment {test_payment.transaction_id} appear 35 minutes old")
        
        # Test auto-cleanup
        cleanup_result = test_cart.auto_cleanup_old_payments()
        
        if cleanup_result['cleaned_up']:
            api_response = {
                'message': 'Cart deleted successfully',
                'deleted_cart_id': test_cart.cart_id,
                'auto_cleanup': cleanup_result
            }
            
            print("   Auto-cleanup triggered!")
            print("   HTTP 200 OK")
            print("   Response body:")
            print(json.dumps(api_response, indent=4))
        
        # Restore original time
        Payment.objects.filter(id=test_payment.id).update(created_at=original_time)
        print(f"   Restored original timestamp for {test_payment.transaction_id}")

def demo_user_friendly_messages():
    """Show different user-friendly message variations"""
    print("\n=== User-Friendly Message Variations ===\n")
    
    scenarios = [
        {
            "name": "Fresh payment (25 minutes old)",
            "age_minutes": 25,
            "wait_minutes": 5,
            "expected": "Cart has pending payment(s). Please wait 5 more minute(s) before deletion or complete the payment."
        },
        {
            "name": "Very fresh payment (2 minutes old)", 
            "age_minutes": 2,
            "wait_minutes": 28,
            "expected": "Cart has pending payment(s). Please wait 28 more minute(s) before deletion or complete the payment."
        },
        {
            "name": "Almost expired (29 minutes old)",
            "age_minutes": 29,
            "wait_minutes": 1,
            "expected": "Cart has pending payment(s). Please wait 1 more minute(s) before deletion or complete the payment."
        },
        {
            "name": "Just expired (31 minutes old)",
            "age_minutes": 31,
            "wait_minutes": 0,
            "expected": "Auto-cleanup triggered - cart can be deleted immediately"
        }
    ]
    
    for scenario in scenarios:
        print(f"{scenario['name']}:")
        print(f"   Payment age: {scenario['age_minutes']} minutes")
        print(f"   Wait time: {scenario['wait_minutes']} minutes")
        print(f"   Message: {scenario['expected']}")
        print()

if __name__ == "__main__":
    demo_enhanced_error_messages()
    demo_user_friendly_messages()
    print("Demo completed!")
