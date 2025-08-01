#!/usr/bin/env python
"""
Diagnostic script to identify problematic booking IDs that cause FK constraint errors
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking, BookingAttachment
from payments.models import PaymentOrder
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

def check_booking_dependencies(booking):
    """Check what dependencies a booking has that might cause FK constraint issues"""
    dependencies = {}
    
    # Check BookingAttachments
    attachments = BookingAttachment.objects.filter(booking=booking)
    dependencies['attachments'] = list(attachments.values('id', 'image', 'caption'))
    
    # Check PaymentOrders
    try:
        payment_orders = PaymentOrder.objects.filter(
            cart_id=booking.cart.cart_id if booking.cart else None
        )
        dependencies['payment_orders'] = list(payment_orders.values('id', 'merchant_transaction_id', 'status'))
    except:
        dependencies['payment_orders'] = []
    
    # Check other potential references
    dependencies['cart'] = {
        'id': booking.cart.id if booking.cart else None,
        'cart_id': booking.cart.cart_id if booking.cart else None,
        'status': booking.cart.status if booking.cart else None
    }
    
    dependencies['user'] = {
        'id': booking.user.id,
        'email': booking.user.email
    }
    
    dependencies['address'] = {
        'id': booking.address.id if booking.address else None
    }
    
    dependencies['assigned_to'] = {
        'id': booking.assigned_to.id if booking.assigned_to else None,
        'email': booking.assigned_to.email if booking.assigned_to else None
    }
    
    return dependencies

def test_individual_booking_deletion():
    """Test deletion of each booking individually to find problematic ones"""
    print("🔍 Testing individual booking deletion to identify problematic bookings...")
    print("=" * 80)
    
    bookings = Booking.objects.all().order_by('created_at')
    problematic_bookings = []
    successful_deletions = []
    
    for booking in bookings:
        print(f"\n📋 Testing booking: {booking.book_id} ({booking.user.email})")
        
        # Check dependencies first
        dependencies = check_booking_dependencies(booking)
        print(f"   - Attachments: {len(dependencies['attachments'])}")
        print(f"   - Payment Orders: {len(dependencies['payment_orders'])}")
        print(f"   - Cart: {dependencies['cart']['cart_id']}")
        print(f"   - Status: {booking.status}")
        
        # Test deletion in a transaction that we'll rollback
        try:
            with transaction.atomic():
                # Create a savepoint
                sid = transaction.savepoint()
                
                # Try to delete
                booking.delete()
                
                # If we get here, deletion would succeed
                transaction.savepoint_rollback(sid)
                print(f"   ✅ Can be deleted safely")
                successful_deletions.append({
                    'book_id': booking.book_id,
                    'dependencies': dependencies
                })
                
        except Exception as e:
            print(f"   ❌ Deletion would fail: {str(e)}")
            problematic_bookings.append({
                'book_id': booking.book_id,
                'error': str(e),
                'dependencies': dependencies
            })
    
    return problematic_bookings, successful_deletions

def analyze_problematic_bookings(problematic_bookings):
    """Analyze what makes certain bookings problematic"""
    print("\n" + "=" * 80)
    print("🚨 PROBLEMATIC BOOKINGS ANALYSIS")
    print("=" * 80)
    
    if not problematic_bookings:
        print("✅ No problematic bookings found!")
        return
    
    for booking_info in problematic_bookings:
        print(f"\n🔴 Booking ID: {booking_info['book_id']}")
        print(f"   Error: {booking_info['error']}")
        
        deps = booking_info['dependencies']
        print(f"   Dependencies:")
        print(f"   - Attachments: {len(deps['attachments'])}")
        for att in deps['attachments']:
            print(f"     • Attachment ID {att['id']}: {att['caption']}")
        
        print(f"   - Payment Orders: {len(deps['payment_orders'])}")
        for po in deps['payment_orders']:
            print(f"     • Payment {po['id']}: {po['merchant_transaction_id']} ({po['status']})")
        
        print(f"   - Cart: {deps['cart']}")
        print(f"   - User: {deps['user']}")
        print(f"   - Address: {deps['address']}")
        print(f"   - Assigned To: {deps['assigned_to']}")

def fix_problematic_bookings(problematic_bookings):
    """Attempt to fix problematic bookings by cleaning up dependencies"""
    print("\n" + "=" * 80)
    print("🔧 ATTEMPTING TO FIX PROBLEMATIC BOOKINGS")
    print("=" * 80)
    
    if not problematic_bookings:
        print("✅ No problematic bookings to fix!")
        return
    
    for booking_info in problematic_bookings:
        book_id = booking_info['book_id']
        print(f"\n🔧 Fixing booking: {book_id}")
        
        try:
            booking = Booking.objects.get(book_id=book_id)
            
            # Try to clean up attachments first
            attachments = BookingAttachment.objects.filter(booking=booking)
            if attachments.exists():
                print(f"   Deleting {attachments.count()} attachments...")
                attachments.delete()
            
            # Test deletion again
            with transaction.atomic():
                sid = transaction.savepoint()
                booking.delete()
                transaction.savepoint_rollback(sid)
                print(f"   ✅ Booking {book_id} can now be deleted safely")
                
        except Exception as e:
            print(f"   ❌ Still can't fix booking {book_id}: {str(e)}")

if __name__ == "__main__":
    print("🔍 BOOKING DELETION DIAGNOSTIC TOOL")
    print("This script identifies which specific bookings are causing FK constraint errors")
    print("=" * 80)
    
    # Test each booking individually
    problematic, successful = test_individual_booking_deletion()
    
    # Analyze problematic bookings
    analyze_problematic_bookings(problematic)
    
    # Show summary
    print(f"\n📊 SUMMARY:")
    print(f"   • Total bookings: {len(problematic) + len(successful)}")
    print(f"   • Successful deletions: {len(successful)}")
    print(f"   • Problematic bookings: {len(problematic)}")
    
    if problematic:
        print(f"\n🚨 Problematic booking IDs:")
        for booking_info in problematic:
            print(f"   - {booking_info['book_id']}")
        
        # Ask if user wants to attempt fixes
        print(f"\n❓ The script can attempt to fix these by cleaning up dependencies.")
        response = input("Do you want to attempt automatic fixes? (y/n): ")
        if response.lower() == 'y':
            fix_problematic_bookings(problematic)
    else:
        print(f"\n🎉 All bookings can be deleted safely!")
