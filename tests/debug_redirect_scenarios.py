#!/usr/bin/env python3
"""
Simulate real PhonePe redirect scenarios to debug the issue
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
from unittest.mock import patch
import json

def test_various_phonepe_redirect_scenarios():
    """Test different PhonePe redirect parameter formats"""
    
    print("🧪 Testing Various PhonePe Redirect Scenarios")
    print("=" * 50)
    
    # Get a recent astrology payment order
    payment_order = PaymentOrder.objects.filter(
        metadata__booking_type='astrology',
        status='SUCCESS'
    ).first()
    
    if not payment_order:
        print("❌ No successful astrology payment found. Creating test payment...")
        return
    
    print(f"📦 Using payment order: {payment_order.merchant_order_id}")
    print(f"   Status: {payment_order.status}")
    print(f"   Booking type: {payment_order.metadata.get('booking_type')}")
    
    # Check if astrology booking exists
    astrology_booking = AstrologyBooking.objects.filter(payment_id=str(payment_order.id)).first()
    if astrology_booking:
        print(f"   ✅ Astrology booking exists: {astrology_booking.astro_book_id}")
    else:
        print(f"   ❌ No astrology booking found")
    
    factory = RequestFactory()
    handler = PaymentRedirectHandler()
    
    # Test different parameter formats that PhonePe might send
    test_scenarios = [
        {
            'name': 'Standard merchantOrderId',
            'params': {
                'merchantOrderId': payment_order.merchant_order_id,
                'transactionId': 'TEST_TXN_123'
            }
        },
        {
            'name': 'Alternative merchantId',
            'params': {
                'merchantId': payment_order.merchant_order_id,
                'transactionId': 'TEST_TXN_123'
            }
        },
        {
            'name': 'Alternative orderId',
            'params': {
                'orderId': payment_order.merchant_order_id,
                'paymentId': 'TEST_TXN_123'
            }
        },
        {
            'name': 'Alternative order_id',
            'params': {
                'order_id': payment_order.merchant_order_id,
                'transaction_id': 'TEST_TXN_123'
            }
        },
        {
            'name': 'Alternative transactionId only',
            'params': {
                'transactionId': payment_order.merchant_order_id
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔬 Scenario {i}: {scenario['name']}")
        print(f"   Parameters: {scenario['params']}")
        
        # Create mock request
        request = factory.get('/payments/redirect/', scenario['params'])
        
        # Mock the payment status check
        with patch('payments.services.PaymentService.check_payment_status') as mock_status:
            mock_status.return_value = {
                'success': True,
                'payment_order': payment_order,
                'transaction_id': scenario['params'].get('transactionId', 'TEST_TXN_123')
            }
            
            try:
                response = handler.get(request)
                redirect_url = response.url
                print(f"   ✅ Redirect URL: {redirect_url}")
                
                # Analyze the redirect
                if 'astro-booking-success' in redirect_url and 'astro_book_id=' in redirect_url:
                    print(f"   ✅ CORRECT: Astrology booking success redirect")
                elif 'confirmbooking?status=completed' in redirect_url:
                    print(f"   ❌ INCORRECT: Puja booking redirect (this is the bug!)")
                else:
                    print(f"   ⚠️ OTHER: Unknown redirect format")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")

def test_missing_booking_scenario():
    """Test what happens when astrology booking doesn't exist"""
    print(f"\n\n🔬 Testing Missing Astrology Booking Scenario")
    print("=" * 50)
    
    # Create a payment order without astrology booking
    test_payment = PaymentOrder.objects.create(
        merchant_order_id='TEST_MISSING_BOOKING',
        user_id=1,
        amount=1999,
        status='SUCCESS',
        metadata={
            'booking_type': 'astrology',
            'frontend_redirect_url': 'https://www.okpuja.com',
            'service_id': 7,
            'user_id': 2
        }
    )
    
    print(f"📦 Created test payment: {test_payment.merchant_order_id}")
    print(f"   No astrology booking exists for this payment")
    
    factory = RequestFactory()
    handler = PaymentRedirectHandler()
    
    request = factory.get('/payments/redirect/', {
        'merchantOrderId': test_payment.merchant_order_id,
        'transactionId': 'TEST_TXN_MISSING'
    })
    
    with patch('payments.services.PaymentService.check_payment_status') as mock_status:
        mock_status.return_value = {
            'success': True,
            'payment_order': test_payment,
            'transaction_id': 'TEST_TXN_MISSING'
        }
        
        try:
            response = handler.get(request)
            redirect_url = response.url
            print(f"   Redirect URL: {redirect_url}")
            
            if 'astro-booking-success' in redirect_url:
                print(f"   ✅ Still redirects to astrology success (webhook creates booking)")
            elif 'confirmbooking?status=completed' in redirect_url:
                print(f"   ❌ Falls back to puja booking redirect")
            else:
                print(f"   ⚠️ Other redirect: {redirect_url}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Clean up
    test_payment.delete()

def test_actual_production_url():
    """Test the actual URL from the browser"""
    print(f"\n\n🌐 Testing Actual Production-like Scenario")
    print("=" * 50)
    
    # The URL you showed: https://www.okpuja.com/confirmbooking?status=completed
    # This suggests the redirect is bypassing the astrology logic entirely
    
    # Let's check what happens with an empty or malformed request
    factory = RequestFactory()
    handler = PaymentRedirectHandler()
    
    # Test empty parameters (like what might happen if PhonePe sends no params)
    empty_request = factory.get('/payments/redirect/', {})
    
    print("🔬 Testing empty redirect parameters...")
    try:
        response = handler.get(empty_request)
        redirect_url = response.url
        print(f"   Empty params redirect: {redirect_url}")
        
        if 'confirmbooking?status=completed' in redirect_url:
            print(f"   ✅ This explains the issue! Empty params = generic success redirect")
            
    except Exception as e:
        print(f"   ❌ Error with empty params: {e}")

if __name__ == '__main__':
    test_various_phonepe_redirect_scenarios()
    test_missing_booking_scenario()
    test_actual_production_url()
