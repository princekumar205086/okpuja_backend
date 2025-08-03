#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Demonstrate the FIXED payment verification system
This test shows the complete payment flow and verifies that:
1. Failed payments NEVER create bookings
2. Success payments ALWAYS create bookings
3. The system properly verifies payment status before booking creation
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

from accounts.models import User, Address
from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking
from payments.professional_redirect_handler import ProfessionalPaymentRedirectHandler
from puja.models import PujaService, Package
from django.http import HttpRequest
import json
from datetime import datetime

def comprehensive_payment_test():
    print("🚀 COMPREHENSIVE PAYMENT SYSTEM TEST")
    print("=" * 70)
    print("📋 Testing the FIXED payment verification system")
    print("🎯 Objective: Ensure failed payments NEVER create bookings")
    print("=" * 70)
    
    # Get test data
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ Test user not found")
        return
    
    address = Address.objects.filter(user=user).first()
    
    # Get a puja service and package for the cart
    puja_service = PujaService.objects.first()
    if not puja_service:
        print("❌ No puja service found")
        return
        
    package = Package.objects.filter(puja_service=puja_service).first()
    if not package:
        print("❌ No package found")
        return
    
    # Create a fresh cart for testing
    new_cart = Cart.objects.create(
        user=user,
        cart_id=f"TEST_CART_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        service_type='PUJA',
        puja_service=puja_service,
        package=package,
        selected_date='2025-08-05',
        selected_time='10:00'
    )
    
    print(f"✅ User: {user.email}")
    print(f"✅ Address: {address.id} - {address.city if address else 'None'}")
    print(f"✅ Test Cart: {new_cart.cart_id}")
    print(f"💰 Cart Amount: ₹{new_cart.total_price}")
    print(f"🔧 Service: {puja_service.title}")
    print(f"📦 Package: {package.get_package_type_display()} - ₹{package.price}")
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'FAILED Payment',
            'status': 'FAILED',
            'expected_redirect': 'failedbooking',
            'should_create_booking': False
        },
        {
            'name': 'CANCELLED Payment', 
            'status': 'CANCELLED',
            'expected_redirect': 'failedbooking',
            'should_create_booking': False
        },
        {
            'name': 'PENDING Payment',
            'status': 'PENDING', 
            'expected_redirect': 'payment-pending',
            'should_create_booking': False
        },
        {
            'name': 'SUCCESS Payment',
            'status': 'SUCCESS',
            'expected_redirect': 'confirmbooking',
            'should_create_booking': True
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📝 TEST {i}: {scenario['name']}")
        print("-" * 40)
        
        # Create payment order with specific status
        payment = PaymentOrder.objects.create(
            user=user,
            merchant_order_id=f"TEST_{scenario['status']}_{datetime.now().strftime('%H%M%S')}_{i:02d}",
            amount=new_cart.total_price,
            status=scenario['status'],
            cart_id=new_cart.cart_id,
            address_id=address.id if address else None
        )
        
        print(f"💳 Payment Created: {payment.merchant_order_id}")
        print(f"📊 Status: {payment.status}")
        
        # Count bookings before handler
        bookings_before = Booking.objects.filter(cart=new_cart).count()
        print(f"📦 Bookings before: {bookings_before}")
        
        # Test the professional handler
        try:
            handler = ProfessionalPaymentRedirectHandler()
            request = HttpRequest()
            request.method = 'GET'
            request.user = user
            request.META = {'HTTP_USER_AGENT': 'Test Agent'}
            
            response = handler.get(request)
            
            # Count bookings after handler
            bookings_after = Booking.objects.filter(cart=new_cart).count()
            booking_created = bookings_after > bookings_before
            
            print(f"📦 Bookings after: {bookings_after}")
            print(f"🔄 Redirect: {response.status_code} -> {response.url}")
            
            # Verify results
            redirect_correct = scenario['expected_redirect'] in response.url
            booking_behavior_correct = booking_created == scenario['should_create_booking']
            
            test_passed = redirect_correct and booking_behavior_correct
            
            result = {
                'scenario': scenario['name'],
                'status': scenario['status'],
                'redirect_correct': redirect_correct,
                'booking_behavior_correct': booking_behavior_correct,
                'test_passed': test_passed,
                'booking_created': booking_created,
                'expected_booking': scenario['should_create_booking']
            }
            results.append(result)
            
            if test_passed:
                print("✅ PASSED: Correct behavior")
            else:
                print("❌ FAILED: Incorrect behavior")
                if not redirect_correct:
                    print(f"   ⚠️ Expected redirect to contain '{scenario['expected_redirect']}'")
                if not booking_behavior_correct:
                    print(f"   ⚠️ Expected booking creation: {scenario['should_create_booking']}, Got: {booking_created}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                'scenario': scenario['name'],
                'status': scenario['status'], 
                'test_passed': False,
                'error': str(e)
            })
    
    # Cleanup test data
    print(f"\n🧹 Cleaning up test data...")
    PaymentOrder.objects.filter(merchant_order_id__startswith="TEST_").delete()
    Booking.objects.filter(cart=new_cart).delete()
    new_cart.delete()
    print("✅ Cleanup complete")
    
    # Final results summary
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(1 for r in results if r.get('test_passed', False))
    total_tests = len(results)
    
    for result in results:
        status_icon = "✅" if result.get('test_passed', False) else "❌"
        print(f"{status_icon} {result['scenario']}: {result['status']}")
        if 'error' in result:
            print(f"   💥 Error: {result['error']}")
    
    print(f"\n🎯 TEST RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Payment verification system is working correctly!")
        print("✅ Failed payments correctly do NOT create bookings")
        print("✅ Success payments correctly DO create bookings")
    else:
        print("⚠️ Some tests failed. Payment system needs further fixes.")
    
    print("=" * 70)

if __name__ == "__main__":
    comprehensive_payment_test()
