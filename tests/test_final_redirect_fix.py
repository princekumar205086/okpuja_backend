#!/usr/bin/env python3
"""
Test to verify the redirect fix uses correct URL format:
Expected: https://www.okpuja.com/astro-booking-success?astro_book_id=ASTRO_BOOK_XXXXXXXX
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from astrology.models import AstrologyBooking, AstrologyService
from payments.redirect_handler import PaymentRedirectHandler
from django.test import RequestFactory
from unittest.mock import patch

def test_correct_url_format():
    """Test that redirect produces the exact URL format the user wants"""
    
    print("=== TESTING CORRECT URL FORMAT ===\n")
    
    desired_pattern = "https://www.okpuja.com/astro-booking-success?astro_book_id=ASTRO_BOOK_"
    not_wanted = "https://www.okpuja.com/confirmbooking?status=completed"
    
    print(f"✅ Desired: {desired_pattern}XXXXXXXX")
    print(f"❌ Not wanted: {not_wanted}")
    print()
    
    # Create test payment with correct metadata
    test_payment = PaymentOrder.objects.filter(merchant_order_id='FINAL_REDIRECT_TEST').first()
    if not test_payment:
        test_payment = PaymentOrder.objects.create(
            merchant_order_id='FINAL_REDIRECT_TEST',
            user_id=1,
            amount=1999,
            status='SUCCESS',
            metadata={
                'booking_type': 'astrology',
                'frontend_redirect_url': 'https://www.okpuja.com',  # With www
                'service_id': 1,
                'user_id': 1
            }
        )
        print(f"✅ Created test payment: {test_payment.merchant_order_id}")
    
    # Create astrology booking
    test_booking = AstrologyBooking.objects.filter(payment_id=str(test_payment.id)).first()
    if not test_booking:
        service = AstrologyService.objects.first()
        if not service:
            service = AstrologyService.objects.create(
                title="Final Test Service",
                service_type="HOROSCOPE",
                description="Final test",
                price=1999.00
            )
        
        test_booking = AstrologyBooking.objects.create(
            astro_book_id='ASTRO_BOOK_20250805_7540D36E',  # Use the exact ID from screenshot
            user_id=1,
            service=service,
            language='Hindi',
            preferred_date='2025-08-15',
            preferred_time='14:00:00',
            birth_place='Test Place',
            birth_date='1995-05-15',
            birth_time='08:30:00',
            gender='MALE',
            contact_email='test@example.com',
            contact_phone='9876543210',
            payment_id=str(test_payment.id),
            status='CONFIRMED'
        )
        print(f"✅ Created test booking: {test_booking.astro_book_id}")
    
    # Test the redirect logic
    print(f"\n=== TESTING REDIRECT FOR {test_booking.astro_book_id} ===")
    
    with patch('payments.services.PaymentService.check_payment_status') as mock_status:
        mock_status.return_value = {
            'success': True,
            'payment_order': test_payment,
            'transaction_id': 'TXN123456'
        }
        
        factory = RequestFactory()
        request = factory.get('/payments/redirect/', {
            'order_id': test_payment.merchant_order_id,
            'transaction_id': 'TXN123456'
        })
        
        handler = PaymentRedirectHandler()
        response = handler.get(request)
        redirect_url = response.url
        
        print(f"Generated URL: {redirect_url}")
        
        # Validate the URL format
        checks = [
            ('Uses www.okpuja.com', 'https://www.okpuja.com' in redirect_url),
            ('Goes to astro-booking-success', '/astro-booking-success' in redirect_url),
            ('Has astro_book_id parameter', 'astro_book_id=' in redirect_url),
            ('Contains correct booking ID', test_booking.astro_book_id in redirect_url),
            ('NOT confirmbooking page', 'confirmbooking' not in redirect_url),
            ('Correct format match', redirect_url.startswith('https://www.okpuja.com/astro-booking-success?astro_book_id='))
        ]
        
        print(f"\n📋 Validation Results:")
        all_passed = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
            if not result:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 SUCCESS! Redirect URL is correct format!")
            print(f"Expected: {desired_pattern}XXXXXXXX")
            print(f"Got:      {redirect_url}")
        else:
            print(f"\n❌ Some checks failed - need to debug further")
    
    print(f"\n=== TESTING PRODUCTION SCENARIO ===")
    print(f"To test in production:")
    print(f"1. Create an astrology booking")
    print(f"2. Complete payment via PhonePe")
    print(f"3. Should redirect to: https://www.okpuja.com/astro-booking-success?astro_book_id=ASTRO_BOOK_XXXXXXXX")
    print(f"4. Should NOT redirect to: https://www.okpuja.com/confirmbooking?status=completed")

if __name__ == '__main__':
    test_correct_url_format()
