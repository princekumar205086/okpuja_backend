#!/usr/bin/env python
"""
Final verification script to test admin-like booking deletion
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking, BookingStatus
from django.contrib.auth import get_user_model
from accounts.models import Address
from datetime import date, time, timedelta

User = get_user_model()

def create_test_bookings():
    """Create some test bookings for admin deletion testing"""
    print("Creating test bookings for admin deletion testing...")
    
    # Use the specified test user
    try:
        test_user = User.objects.get(email="asliprinceraj@gmail.com")
        test_address = Address.objects.get(id=1)
    except (User.DoesNotExist, Address.DoesNotExist) as e:
        print(f"Error: {e}")
        return []
    
    bookings = []
    for i in range(5):
        booking = Booking.objects.create(
            user=test_user,
            selected_date=date.today() + timedelta(days=i+1),
            selected_time=time(9 + i, 0),  # 9:00, 10:00, 11:00, 12:00, 13:00
            address=test_address,
            status=BookingStatus.PENDING,
        )
        bookings.append(booking)
        print(f"✅ Created booking: {booking.book_id}")
    
    return bookings

def test_admin_style_deletion():
    """Test deletion exactly like Django admin does it"""
    print("\n" + "="*60)
    print("Testing Admin-Style Deletion")
    print("="*60)
    
    # Create test bookings
    bookings = create_test_bookings()
    if not bookings:
        print("❌ Failed to create test bookings")
        return False
    
    print(f"\nCreated {len(bookings)} test bookings")
    
    # Test individual deletion (admin change view delete)
    print("\n1. Testing individual booking deletion...")
    single_booking = bookings[0]
    try:
        booking_id = single_booking.book_id
        single_booking.delete()
        print(f"✅ Successfully deleted individual booking {booking_id}")
    except Exception as e:
        print(f"❌ Error deleting individual booking: {e}")
        return False
    
    # Test bulk deletion (admin changelist action)
    print("\n2. Testing bulk deletion (admin action)...")
    remaining_bookings = bookings[1:]  # Skip the already deleted one
    try:
        booking_ids = [b.book_id for b in remaining_bookings]
        # This mimics what Django admin does when you select multiple items and delete
        queryset = Booking.objects.filter(book_id__in=booking_ids)
        count = queryset.count()
        queryset.delete()
        print(f"✅ Successfully bulk deleted {count} bookings: {booking_ids}")
    except Exception as e:
        print(f"❌ Error in bulk deletion: {e}")
        return False
    
    print("\n🎉 All admin-style deletion tests passed!")
    print("The admin interface should now work without foreign key constraint errors.")
    return True

def show_current_bookings():
    """Show current bookings in the system"""
    print("\n" + "="*60)
    print("Current Bookings in System")
    print("="*60)
    
    bookings = Booking.objects.all().order_by('-created_at')
    if bookings:
        for booking in bookings:
            print(f"- {booking.book_id} | {booking.user.email} | {booking.status} | {booking.created_at}")
    else:
        print("No bookings found in the system.")

if __name__ == "__main__":
    print("🔧 Admin Deletion Verification Test")
    print("This script tests if the booking admin deletion works properly")
    
    # Show current state
    show_current_bookings()
    
    # Run deletion tests
    success = test_admin_style_deletion()
    
    # Show final state
    show_current_bookings()
    
    print("\n" + "="*60)
    if success:
        print("✅ RESULT: Admin deletion is working properly!")
        print("You can now safely delete bookings in the Django admin interface.")
    else:
        print("❌ RESULT: There are still issues with admin deletion.")
        print("Please check the error messages above.")
    print("="*60)
