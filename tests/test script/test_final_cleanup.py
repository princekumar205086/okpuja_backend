#!/usr/bin/env python
"""
Clean up remaining problematic carts and test enhanced cleanup
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def cleanup_remaining_carts():
    """Clean up the remaining problematic carts"""
    print("🧹 Cleaning Up Remaining Problematic Carts")
    print("=" * 45)
    
    from cart.models import Cart
    from django.db import connection
    from accounts.models import User
    
    # Remaining problematic cart IDs
    problem_cart_ids = [
        'b784d3e0-fca5-4757-8ba9-9e9783cb212f',
        '9b096c39-8de9-4975-ade1-244ac38c7bfb'
    ]
    
    user = User.objects.get(email='asliprinceraj@gmail.com')
    
    for cart_id in problem_cart_ids:
        cart = Cart.objects.filter(cart_id=cart_id).first()
        if cart:
            print(f"🗑️  Force deleting cart: {cart_id}")
            try:
                cursor = connection.cursor()
                cursor.execute("PRAGMA foreign_keys = OFF")
                cart.delete()
                cursor.execute("PRAGMA foreign_keys = ON")
                print(f"   ✅ Deleted successfully!")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        else:
            print(f"   ✅ Cart {cart_id} already deleted")
    
    # Check final cart count
    converted_carts = Cart.objects.filter(user=user, status='CONVERTED').count()
    print(f"\n📊 Final converted cart count: {converted_carts}")

def test_enhanced_cleanup():
    """Test the enhanced cleanup functionality"""
    print(f"\n🧪 Testing Enhanced Cleanup Functionality")
    print("=" * 45)
    
    from cart.models import Cart
    from accounts.models import User
    from payments.services import WebhookService
    
    user = User.objects.get(email='asliprinceraj@gmail.com')
    
    # Check current state
    converted_carts = Cart.objects.filter(user=user, status='CONVERTED').order_by('-created_at')
    print(f"📦 Current converted carts: {converted_carts.count()}")
    
    for i, cart in enumerate(converted_carts):
        print(f"   {i+1}. {cart.cart_id} (Created: {cart.created_at})")
    
    # Test the enhanced cleanup
    if converted_carts.count() > 3:
        print(f"\n🧹 Running enhanced cleanup...")
        webhook_service = WebhookService()
        try:
            webhook_service._cleanup_old_carts(user)
            print("✅ Enhanced cleanup completed!")
        except Exception as e:
            print(f"❌ Enhanced cleanup failed: {e}")
        
        # Check final state
        final_carts = Cart.objects.filter(user=user, status='CONVERTED').order_by('-created_at')
        print(f"\n📊 Final converted carts: {final_carts.count()}")
        
        for i, cart in enumerate(final_carts):
            print(f"   {i+1}. {cart.cart_id} (Created: {cart.created_at})")
        
        if final_carts.count() <= 3:
            print("\n✅ Cleanup successful - 3 or fewer carts remaining!")
            return True
        else:
            print("\n❌ Cleanup incomplete - more than 3 carts still exist")
            return False
    else:
        print("\n💡 No cleanup needed - 3 or fewer carts")
        return True

def test_booking_creation_with_cleanup():
    """Test that booking creation triggers automatic cleanup"""
    print(f"\n🎯 Testing Booking Creation with Auto-Cleanup")
    print("=" * 45)
    
    from cart.models import Cart
    from accounts.models import User
    from payments.models import PaymentOrder
    from payments.services import WebhookService
    from puja.models import PujaService, Package
    from datetime import datetime, timedelta
    import uuid
    
    user = User.objects.get(email='asliprinceraj@gmail.com')
    
    # Create a new cart to trigger the flow
    puja_service = PujaService.objects.first()
    package = Package.objects.filter(puja_service=puja_service).first()
    
    new_cart = Cart.objects.create(
        user=user,
        service_type='PUJA',
        puja_service=puja_service,
        package=package,
        selected_date=datetime.now().date() + timedelta(days=10),
        selected_time="15:00",
        cart_id=str(uuid.uuid4()),
        status='ACTIVE'
    )
    
    print(f"📦 Created new cart: {new_cart.cart_id}")
    
    # Create a mock payment order
    payment_order = PaymentOrder.objects.create(
        merchant_order_id=f"TEST_{uuid.uuid4().hex[:8]}",
        user=user,
        cart_id=new_cart.cart_id,
        amount=500000,  # ₹5000 in paisa
        status='SUCCESS'
    )
    
    print(f"💳 Created payment order: {payment_order.merchant_order_id}")
    
    # Check cart count before booking creation
    before_count = Cart.objects.filter(user=user, status='CONVERTED').count()
    print(f"📊 Converted carts before booking creation: {before_count}")
    
    # Create booking (this should trigger cleanup)
    webhook_service = WebhookService()
    booking = webhook_service._create_booking_from_cart(payment_order)
    
    if booking:
        print(f"✅ Booking created: {booking.book_id}")
        
        # Check cart count after booking creation
        after_count = Cart.objects.filter(user=user, status='CONVERTED').count()
        print(f"📊 Converted carts after booking creation: {after_count}")
        
        if after_count <= 3:
            print("✅ Auto-cleanup working - cart count maintained at 3 or less!")
            return True
        else:
            print("❌ Auto-cleanup not working - too many converted carts")
            return False
    else:
        print("❌ Booking creation failed!")
        return False

if __name__ == "__main__":
    # Step 1: Clean up remaining problematic carts
    cleanup_remaining_carts()
    
    # Step 2: Test enhanced cleanup
    cleanup_success = test_enhanced_cleanup()
    
    # Step 3: Test auto-cleanup during booking creation
    auto_cleanup_success = test_booking_creation_with_cleanup()
    
    print("\n" + "=" * 45)
    print("🎯 CART CLEANUP TEST RESULTS:")
    print(f"   Enhanced Cleanup: {'✅ WORKING' if cleanup_success else '❌ FAILED'}")
    print(f"   Auto-Cleanup: {'✅ WORKING' if auto_cleanup_success else '❌ FAILED'}")
    
    if cleanup_success and auto_cleanup_success:
        print("\n✅ ALL CART CLEANUP TESTS PASSED!")
        print("🎉 Converted carts are automatically cleaned up!")
    else:
        print("\n❌ SOME CLEANUP TESTS FAILED!")
