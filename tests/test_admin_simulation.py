#!/usr/bin/env python
"""
Test script that exactly mimics Django admin deletion process
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from django.contrib.admin.utils import NestedObjects
from django.db import DEFAULT_DB_ALIAS, transaction
from django.contrib.admin.actions import delete_selected
from django.contrib.admin import ModelAdmin
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

User = get_user_model()

def simulate_admin_deletion():
    """Simulate exact Django admin deletion process"""
    print("🎭 Simulating Django Admin Deletion Process")
    print("=" * 60)
    
    # Get all bookings
    bookings = Booking.objects.all()
    print(f"Found {bookings.count()} bookings to test")
    
    # Test each booking with admin deletion process
    for booking in bookings:
        print(f"\n📋 Testing admin deletion for: {booking.book_id}")
        
        # Step 1: Create a queryset like admin does
        queryset = Booking.objects.filter(id=booking.id)
        
        # Step 2: Use NestedObjects to collect related objects (like admin does)
        try:
            collector = NestedObjects(using=DEFAULT_DB_ALIAS)
            collector.collect(queryset)
            
            print(f"   Related objects to delete:")
            for model, instances in collector.model_objs.items():
                if instances:
                    print(f"   - {model._meta.label}: {len(instances)} objects")
            
            # Step 3: Try the actual deletion (like admin does)
            with transaction.atomic():
                sid = transaction.savepoint()
                
                # This is exactly what admin delete_selected does
                num_deleted, deleted_details = collector.delete()
                
                # Rollback since this is just a test
                transaction.savepoint_rollback(sid)
                
                print(f"   ✅ Admin deletion would succeed")
                print(f"   Would delete: {num_deleted} objects")
                for model_name, count in deleted_details.items():
                    print(f"     - {model_name}: {count}")
                    
        except Exception as e:
            print(f"   ❌ Admin deletion would fail: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # Try to get more details about the error
            if "FOREIGN KEY constraint failed" in str(e):
                print(f"   🔍 Investigating FK constraint...")
                check_foreign_key_issues(booking)

def check_foreign_key_issues(booking):
    """Check for specific foreign key issues"""
    print(f"     Checking FK relationships for {booking.book_id}:")
    
    # Check each FK field
    fk_fields = {
        'user': booking.user,
        'cart': booking.cart,
        'address': booking.address,
        'assigned_to': booking.assigned_to
    }
    
    for field_name, related_obj in fk_fields.items():
        if related_obj:
            print(f"     - {field_name}: {related_obj} (ID: {related_obj.id})")
            # Check if the related object exists
            try:
                model_class = related_obj.__class__
                obj = model_class.objects.get(id=related_obj.id)
                print(f"       ✅ Related object exists")
            except model_class.DoesNotExist:
                print(f"       ❌ Related object missing!")
        else:
            print(f"     - {field_name}: None")
    
    # Check reverse FK relationships
    print(f"     Reverse relationships:")
    attachments = booking.attachments.all()
    print(f"     - attachments: {attachments.count()}")

def test_bulk_admin_deletion():
    """Test bulk deletion like admin interface"""
    print(f"\n🗂️ Testing Bulk Admin Deletion")
    print("=" * 60)
    
    # Create a test booking for bulk deletion
    try:
        test_user = User.objects.get(email="asliprinceraj@gmail.com")
        from accounts.models import Address
        from datetime import date, time
        from booking.models import BookingStatus
        
        test_address = Address.objects.get(id=1)
        
        # Create a test booking
        test_booking = Booking.objects.create(
            user=test_user,
            selected_date=date.today(),
            selected_time=time(14, 0),
            address=test_address,
            status=BookingStatus.PENDING,
        )
        print(f"Created test booking: {test_booking.book_id}")
        
        # Test bulk deletion
        queryset = Booking.objects.filter(book_id=test_booking.book_id)
        
        print(f"Testing bulk deletion on queryset with {queryset.count()} booking(s)")
        
        # Simulate admin bulk deletion
        try:
            collector = NestedObjects(using=DEFAULT_DB_ALIAS)
            collector.collect(queryset)
            
            with transaction.atomic():
                sid = transaction.savepoint()
                num_deleted, deleted_details = collector.delete()
                transaction.savepoint_rollback(sid)
                
                print(f"✅ Bulk deletion would succeed")
                print(f"Would delete: {num_deleted} objects")
                
        except Exception as e:
            print(f"❌ Bulk deletion failed: {str(e)}")
            
        # Clean up test booking
        test_booking.delete()
        print(f"Cleaned up test booking")
        
    except Exception as e:
        print(f"Error in bulk deletion test: {str(e)}")

def test_admin_queryset_deletion():
    """Test using queryset.delete() like admin does"""
    print(f"\n📝 Testing Admin Queryset.delete()")
    print("=" * 60)
    
    bookings = Booking.objects.all()
    
    for booking in bookings:
        print(f"\nTesting queryset.delete() for: {booking.book_id}")
        
        # Create queryset like admin
        queryset = Booking.objects.filter(id=booking.id)
        
        try:
            with transaction.atomic():
                sid = transaction.savepoint()
                
                # This is what happens when admin calls queryset.delete()
                num_deleted, deleted_details = queryset.delete()
                
                transaction.savepoint_rollback(sid)
                
                print(f"✅ queryset.delete() would succeed")
                print(f"Would delete: {num_deleted} objects: {deleted_details}")
                
        except Exception as e:
            print(f"❌ queryset.delete() failed: {str(e)}")
            if "FOREIGN KEY constraint failed" in str(e):
                print(f"🔍 This is the exact error admin is getting!")

if __name__ == "__main__":
    print("🧪 DJANGO ADMIN DELETION SIMULATION")
    print("This script exactly mimics what Django admin does when deleting")
    print("=" * 80)
    
    # Test individual deletions
    simulate_admin_deletion()
    
    # Test bulk deletion
    test_bulk_admin_deletion()
    
    # Test queryset deletion
    test_admin_queryset_deletion()
    
    print("\n" + "=" * 80)
    print("✅ Admin simulation complete!")
