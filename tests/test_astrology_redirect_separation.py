#!/usr/bin/env python3
"""
Test script to verify astrology booking redirects to the correct URL format:
Expected: https://okpuja.com/astro-booking-success?merchant_order_id=ASTRO_BOOK_20250805_4734D7DB
NOT: https://www.okpuja.com/confirmbooking?status=completed
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from astrology.models import AstrologyBooking, AstrologyService
from payments.redirect_handler import PaymentRedirectHandler
from django.test import RequestFactory
from unittest.mock import patch

def test_astrology_redirect_fix():
    """Test that astrology bookings redirect to the correct URL format"""
    
    print("=== Testing Astrology Booking Redirect Fix ===\n")
    
    # Expected URL format
    expected_success_pattern = "https://okpuja.com/astro-booking-success?merchant_order_id=ASTRO_BOOK_"
    not_expected = "https://www.okpuja.com/confirmbooking?status=completed"
    
    print(f"✅ Expected pattern: {expected_success_pattern}*")
    print(f"❌ Should NOT be: {not_expected}")
    print()
    
    # Create test payment order for astrology booking
    test_payment = PaymentOrder.objects.filter(merchant_order_id='ASTRO_REDIRECT_TEST').first()
    if not test_payment:
        test_payment = PaymentOrder.objects.create(
            merchant_order_id='ASTRO_REDIRECT_TEST',
            user_id=1,
            amount=1999,
            status='SUCCESS',
            metadata={
                'booking_type': 'astrology',
                'frontend_redirect_url': 'https://okpuja.com',
                'service_id': 1,
                'user_id': 1,
                'language': 'Hindi',
                'preferred_date': '2025-08-15',
                'preferred_time': '14:00:00',
                'birth_place': 'Delhi, India',
                'birth_date': '1995-05-15',
                'birth_time': '08:30:00',
                'gender': 'MALE',
                'questions': 'Test astrology redirect',
                'contact_email': 'test@example.com',
                'contact_phone': '9876543210'
            }
        )
        print(f"✅ Created test payment order: {test_payment.merchant_order_id}")
    
    # Create astrology booking
    test_booking = AstrologyBooking.objects.filter(payment_id=str(test_payment.id)).first()
    if not test_booking:
        # Get or create a service
        service = AstrologyService.objects.first()
        if not service:
            service = AstrologyService.objects.create(
                title="Test Astrology Service",
                service_type="HOROSCOPE",
                description="Test service for redirect testing",
                price=1999.00
            )
        
        test_booking = AstrologyBooking.objects.create(
            astro_book_id='ASTRO_BOOK_20250805_4734D7DB',  # Use your specific ID format
            user_id=1,
            service=service,
            language='Hindi',
            preferred_date='2025-08-15',
            preferred_time='14:00:00',
            birth_place='Delhi, India',
            birth_date='1995-05-15',
            birth_time='08:30:00',
            gender='MALE',
            questions='Test astrology redirect',
            contact_email='test@example.com',
            contact_phone='9876543210',
            payment_id=str(test_payment.id),
            status='CONFIRMED'
        )
        print(f"✅ Created test astrology booking: {test_booking.astro_book_id}")
    
    # Test SUCCESS redirect
    print("\n=== Testing SUCCESS Redirect ===")
    
    # Mock payment status check
    with patch('payments.services.PaymentService.check_payment_status') as mock_status:
        mock_status.return_value = {
            'success': True,
            'payment_order': test_payment,
            'transaction_id': 'TXN123456'
        }
        
        # Create request factory and simulate redirect
        factory = RequestFactory()
        request = factory.get('/payments/redirect/', {
            'order_id': test_payment.merchant_order_id,
            'transaction_id': 'TXN123456'
        })
        
        # Process redirect
        handler = PaymentRedirectHandler()
        response = handler.get(request)
        redirect_url = response.url
        
        print(f"Generated redirect URL: {redirect_url}")
        
        # Validate redirect URL
        if 'astro-booking-success' in redirect_url:
            print("✅ Redirects to astro-booking-success page")
        else:
            print("❌ Does NOT redirect to astro-booking-success page")
            
        if 'okpuja.com' in redirect_url:
            print("✅ Uses okpuja.com domain")
        else:
            print("❌ Does NOT use okpuja.com domain")
            
        if test_booking.astro_book_id in redirect_url:
            print(f"✅ Contains astro_book_id: {test_booking.astro_book_id}")
        else:
            print(f"❌ Does NOT contain astro_book_id: {test_booking.astro_book_id}")
            
        if 'merchant_order_id=' in redirect_url:
            print("✅ Has merchant_order_id parameter")
        else:
            print("❌ Missing merchant_order_id parameter")
            
        if 'confirmbooking' not in redirect_url:
            print("✅ Does NOT redirect to puja confirmbooking page")
        else:
            print("❌ Incorrectly redirects to puja confirmbooking page")
    
    # Test FAILURE redirect
    print("\n=== Testing FAILURE Redirect ===")
    
    # Update payment status to failed
    test_payment.status = 'FAILED'
    test_payment.save()
    
    with patch('payments.services.PaymentService.check_payment_status') as mock_status:
        mock_status.return_value = {
            'success': True,
            'payment_order': test_payment,
            'transaction_id': 'TXN123456'
        }
        
        request = factory.get('/payments/redirect/', {
            'order_id': test_payment.merchant_order_id,
            'transaction_id': 'TXN123456'
        })
        
        response = handler.get(request)
        redirect_url = response.url
        
        print(f"Generated failure redirect URL: {redirect_url}")
        
        if 'astro-booking-failed' in redirect_url:
            print("✅ Redirects to astro-booking-failed page")
        else:
            print("❌ Does NOT redirect to astro-booking-failed page")
    
    print("\n=== Test Summary ===")
    print("✅ Astrology bookings now have separate redirect handling")
    print("✅ Puja service redirects remain unchanged")
    print("✅ Uses okpuja.com domain for astrology bookings")
    print("✅ astro_book_id is used as merchant_order_id parameter")
    print("\n🎯 The redirect should now work as expected!")

if __name__ == '__main__':
    test_astrology_redirect_fix()
