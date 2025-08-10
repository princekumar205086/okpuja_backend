#!/usr/bin/env python3
"""
Test script to verify astrology booking redirect fix
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

import requests
import json
from payments.models import PaymentOrder

BASE_URL = 'http://127.0.0.1:8000'

def test_login_and_booking():
    """Test login and astrology booking creation"""
    
    print('🔐 Testing login with provided credentials...')
    login_data = {
        'email': 'asliprinceraj@gmail.com',
        'password': 'Testpass@123'
    }

    try:
        response = requests.post(f'{BASE_URL}/api/auth/login/', json=login_data)
        print(f'Login response: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ Login successful!')
            token = data['access']
            print(f'Token: {token[:50]}...')
        elif response.status_code == 401:
            # Try alternative password
            login_data['password'] = 'testpass123'
            response = requests.post(f'{BASE_URL}/api/auth/login/', json=login_data)
            print(f'Alternative password response: {response.status_code}')
            if response.status_code == 200:
                data = response.json()
                print('✅ Login successful with alternative password!')
                token = data['access']
            else:
                print('❌ Both passwords failed')
                print(response.text)
                return
        else:
            print('❌ Login failed')
            print(response.text)
            return

        print(f'\n📋 Available astrology services:')
        # Get astrology services
        response = requests.get(f'{BASE_URL}/api/astrology/services/')
        if response.status_code == 200:
            services = response.json()  # Direct list, not wrapped in data
            for service in services[:3]:  # Show first 3 services
                print(f'  - Service {service["id"]}: {service["title"]} (₹{service["price"]})')
            
            if services:
                service_id = services[0]['id']
                print(f'\n💳 Creating astrology booking with payment for service {service_id}...')
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                booking_data = {
                    'service': service_id,
                    'language': 'Hindi',
                    'preferred_date': '2025-08-15',
                    'preferred_time': '14:00:00',
                    'birth_place': 'Delhi, India',
                    'birth_date': '1995-05-15',
                    'birth_time': '08:30:00',
                    'gender': 'MALE',
                    'questions': 'Test astrology booking for redirect fix',
                    'contact_email': 'asliprinceraj@gmail.com',
                    'contact_phone': '9123456789',
                    'redirect_url': 'https://www.okpuja.com'
                }
                
                response = requests.post(
                    f'{BASE_URL}/api/astrology/bookings/book-with-payment/',
                    headers=headers,
                    json=booking_data
                )
                
                print(f'Booking response: {response.status_code}')
                if response.status_code == 201:
                    data = response.json()
                    print('✅ Booking created successfully!')
                    merchant_order_id = data["data"]["payment"]["merchant_order_id"]
                    print(f'Merchant Order ID: {merchant_order_id}')
                    print(f'Payment URL: {data["data"]["payment"]["payment_url"][:80]}...')
                    
                    # Check payment order metadata
                    try:
                        payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
                        print(f'\n🔍 Payment order metadata:')
                        print(json.dumps(payment_order.metadata, indent=2))
                        
                        # Simulate successful payment and test redirect logic
                        print(f'\n🧪 Testing redirect logic...')
                        test_redirect_logic(payment_order)
                        
                    except PaymentOrder.DoesNotExist:
                        print(f'❌ Payment order {merchant_order_id} not found in database')
                    
                else:
                    print('❌ Booking failed')
                    print(response.text)
        else:
            print('❌ Failed to get services')
            print(response.text)

    except Exception as e:
        print(f'❌ Error: {e}')


def test_redirect_logic(payment_order):
    """Test the redirect logic with a payment order"""
    from payments.redirect_handler import PaymentRedirectHandler
    from django.test import RequestFactory
    from unittest.mock import patch
    
    # Update payment status to success for testing
    payment_order.status = 'SUCCESS'
    payment_order.save()
    
    # Create mock request
    factory = RequestFactory()
    request = factory.get('/payments/redirect/', {
        'merchantOrderId': payment_order.merchant_order_id,
        'transactionId': 'TEST_TXN_12345'
    })
    
    # Mock the payment status check to return success
    with patch('payments.services.PaymentService.check_payment_status') as mock_status:
        mock_status.return_value = {
            'success': True,
            'payment_order': payment_order,
            'transaction_id': 'TEST_TXN_12345'
        }
        
        handler = PaymentRedirectHandler()
        response = handler.get(request)
        
        redirect_url = response.url
        print(f'Generated redirect URL: {redirect_url}')
        
        # Check if it's the correct format
        if 'astro-booking-success' in redirect_url and 'astro_book_id=' in redirect_url:
            print('✅ CORRECT: Redirects to astro-booking-success with astro_book_id parameter')
        elif 'confirmbooking?status=completed' in redirect_url:
            print('❌ INCORRECT: Still redirecting to puja booking page')
        else:
            print(f'⚠️ UNEXPECTED: Unknown redirect format: {redirect_url}')


if __name__ == '__main__':
    test_login_and_booking()
