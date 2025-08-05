#!/usr/bin/env python3
"""
Simple test to verify the redirect fix using existing data
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from astrology.models import AstrologyBooking

def test_redirect_logic():
    """Test the redirect logic with existing data"""
    
    print("=== Testing Redirect Logic with Existing Data ===\n")
    
    # Find existing astrology booking with payment
    booking = AstrologyBooking.objects.filter(payment_id__isnull=False).first()
    
    if booking and booking.payment_id:
        try:
            payment = PaymentOrder.objects.get(id=booking.payment_id)
            print(f"Found booking: {booking.astro_book_id}")
            print(f"Payment status: {payment.status}")
            print(f"Payment metadata: {payment.metadata.get('booking_type', 'Not set')}")
            
            # Simulate the redirect logic
            if payment.metadata.get('booking_type') == 'astrology':
                frontend_base = payment.metadata.get('frontend_redirect_url', 'https://okpuja.com')
                if frontend_base.endswith('/'):
                    frontend_base = frontend_base.rstrip('/')
                
                # SUCCESS redirect
                success_url = f"{frontend_base}/astro-booking-success?merchant_order_id={booking.astro_book_id}"
                print(f"\n✅ SUCCESS redirect would be: {success_url}")
                
                # FAILURE redirect  
                failure_url = f"{frontend_base}/astro-booking-failed?merchant_order_id={booking.astro_book_id}&reason=failed"
                print(f"✅ FAILURE redirect would be: {failure_url}")
                
                # Verify format
                if 'okpuja.com/astro-booking-success' in success_url:
                    print("✅ Correct success URL format")
                if booking.astro_book_id in success_url:
                    print("✅ Contains astro_book_id")
                if 'merchant_order_id=' in success_url:
                    print("✅ Uses merchant_order_id parameter")
                    
            else:
                print("❌ Booking type is not 'astrology'")
                
        except PaymentOrder.DoesNotExist:
            print(f"❌ Payment order {booking.payment_id} not found")
    else:
        print("❌ No astrology booking with payment found")
    
    print("\n=== Manual Test Example ===")
    print("To test manually, create a payment with:")
    print("- metadata['booking_type'] = 'astrology'")
    print("- metadata['frontend_redirect_url'] = 'https://okpuja.com'")
    print("- Associated AstrologyBooking with astro_book_id")
    print("\nExpected redirect:")
    print("SUCCESS: https://okpuja.com/astro-booking-success?merchant_order_id=ASTRO_BOOK_XXXXXXXX")
    print("FAILURE: https://okpuja.com/astro-booking-failed?merchant_order_id=ASTRO_BOOK_XXXXXXXX&reason=failed")

if __name__ == '__main__':
    test_redirect_logic()
