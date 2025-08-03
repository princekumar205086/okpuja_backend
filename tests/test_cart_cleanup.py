#!/usr/bin/env python3
"""
Cart Cleanup Test Suite

Tests the cart cleanup functionality after successful booking creation
"""

import requests
import time
from datetime import datetime, date, time as dt_time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from cart.models import Cart, CartItem
from booking.models import Booking
from payments.models import PaymentOrder
from puja.models import Puja


class CartCleanupTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test puja
        self.puja = Puja.objects.create(
            name='Test Puja',
            price=500.00,
            is_active=True
        )
        
        # Create test cart
        self.cart = Cart.objects.create(
            user=self.user,
            selected_date=date.today(),
            selected_time=dt_time(10, 0),
            is_active=True
        )
        
        # Add items to cart
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            puja=self.puja,
            quantity=1
        )
        
        # Create test payment
        self.payment = PaymentOrder.objects.create(
            cart=self.cart,
            user=self.user,
            amount=500.00,
            payment_id='TEST_PAYMENT_123',
            merchant_transaction_id='TEST_TXN_123',
            status='INITIATED'
        )
    
    def test_cart_cleanup_after_successful_booking(self):
        """Test that cart is cleaned after successful booking"""
        # Verify initial state
        self.assertTrue(self.cart.is_active)
        self.assertEqual(self.cart.cartitem_set.count(), 1)
        
        # Simulate hyper-speed booking creation process
        from payments.hyper_speed_redirect_handler import HyperSpeedPaymentRedirectHandler
        
        handler = HyperSpeedPaymentRedirectHandler()
        
        # Simulate successful booking creation
        booking = handler._create_booking_instantly(self.cart, self.payment)
        
        # Verify booking was created
        self.assertIsNotNone(booking)
        self.assertEqual(booking.cart, self.cart)
        self.assertEqual(booking.status, 'CONFIRMED')
        
        # Verify cart was cleaned
        self.cart.refresh_from_db()
        self.assertFalse(self.cart.is_active)
        self.assertEqual(self.cart.cartitem_set.count(), 0)
        
        # Verify payment status was updated
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'SUCCESS')
    
    def test_cart_cleanup_doesnt_fail_booking(self):
        """Test that cart cleanup errors don't prevent booking creation"""
        # Create invalid cart scenario
        invalid_cart = Cart.objects.create(
            user=self.user,
            selected_date=date.today(),
            selected_time=dt_time(10, 0),
            is_active=True
        )
        
        # Delete the cart to simulate cleanup error
        cart_id = invalid_cart.id
        invalid_cart.delete()
        
        # Try to clean non-existent cart
        from payments.hyper_speed_redirect_handler import HyperSpeedPaymentRedirectHandler
        
        handler = HyperSpeedPaymentRedirectHandler()
        
        # This should not raise an exception
        try:
            handler._clean_cart_after_booking(invalid_cart)
            # If we reach here, cleanup handled the error gracefully
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Cart cleanup should not fail booking: {e}")


class CartCleanupIntegrationTest:
    """Integration test for cart cleanup in production-like scenario"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    def test_complete_payment_flow_with_cleanup(self):
        """Test complete payment flow including cart cleanup"""
        print("🧪 Testing complete payment flow with cart cleanup...")
        
        # This would simulate:
        # 1. User creates cart
        # 2. User initiates payment
        # 3. Payment completes via hyper-speed handler
        # 4. Cart gets cleaned automatically
        
        # Note: This requires running Django server
        print("✅ Integration test placeholder - implement with live server")


def run_cart_cleanup_tests():
    """Run all cart cleanup tests"""
    print("🧹 CART CLEANUP TEST SUITE")
    print("=" * 50)
    
    print("\n1. Testing cart cleanup functionality...")
    
    # Run Django tests
    import subprocess
    import os
    
    try:
        os.chdir('/c/Users/Prince Raj/Desktop/nextjs project/okpuja_backend')
        result = subprocess.run([
            'python', 'manage.py', 'test', 'tests.test_cart_cleanup', '-v', '2'
        ], capture_output=True, text=True)
        
        print("Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Test execution error: {e}")
    
    print("\n2. Integration test summary:")
    integration_test = CartCleanupIntegrationTest()
    integration_test.test_complete_payment_flow_with_cleanup()
    
    print("\n✅ Cart cleanup tests completed!")


if __name__ == "__main__":
    run_cart_cleanup_tests()
