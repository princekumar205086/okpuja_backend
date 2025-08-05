#!/usr/bin/env python3
"""
Comprehensive test to debug astrology booking redirect issue.
This test will check the exact payment data and redirect logic.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from astrology.models import AstrologyBooking
import json

def debug_redirect_issue():
    """Debug the redirect issue with actual data"""
    
    print("=== DEBUGGING ASTROLOGY REDIRECT ISSUE ===\n")
    
    # Find the specific booking from the screenshot
    target_astro_book_id = "ASTRO_BOOK_20250805_7540D36E"
    
    print(f"🔍 Looking for booking: {target_astro_book_id}")
    
    # Check if this booking exists
    booking = AstrologyBooking.objects.filter(astro_book_id=target_astro_book_id).first()
    
    if booking:
        print(f"✅ Found booking: {booking.astro_book_id}")
        print(f"   Payment ID: {booking.payment_id}")
        print(f"   Status: {booking.status}")
        print(f"   User: {booking.user_id}")
        
        if booking.payment_id:
            try:
                payment_order = PaymentOrder.objects.get(id=booking.payment_id)
                print(f"✅ Found payment order: {payment_order.merchant_order_id}")
                print(f"   Payment Status: {payment_order.status}")
                print(f"   Amount: {payment_order.amount}")
                print(f"   Metadata keys: {list(payment_order.metadata.keys())}")
                print(f"   Full metadata: {json.dumps(payment_order.metadata, indent=2)}")
                
                # Check what the redirect logic would do
                print(f"\n🔧 REDIRECT LOGIC ANALYSIS:")
                
                # Check booking type
                booking_type = payment_order.metadata.get('booking_type')
                print(f"   Booking type: {booking_type}")
                
                if booking_type == 'astrology':
                    print("   ✅ Would be detected as astrology booking")
                    
                    # Check frontend URL
                    frontend_url = payment_order.metadata.get('frontend_redirect_url')
                    print(f"   Frontend redirect URL: {frontend_url}")
                    
                    if not frontend_url:
                        print("   ⚠️ No frontend_redirect_url in metadata - using default")
                        frontend_url = "https://www.okpuja.com"
                    
                    # Generate expected redirect URL
                    expected_url = f"{frontend_url.rstrip('/')}/astro-booking-success?astro_book_id={booking.astro_book_id}"
                    print(f"   Expected redirect: {expected_url}")
                    
                    # Check if this matches what user wants
                    desired_url = f"https://www.okpuja.com/astro-booking-success?astro_book_id={booking.astro_book_id}"
                    print(f"   Desired redirect:  {desired_url}")
                    
                    if expected_url == desired_url:
                        print("   ✅ URLs match!")
                    else:
                        print("   ❌ URLs don't match")
                        print(f"   Issue: frontend_redirect_url = '{frontend_url}' vs desired 'https://www.okpuja.com'")
                        
                else:
                    print("   ❌ Would NOT be detected as astrology booking")
                    print("   This is the problem! Need to check why booking_type is not 'astrology'")
                
            except PaymentOrder.DoesNotExist:
                print(f"❌ Payment order {booking.payment_id} not found")
        else:
            print("❌ Booking has no payment_id")
    else:
        print(f"❌ Booking {target_astro_book_id} not found")
        
        # Show available bookings
        print("\n📋 Available astrology bookings:")
        all_bookings = AstrologyBooking.objects.all().order_by('-created_at')[:5]
        for b in all_bookings:
            print(f"   - {b.astro_book_id} (Payment: {b.payment_id})")
    
    print("\n🔧 RECOMMENDED FIXES:")
    print("1. Ensure payment metadata has 'booking_type': 'astrology'")
    print("2. Ensure payment metadata has 'frontend_redirect_url': 'https://www.okpuja.com'")
    print("3. Check redirect handler logs to see what's happening")
    print("4. Test with a new astrology booking to verify the fix")

def test_redirect_logic_directly():
    """Test the redirect logic with a mock scenario"""
    
    print("\n=== TESTING REDIRECT LOGIC DIRECTLY ===\n")
    
    # Find any astrology booking with payment
    booking = AstrologyBooking.objects.filter(payment_id__isnull=False).first()
    
    if booking and booking.payment_id:
        try:
            payment_order = PaymentOrder.objects.get(id=booking.payment_id)
            
            # Simulate the redirect handler logic
            print(f"🔍 Testing with booking: {booking.astro_book_id}")
            print(f"   Payment order: {payment_order.merchant_order_id}")
            
            # Check if metadata contains booking_type
            metadata = payment_order.metadata
            booking_type = metadata.get('booking_type')
            
            print(f"   Metadata booking_type: {booking_type}")
            
            if booking_type == 'astrology':
                print("   ✅ Detected as astrology booking")
                
                # Get frontend base
                frontend_base = metadata.get('frontend_redirect_url', 'https://www.okpuja.com')
                if frontend_base.endswith('/'):
                    frontend_base = frontend_base.rstrip('/')
                    
                # Build redirect URL
                redirect_url = f"{frontend_base}/astro-booking-success?astro_book_id={booking.astro_book_id}"
                print(f"   Generated redirect: {redirect_url}")
                
                # Check if this is what we want
                if 'astro-booking-success' in redirect_url and booking.astro_book_id in redirect_url:
                    print("   ✅ Redirect URL looks correct!")
                else:
                    print("   ❌ Redirect URL is incorrect")
            else:
                print("   ❌ Not detected as astrology booking")
                print(f"   ⚠️ Need to fix metadata: booking_type should be 'astrology', got '{booking_type}'")
                
        except PaymentOrder.DoesNotExist:
            print(f"❌ Payment order not found")
    else:
        print("❌ No astrology booking with payment found")

if __name__ == '__main__':
    debug_redirect_issue()
    test_redirect_logic_directly()
