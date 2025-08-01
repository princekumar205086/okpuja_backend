#!/usr/bin/env python
"""
Check for bookings with cart-related issues that might cause admin problems
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from cart.models import Cart

def check_cart_issues():
    """Check for cart-related issues in bookings"""
    print("🛒 Checking Cart-Related Issues in Bookings")
    print("=" * 60)
    
    bookings = Booking.objects.all()
    issues = []
    
    for booking in bookings:
        print(f"\n📋 Booking: {booking.book_id}")
        
        # Check if cart exists
        if booking.cart is None:
            print(f"   ❌ Cart is None")
            issues.append({
                'book_id': booking.book_id,
                'issue': 'cart_is_none',
                'description': 'Cart is None'
            })
        else:
            print(f"   ✅ Cart exists: {booking.cart.cart_id}")
            
            # Check if cart actually exists in database
            try:
                cart = Cart.objects.get(id=booking.cart.id)
                print(f"   ✅ Cart found in database")
                
                # Check cart fields that admin tries to access
                print(f"   - Service Type: {getattr(cart, 'service_type', 'NOT SET')}")
                print(f"   - Puja Service: {getattr(cart, 'puja_service', 'NOT SET')}")
                print(f"   - Astrology Service: {getattr(cart, 'astrology_service', 'NOT SET')}")
                
                # Test the admin's get_service_name logic
                try:
                    if cart.service_type == 'PUJA' and cart.puja_service:
                        service_name = cart.puja_service.title
                    elif cart.service_type == 'ASTROLOGY' and cart.astrology_service:
                        service_name = cart.astrology_service.title
                    else:
                        service_name = '-'
                    print(f"   ✅ Service name: {service_name}")
                except Exception as e:
                    print(f"   ❌ Error getting service name: {str(e)}")
                    issues.append({
                        'book_id': booking.book_id,
                        'issue': 'service_name_error',
                        'description': f'Error in get_service_name: {str(e)}'
                    })
                
            except Cart.DoesNotExist:
                print(f"   ❌ Cart not found in database (orphaned FK)")
                issues.append({
                    'book_id': booking.book_id,
                    'issue': 'orphaned_cart_fk',
                    'description': 'Cart FK points to non-existent cart'
                })
            except Exception as e:
                print(f"   ❌ Error accessing cart: {str(e)}")
                issues.append({
                    'book_id': booking.book_id,
                    'issue': 'cart_access_error',
                    'description': f'Error accessing cart: {str(e)}'
                })
    
    return issues

def fix_cart_issues(issues):
    """Fix cart-related issues"""
    print(f"\n🔧 Fixing Cart Issues")
    print("=" * 60)
    
    if not issues:
        print("✅ No cart issues to fix!")
        return
    
    for issue in issues:
        book_id = issue['book_id']
        issue_type = issue['issue']
        
        print(f"\n🔧 Fixing {book_id}: {issue_type}")
        
        try:
            booking = Booking.objects.get(book_id=book_id)
            
            if issue_type == 'cart_is_none':
                print(f"   Setting cart to None (already is None)")
                # Nothing to do, cart is already None
                
            elif issue_type == 'orphaned_cart_fk':
                print(f"   Setting cart to None (removing orphaned FK)")
                booking.cart = None
                booking.save()
                
            elif issue_type in ['service_name_error', 'cart_access_error']:
                print(f"   Setting cart to None (fixing access error)")
                booking.cart = None
                booking.save()
                
            print(f"   ✅ Fixed booking {book_id}")
            
        except Exception as e:
            print(f"   ❌ Error fixing {book_id}: {str(e)}")

def test_admin_access():
    """Test accessing booking admin functionality"""
    print(f"\n🎭 Testing Admin Access")
    print("=" * 60)
    
    bookings = Booking.objects.all()
    
    for booking in bookings:
        print(f"\nTesting admin access for: {booking.book_id}")
        
        # Test get_service_name method
        try:
            if booking.cart and hasattr(booking.cart, 'service_type'):
                if booking.cart.service_type == 'PUJA' and booking.cart.puja_service:
                    service_name = booking.cart.puja_service.title
                elif booking.cart.service_type == 'ASTROLOGY' and booking.cart.astrology_service:
                    service_name = booking.cart.astrology_service.title
                else:
                    service_name = '-'
            else:
                service_name = '-'
            print(f"   ✅ Service name: {service_name}")
        except Exception as e:
            print(f"   ❌ get_service_name error: {str(e)}")
        
        # Test total_amount property
        try:
            total = booking.total_amount
            print(f"   ✅ Total amount: {total}")
        except Exception as e:
            print(f"   ❌ total_amount error: {str(e)}")

if __name__ == "__main__":
    print("🔍 BOOKING CART ISSUES DIAGNOSTIC")
    print("Checking for cart-related issues that might cause admin errors")
    print("=" * 80)
    
    # Check for issues
    issues = check_cart_issues()
    
    # Test admin access
    test_admin_access()
    
    # Show summary
    print(f"\n📊 SUMMARY:")
    print(f"   • Total issues found: {len(issues)}")
    
    if issues:
        print(f"\n🚨 Issues found:")
        for issue in issues:
            print(f"   - {issue['book_id']}: {issue['description']}")
        
        # Ask if user wants to fix
        response = input(f"\nDo you want to fix these issues? (y/n): ")
        if response.lower() == 'y':
            fix_cart_issues(issues)
            print(f"\n✅ Issues fixed! Try the admin interface again.")
    else:
        print(f"\n🎉 No cart issues found!")
