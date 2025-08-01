#!/usr/bin/env python
"""
Test script to check if booking admin deletion works properly
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from django.contrib.auth import get_user_model

User = get_user_model()

def test_booking_creation_and_deletion():
    """Test booking creation and deletion to verify FK constraints are working"""
    print("Testing booking creation and deletion...")
    
    # Use the specified test user
    try:
        test_user = User.objects.get(email="asliprinceraj@gmail.com")
        print(f"Using test user: {test_user}")
    except User.DoesNotExist:
        print("Test user asliprinceraj@gmail.com not found, please create it first")
        return False
    
    # Use address ID 1
    from datetime import date, time
    from booking.models import BookingStatus
    from accounts.models import Address
    
    try:
        test_address = Address.objects.get(id=1)
        print(f"Using address ID 1: {test_address}")
    except Address.DoesNotExist:
        print("Address ID 1 not found, please check if it exists")
        return False
    
    test_booking = Booking.objects.create(
        user=test_user,
        selected_date=date.today(),
        selected_time=time(10, 0),  # 10:00 AM
        address=test_address,
        status=BookingStatus.PENDING,  # Use the proper enum value
    )
    print(f"Created test booking: {test_booking.book_id}")
    
    # Try to delete the booking (this should work without FK constraints)
    try:
        booking_id = test_booking.book_id
        test_booking.delete()
        print(f"✅ Successfully deleted booking {booking_id}")
        print("Foreign key constraints are working properly!")
        return True
    except Exception as e:
        print(f"❌ Error deleting booking: {e}")
        return False

def test_bulk_deletion():
    """Test bulk deletion like admin does"""
    print("\nTesting bulk deletion (like admin interface)...")
    
    # Use the specified test user
    try:
        test_user = User.objects.get(email="asliprinceraj@gmail.com")
        print(f"Using test user: {test_user}")
    except User.DoesNotExist:
        print("Test user asliprinceraj@gmail.com not found, please create it first")
        return False
    
    # Use address ID 1
    from datetime import date, time, timedelta
    from booking.models import BookingStatus
    from accounts.models import Address
    
    try:
        test_address = Address.objects.get(id=1)
        print(f"Using address ID 1: {test_address}")
    except Address.DoesNotExist:
        print("Address ID 1 not found, please check if it exists")
        return False
    
    bookings = []
    for i in range(3):
        booking = Booking.objects.create(
            user=test_user,
            selected_date=date.today() + timedelta(days=i+1),
            selected_time=time(10 + i, 0),  # 10:00, 11:00, 12:00
            address=test_address,
            status=BookingStatus.PENDING,
        )
        bookings.append(booking)
        print(f"Created booking: {booking.book_id}")
    
    # Try bulk deletion (like admin interface does)
    try:
        booking_ids = [b.book_id for b in bookings]
        queryset = Booking.objects.filter(book_id__in=booking_ids)
        count = queryset.count()
        queryset.delete()  # This is what admin does
        print(f"✅ Successfully bulk deleted {count} bookings")
        print("Bulk deletion works properly!")
        return True
    except Exception as e:
        print(f"❌ Error in bulk deletion: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Booking Admin Functionality")
    print("=" * 50)
    
    single_test = test_booking_creation_and_deletion()
    bulk_test = test_bulk_deletion()
    
    print("\n" + "=" * 50)
    if single_test and bulk_test:
        print("🎉 All tests passed! Admin deletion should work now.")
    else:
        print("⚠️  Some tests failed. There might still be FK constraint issues.")
