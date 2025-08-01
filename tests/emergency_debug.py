#!/usr/bin/env python
"""
Real-time admin error debugging tool
Run this when you get the FK constraint error to identify the exact cause
"""
import os
import django
import sys
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking, BookingAttachment
from django.db import connection
from django.contrib.admin.utils import NestedObjects
from django.db import DEFAULT_DB_ALIAS

def emergency_admin_debug():
    """Emergency debugging for admin FK constraint errors"""
    print("🚨 EMERGENCY ADMIN DEBUG TOOL")
    print("=" * 60)
    print(f"Run time: {datetime.now()}")
    
    # Check current database state
    print(f"\n📊 Current Database State:")
    print(f"- Total bookings: {Booking.objects.count()}")
    print(f"- Total attachments: {BookingAttachment.objects.count()}")
    
    # Check for any database locks or transactions
    with connection.cursor() as cursor:
        # Check if there are any active transactions
        cursor.execute("PRAGMA database_list")
        databases = cursor.fetchall()
        print(f"- Active databases: {len(databases)}")
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()
        print(f"- Foreign key constraints: {'ON' if fk_status[0] else 'OFF'}")
        
        # Check for any locks
        cursor.execute("PRAGMA lock_status")
        lock_status = cursor.fetchall()
        print(f"- Lock status: {lock_status}")
    
    # Test each booking for deletability RIGHT NOW
    print(f"\n🔍 REAL-TIME DELETION TEST:")
    bookings = Booking.objects.all().order_by('id')
    
    for booking in bookings:
        print(f"\n📋 {booking.book_id} (ID: {booking.id})")
        
        # Test with NestedObjects (what admin uses)
        try:
            collector = NestedObjects(using=DEFAULT_DB_ALIAS)
            queryset = Booking.objects.filter(id=booking.id)
            collector.collect(queryset)
            
            # Check what would be deleted
            related_count = sum(len(instances) for instances in collector.model_objs.values())
            print(f"   Would delete {related_count} related objects")
            
            # List related objects
            for model, instances in collector.model_objs.items():
                if instances and model != Booking:
                    print(f"   - {model._meta.label}: {len(instances)}")
            
            print(f"   ✅ Can be deleted")
            
        except Exception as e:
            print(f"   ❌ CANNOT BE DELETED: {str(e)}")
            print(f"   This is likely the problematic booking!")
            
            # Deep dive into this booking
            print(f"   📊 Deep Analysis:")
            print(f"   - Created: {booking.created_at}")
            print(f"   - Updated: {booking.updated_at}")
            print(f"   - User ID: {booking.user_id}")
            print(f"   - Cart ID: {booking.cart_id}")
            print(f"   - Address ID: {booking.address_id}")
            print(f"   - Assigned To ID: {booking.assigned_to_id}")
            
            # Check if any FK references are broken
            print(f"   🔗 FK Reference Check:")
            
            # Check user
            try:
                user = booking.user
                print(f"   - User: ✅ {user.email}")
            except Exception as ue:
                print(f"   - User: ❌ {str(ue)}")
            
            # Check cart
            try:
                cart = booking.cart
                print(f"   - Cart: ✅ {cart.cart_id if cart else 'None'}")
            except Exception as ce:
                print(f"   - Cart: ❌ {str(ce)}")
            
            # Check address
            try:
                address = booking.address
                print(f"   - Address: ✅ {address.id if address else 'None'}")
            except Exception as ae:
                print(f"   - Address: ❌ {str(ae)}")
            
            # Check assigned_to
            try:
                assigned = booking.assigned_to
                print(f"   - Assigned To: ✅ {assigned.email if assigned else 'None'}")
            except Exception as ase:
                print(f"   - Assigned To: ❌ {str(ase)}")
            
            return booking.book_id
    
    print(f"\n✅ All bookings can be deleted successfully")
    return None

def check_for_foreign_key_violations():
    """Check for any foreign key violations in the database"""
    print(f"\n🔍 FOREIGN KEY VIOLATION CHECK:")
    
    with connection.cursor() as cursor:
        # Enable foreign key checks
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        
        if violations:
            print(f"❌ Found {len(violations)} foreign key violations:")
            for violation in violations:
                print(f"   - Table: {violation[0]}, Row: {violation[1]}, Parent: {violation[2]}, FK: {violation[3]}")
        else:
            print(f"✅ No foreign key violations found")

def suggest_fixes():
    """Suggest potential fixes"""
    print(f"\n💡 SUGGESTED FIXES:")
    print(f"1. If you found a problematic booking ID above:")
    print(f"   - Try deleting that specific booking individually")
    print(f"   - Check if it has orphaned relationships")
    print(f"2. If no problematic booking found but error persists:")
    print(f"   - The error might be caused by admin interface caching")
    print(f"   - Try refreshing the admin page")
    print(f"   - Clear browser cache")
    print(f"3. Nuclear option:")
    print(f"   - Restart Django server")
    print(f"   - Check server logs for more detailed error info")

if __name__ == "__main__":
    print("🚨 EMERGENCY ADMIN DEBUGGING")
    print("Run this script immediately after getting the FK constraint error")
    print("=" * 80)
    
    # Find problematic booking
    problematic_id = emergency_admin_debug()
    
    # Check for FK violations
    check_for_foreign_key_violations()
    
    # Suggest fixes
    suggest_fixes()
    
    if problematic_id:
        print(f"\n🎯 RESULT: Problematic booking found: {problematic_id}")
        print(f"Focus on this booking for manual inspection/deletion")
    else:
        print(f"\n🤔 RESULT: No problematic booking found in current state")
        print(f"The error might be intermittent or browser-cached")
    
    print(f"\n" + "=" * 80)
