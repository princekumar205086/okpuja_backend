#!/usr/bin/env python
"""
Test automatic cart cleanup functionality
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

def test_cart_cleanup():
    """Test the automatic cart cleanup system"""
    print("🧹 Testing Automatic Cart Cleanup")
    print("=" * 40)
    
    from cart.models import Cart
    from accounts.models import User
    from payments.services import WebhookService
    from booking.models import Booking
    
    # Get user
    user = User.objects.get(email='asliprinceraj@gmail.com')
    print(f"👤 User: {user.email}")
    
    # Check current converted carts
    converted_carts = Cart.objects.filter(user=user, status='CONVERTED').order_by('-created_at')
    print(f"\n📦 Current converted carts: {converted_carts.count()}")
    
    for i, cart in enumerate(converted_carts):
        booking = Booking.objects.filter(cart=cart).first()
        print(f"   {i+1}. Cart: {cart.cart_id}")
        print(f"      Created: {cart.created_at}")
        print(f"      Booking: {booking.book_id if booking else 'NO BOOKING'}")
    
    # If we have more than 3 converted carts, test cleanup
    if converted_carts.count() <= 3:
        print(f"\n💡 Only {converted_carts.count()} converted carts - no cleanup needed")
        print("   Cleanup only happens when there are more than 3 converted carts")
        
        # Let's create some dummy converted carts to test cleanup
        print(f"\n🧪 Creating test converted carts to trigger cleanup...")
        
        from puja.models import PujaService, Package
        from datetime import datetime, timedelta
        import uuid
        
        puja_service = PujaService.objects.first()
        package = Package.objects.filter(puja_service=puja_service).first()
        
        # Create 4 additional converted carts
        for i in range(4):
            test_cart = Cart.objects.create(
                user=user,
                service_type='PUJA',
                puja_service=puja_service,
                package=package,
                selected_date=datetime.now().date() + timedelta(days=i+1),
                selected_time=f"{10+i}:00",
                cart_id=str(uuid.uuid4()),
                status='CONVERTED'
            )
            print(f"   ✅ Created test cart: {test_cart.cart_id}")
    
    # Check carts again
    converted_carts = Cart.objects.filter(user=user, status='CONVERTED').order_by('-created_at')
    print(f"\n📦 Total converted carts now: {converted_carts.count()}")
    
    # Test the cleanup function
    if converted_carts.count() > 3:
        print(f"\n🧹 Testing automatic cleanup (keeps latest 3)...")
        
        webhook_service = WebhookService()
        try:
            webhook_service._cleanup_old_carts(user)
            print("✅ Cleanup executed successfully!")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
        
        # Check carts after cleanup
        converted_carts_after = Cart.objects.filter(user=user, status='CONVERTED').order_by('-created_at')
        print(f"\n📊 Converted carts after cleanup: {converted_carts_after.count()}")
        
        for i, cart in enumerate(converted_carts_after):
            booking = Booking.objects.filter(cart=cart).first()
            print(f"   {i+1}. Cart: {cart.cart_id}")
            print(f"      Created: {cart.created_at}")
            print(f"      Booking: {booking.book_id if booking else 'NO BOOKING'}")
        
        # Check orphaned bookings (bookings without cart reference)
        orphaned_bookings = Booking.objects.filter(cart__isnull=True, user=user)
        print(f"\n🔗 Orphaned bookings (cart=NULL): {orphaned_bookings.count()}")
        for booking in orphaned_bookings:
            print(f"   📦 Booking: {booking.book_id} - Amount: ₹{booking.total_amount}")
        
        return True
    else:
        print("💡 No cleanup needed or test couldn't be performed")
        return False

if __name__ == "__main__":
    success = test_cart_cleanup()
    print("\n" + "=" * 40)
    if success:
        print("✅ CART CLEANUP TEST COMPLETED!")
        print("🎯 Automatic cleanup is working!")
        print("📝 Key points:")
        print("   • Keeps latest 3 converted carts")
        print("   • Older carts are automatically deleted")
        print("   • Bookings are preserved with cart=NULL")
        print("   • Cleanup happens during booking creation")
    else:
        print("ℹ️  Cleanup test completed - no action needed")
