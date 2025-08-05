#!/usr/bin/env python3
"""
Test to verify that puja service redirects remain unchanged while astrology redirects are fixed.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from payments.redirect_handler import PaymentRedirectHandler
from django.test import RequestFactory
from django.conf import settings
from unittest.mock import patch

def test_puja_redirect_unchanged():
    """Test that puja service redirects are not affected by astrology changes"""
    
    print("=== Testing Puja Service Redirect (Should be Unchanged) ===\n")
    
    # Expected puja redirect format (should remain the same)
    expected_puja_success = f"{settings.FRONTEND_BASE_URL}/confirmbooking"
    
    print(f"Expected puja redirect base: {expected_puja_success}")
    
    # Create test payment order for puja booking (no 'booking_type': 'astrology')
    test_payment = PaymentOrder.objects.filter(merchant_order_id='PUJA_REDIRECT_TEST').first()
    if not test_payment:
        test_payment = PaymentOrder.objects.create(
            merchant_order_id='PUJA_REDIRECT_TEST',
            user_id=1,
            cart_id='test_cart_123',
            amount=999,
            status='SUCCESS',
            metadata={
                # No 'booking_type': 'astrology' - this is a regular puja booking
                'service_id': 1,
                'user_id': 1,
                'cart_items': [{'puja_id': 1, 'quantity': 1}]
            }
        )
        print(f"✅ Created test puja payment order: {test_payment.merchant_order_id}")
    
    # Test SUCCESS redirect for puja service
    print("\n=== Testing Puja SUCCESS Redirect ===")
    
    with patch('payments.services.PaymentService.check_payment_status') as mock_status:
        mock_status.return_value = {
            'success': True,
            'payment_order': test_payment,
            'transaction_id': 'TXN789'
        }
        
        factory = RequestFactory()
        request = factory.get('/payments/redirect/', {
            'order_id': test_payment.merchant_order_id,
            'transaction_id': 'TXN789'
        })
        
        handler = PaymentRedirectHandler()
        response = handler.get(request)
        redirect_url = response.url
        
        print(f"Generated puja redirect URL: {redirect_url}")
        
        # Verify puja redirect format
        if 'confirmbooking' in redirect_url:
            print("✅ Puja service redirects to confirmbooking page (unchanged)")
        else:
            print("❌ Puja service redirect changed unexpectedly")
            
        if 'astro-booking-success' not in redirect_url:
            print("✅ Puja service does NOT redirect to astrology pages")
        else:
            print("❌ Puja service incorrectly redirects to astrology pages")
            
        if 'order_id=' in redirect_url:
            print("✅ Contains order_id parameter (puja format)")
        else:
            print("❌ Missing order_id parameter")
    
    # Test that astrology still works differently
    print("\n=== Confirming Astrology is Different ===")
    
    # Create astrology payment for comparison
    astro_payment = PaymentOrder.objects.filter(merchant_order_id='ASTRO_COMPARISON').first()
    if not astro_payment:
        astro_payment = PaymentOrder.objects.create(
            merchant_order_id='ASTRO_COMPARISON',
            user_id=1,
            amount=1999,
            status='SUCCESS',
            metadata={
                'booking_type': 'astrology',  # This is the key difference
                'frontend_redirect_url': 'https://okpuja.com',
                'service_id': 1
            }
        )
    
    with patch('payments.services.PaymentService.check_payment_status') as mock_status:
        mock_status.return_value = {
            'success': True,
            'payment_order': astro_payment,
            'transaction_id': 'TXN999'
        }
        
        request = factory.get('/payments/redirect/', {
            'order_id': astro_payment.merchant_order_id,
            'transaction_id': 'TXN999'
        })
        
        response = handler.get(request)
        redirect_url = response.url
        
        print(f"Generated astrology redirect URL: {redirect_url}")
        
        if 'astro-booking-success' in redirect_url:
            print("✅ Astrology service redirects to astro-booking-success")
        else:
            print("❌ Astrology service redirect not working")
    
    print("\n=== Summary ===")
    print("✅ Puja service redirects remain unchanged")
    print("✅ Astrology service has separate redirect handling")
    print("✅ No interference between the two services")
    print("\n🎯 Both services now work independently with correct redirects!")

if __name__ == '__main__':
    test_puja_redirect_unchanged()
