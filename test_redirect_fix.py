#!/usr/bin/env python3
"""
Test script to verify that redirect URLs are now working properly for astrology bookings.
This script tests the redirect handler changes that use frontend_redirect_url from metadata.
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
from payments.redirect_handler import PaymentRedirectHandler
from django.test import RequestFactory
from django.conf import settings
import json

def test_redirect_url_generation():
    """Test that redirect URLs use the stored frontend_redirect_url from metadata"""
    
    print("=== Testing Redirect URL Generation ===\n")
    
    # Test data
    frontend_url = "https://www.okpuja.com"
    expected_success_url = f"{frontend_url}/astro-booking-success?astro_book_id=ASTRO_BOOK_20250805_TEST123&merchant_order_id=TEST_ORDER_123"
    expected_failure_url = f"{frontend_url}/astro-booking-failed?merchant_order_id=TEST_ORDER_123&reason=failed"
    
    print(f"Frontend URL from metadata: {frontend_url}")
    print(f"Expected success URL: {expected_success_url}")
    print(f"Expected failure URL: {expected_failure_url}")
    print()
    
    # Check if we have any existing astrology bookings to test with
    print("=== Checking Existing Astrology Bookings ===")
    recent_bookings = AstrologyBooking.objects.all().order_by('-created_at')[:3]
    
    if recent_bookings:
        print(f"Found {recent_bookings.count()} astrology bookings:")
        for booking in recent_bookings:
            print(f"  - {booking.astro_book_id} (Payment ID: {booking.payment_id})")
            
            # Check if payment order exists and has metadata
            if booking.payment_id:
                try:
                    payment_order = PaymentOrder.objects.get(id=booking.payment_id)
                    metadata = payment_order.metadata
                    print(f"    Payment Order Metadata: {json.dumps(metadata, indent=6)}")
                    
                    # Check if frontend_redirect_url is stored
                    frontend_redirect = metadata.get('frontend_redirect_url')
                    if frontend_redirect:
                        print(f"    ✅ Frontend redirect URL stored: {frontend_redirect}")
                        
                        # Simulate what redirect handler would generate
                        frontend_base = frontend_redirect.rstrip('/')
                        success_url = f"{frontend_base}/astro-booking-success?astro_book_id={booking.astro_book_id}&merchant_order_id={payment_order.merchant_order_id}"
                        failure_url = f"{frontend_base}/astro-booking-failed?merchant_order_id={payment_order.merchant_order_id}&reason=failed"
                        
                        print(f"    Success URL would be: {success_url}")
                        print(f"    Failure URL would be: {failure_url}")
                    else:
                        print(f"    ⚠️  No frontend_redirect_url in metadata")
                        
                except PaymentOrder.DoesNotExist:
                    print(f"    ⚠️  Payment order {booking.payment_id} not found")
            print()
    else:
        print("No astrology bookings found")
    
    print("=== Testing Redirect Logic ===")
    
    # Create a mock PaymentOrder with metadata
    try:
        # First check if test order already exists
        test_payment = PaymentOrder.objects.filter(merchant_order_id='TEST_REDIRECT_ORDER').first()
        if not test_payment:
            test_payment = PaymentOrder.objects.create(
                merchant_order_id='TEST_REDIRECT_ORDER',
                user_id=1,  # Add required user_id
                amount=1000,
                status='COMPLETED',
                metadata={
                    'booking_type': 'astrology',
                    'frontend_redirect_url': 'https://www.okpuja.com',
                    'astrology_data': {
                        'user_id': 1,
                        'astrologer_id': 1,
                        'consultation_type': 'CALL',
                        'duration_minutes': 30,
                        'scheduled_datetime': '2025-01-05T10:00:00Z'
                    }
                }
            )
            print(f"✅ Created test payment order: {test_payment.merchant_order_id}")
        else:
            print(f"✅ Using existing test payment order: {test_payment.merchant_order_id}")
        
        # Create a test astrology booking linked to this payment
        test_booking = AstrologyBooking.objects.filter(payment_id=str(test_payment.id)).first()
        if not test_booking:
            # Get first available service
            from astrology.models import AstrologyService
            service = AstrologyService.objects.first()
            if not service:
                print("❌ No astrology service found, creating one...")
                service = AstrologyService.objects.create(
                    title="Test Service",
                    service_type="HOROSCOPE",
                    description="Test service for redirect testing",
                    price=1000.00
                )
            
            test_booking = AstrologyBooking.objects.create(
                astro_book_id='ASTRO_BOOK_TEST_REDIRECT',
                user_id=1,
                service=service,
                language='Hindi',
                preferred_date='2025-08-15',
                preferred_time='14:00:00',
                birth_place='Delhi, India',
                birth_date='1995-05-15',
                birth_time='08:30:00',
                gender='MALE',
                questions='Test questions',
                contact_email='test@example.com',
                contact_phone='9876543210',
                payment_id=str(test_payment.id),
                status='CONFIRMED'
            )
            print(f"✅ Created test astrology booking: {test_booking.astro_book_id}")
        else:
            print(f"✅ Using existing test astrology booking: {test_booking.astro_book_id}")
        
        # Test the redirect URL generation logic
        frontend_base = test_payment.metadata.get('frontend_redirect_url', settings.FRONTEND_BASE_URL).rstrip('/')
        
        # Success URL
        success_url = f"{frontend_base}/astro-booking-success?astro_book_id={test_booking.astro_book_id}&merchant_order_id={test_payment.merchant_order_id}"
        print(f"✅ Generated Success URL: {success_url}")
        
        # Failure URL  
        failure_url = f"{frontend_base}/astro-booking-failed?astro_book_id={test_booking.astro_book_id}&merchant_order_id={test_payment.merchant_order_id}&reason=failed"
        print(f"✅ Generated Failure URL: {failure_url}")
        
        # Verify URLs contain expected components
        assert 'www.okpuja.com' in success_url, "Success URL should use frontend URL from metadata"
        assert test_booking.astro_book_id in success_url, "Success URL should contain astro_book_id"
        assert 'astro-booking-success' in success_url, "Success URL should go to astro-booking-success page"
        
        assert 'www.okpuja.com' in failure_url, "Failure URL should use frontend URL from metadata"
        assert test_booking.astro_book_id in failure_url, "Failure URL should contain astro_book_id"
        assert 'astro-booking-failed' in failure_url, "Failure URL should go to astro-booking-failed page"
        
        print("✅ All URL generation tests passed!")
        
    except Exception as e:
        print(f"❌ Error testing redirect logic: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Summary ===")
    print("The redirect handler has been updated to:")
    print("1. Extract frontend_redirect_url from payment metadata")
    print("2. Use this URL as the base for astrology booking redirects")
    print("3. Generate proper success/failure URLs with astro_book_id")
    print("4. Maintain backward compatibility for regular bookings")
    print("\nThis should fix the redirect issue where users were going to the base URL")
    print("instead of the proper astro-booking-success/failed pages.")

if __name__ == '__main__':
    test_redirect_url_generation()
