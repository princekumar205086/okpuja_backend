#!/usr/bin/env python3
"""
Quick Cart Cleanup Verification Script
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from payments.hyper_speed_redirect_handler import HyperSpeedPaymentRedirectHandler

def test_cart_cleanup():
    """Quick test of cart cleanup functionality"""
    print("🧹 Testing Cart Cleanup Functionality")
    print("=" * 50)
    
    # Check if we have any active carts
    carts = Cart.objects.filter(status=Cart.StatusChoices.ACTIVE)[:5]
    
    if not carts.exists():
        print("❌ No active carts found for testing")
        print("💡 Creating a test cart...")
        
        # Create a simple test cart if none exist
        from django.contrib.auth.models import User
        from puja.models import PujaService
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        
        # Get or create a test puja service
        puja_service = PujaService.objects.first()
        if not puja_service:
            print("❌ No puja services found. Please create some test data first.")
            return
        
        # Create test cart
        test_cart = Cart.objects.create(
            user=user,
            puja_service=puja_service,
            selected_date='2024-12-25',
            selected_time='10:00',
            cart_id='TEST_CART_123',
            status=Cart.StatusChoices.ACTIVE
        )
        carts = [test_cart]
        print(f"✅ Created test cart: {test_cart.cart_id}")
    
    handler = HyperSpeedPaymentRedirectHandler()
    
    for cart in carts:
        print(f"\n📦 Testing cart {cart.cart_id}:")
        print(f"   - Status: {cart.status}")
        print(f"   - Service: {cart.service}")
        
        # Test cleanup method
        try:
            handler._clean_cart_after_booking(cart)
            cart.refresh_from_db()
            
            print(f"   ✅ Cleanup successful!")
            print(f"   - Status after cleanup: {cart.status}")
            
        except Exception as e:
            print(f"   ❌ Cleanup error: {e}")
    
    print("\n✅ Cart cleanup test completed!")

if __name__ == "__main__":
    test_cart_cleanup()
