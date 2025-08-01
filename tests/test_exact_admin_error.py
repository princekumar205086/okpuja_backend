#!/usr/bin/env python
"""
Test exact admin interface deletion scenario
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from booking.admin import BookingAdmin
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.admin.actions import delete_selected
from django.db import transaction

User = get_user_model()

def simulate_exact_admin_deletion():
    """Simulate the exact admin deletion process that's causing the error"""
    print("🎭 EXACT ADMIN DELETION SIMULATION")
    print("=" * 60)
    
    # Create admin instance
    admin_site = AdminSite()
    booking_admin = BookingAdmin(Booking, admin_site)
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.post('/admin/booking/booking/')
    
    # Set up a superuser for the request
    superuser = User.objects.filter(is_superuser=True).first()
    if not superuser:
        print("❌ No superuser found. Please create a superuser first.")
        return
    
    request.user = superuser
    
    # Get all bookings
    all_bookings = Booking.objects.all()
    print(f"Found {all_bookings.count()} bookings")
    
    # Test admin deletion for each booking individually
    for booking in all_bookings:
        print(f"\n📋 Testing admin deletion for: {booking.book_id}")
        
        # Create a queryset with just this booking
        queryset = Booking.objects.filter(id=booking.id)
        
        try:
            # This is exactly what admin does when you select "Delete selected items"
            with transaction.atomic():
                sid = transaction.savepoint()
                
                # Call the admin's delete_queryset method (used by delete_selected action)
                booking_admin.delete_queryset(request, queryset)
                
                # Rollback since this is a test
                transaction.savepoint_rollback(sid)
                
                print(f"   ✅ Admin deletion successful")
                
        except Exception as e:
            print(f"   ❌ Admin deletion failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # This is the problematic booking!
            return booking.book_id, str(e)
    
    # Test bulk deletion with all bookings
    print(f"\n🗂️ Testing bulk deletion with ALL bookings")
    try:
        with transaction.atomic():
            sid = transaction.savepoint()
            
            # This is what happens when you select all and delete
            booking_admin.delete_queryset(request, all_bookings)
            
            transaction.savepoint_rollback(sid)
            
            print(f"   ✅ Bulk deletion of all bookings successful")
            
    except Exception as e:
        print(f"   ❌ Bulk deletion failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return 'BULK_ALL', str(e)
    
    return None, None

def test_specific_combinations():
    """Test specific combinations that might cause issues"""
    print(f"\n🔍 Testing Specific Booking Combinations")
    print("=" * 60)
    
    bookings = list(Booking.objects.all())
    
    if len(bookings) < 2:
        print("Need at least 2 bookings to test combinations")
        return
    
    admin_site = AdminSite()
    booking_admin = BookingAdmin(Booking, admin_site)
    
    factory = RequestFactory()
    request = factory.post('/admin/booking/booking/')
    request.user = User.objects.filter(is_superuser=True).first()
    
    # Test pairs
    for i in range(len(bookings)):
        for j in range(i+1, len(bookings)):
            booking1 = bookings[i]
            booking2 = bookings[j]
            
            print(f"\nTesting pair: {booking1.book_id} + {booking2.book_id}")
            
            queryset = Booking.objects.filter(id__in=[booking1.id, booking2.id])
            
            try:
                with transaction.atomic():
                    sid = transaction.savepoint()
                    booking_admin.delete_queryset(request, queryset)
                    transaction.savepoint_rollback(sid)
                    
                print(f"   ✅ Pair deletion successful")
                
            except Exception as e:
                print(f"   ❌ Pair deletion failed: {str(e)}")
                return f"{booking1.book_id}+{booking2.book_id}", str(e)
    
    return None, None

def check_database_integrity():
    """Check database integrity that might cause FK issues"""
    print(f"\n🔍 Checking Database Integrity")
    print("=" * 60)
    
    # Check for orphaned foreign keys
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check booking table foreign keys
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='booking_booking'
        """)
        result = cursor.fetchone()
        if result:
            print("Booking table structure:")
            print(result[0])
        
        # Check for any triggers or constraints
        cursor.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='trigger' AND tbl_name='booking_booking'
        """)
        triggers = cursor.fetchall()
        if triggers:
            print(f"\nFound {len(triggers)} triggers on booking table:")
            for trigger in triggers:
                print(f"- {trigger[0]}: {trigger[1]}")
        else:
            print("\nNo triggers found on booking table")

if __name__ == "__main__":
    print("🚨 ADMIN DELETION ERROR REPRODUCTION")
    print("Attempting to reproduce the exact error you're seeing")
    print("=" * 80)
    
    # Test exact admin deletion
    problematic_id, error = simulate_exact_admin_deletion()
    
    if problematic_id:
        print(f"\n🚨 FOUND THE PROBLEMATIC BOOKING!")
        print(f"Booking ID: {problematic_id}")
        print(f"Error: {error}")
        
        if problematic_id != 'BULK_ALL':
            # Investigate the specific booking
            booking = Booking.objects.get(book_id=problematic_id)
            print(f"\nInvestigating booking {problematic_id}:")
            print(f"- User: {booking.user}")
            print(f"- Cart: {booking.cart}")
            print(f"- Address: {booking.address}")
            print(f"- Assigned to: {booking.assigned_to}")
            print(f"- Status: {booking.status}")
    else:
        print(f"\n✅ No individual booking deletion issues found")
        
        # Test combinations
        problematic_combo, combo_error = test_specific_combinations()
        
        if problematic_combo:
            print(f"\n🚨 FOUND PROBLEMATIC COMBINATION!")
            print(f"Combination: {problematic_combo}")
            print(f"Error: {combo_error}")
        else:
            print(f"\n✅ No combination issues found either")
    
    # Check database integrity
    check_database_integrity()
    
    print(f"\n" + "=" * 80)
    if problematic_id or problematic_combo:
        print("🚨 Found specific cases causing the FK constraint error!")
    else:
        print("🤔 Could not reproduce the error in testing...")
        print("The error might be intermittent or related to specific admin interface state.")
