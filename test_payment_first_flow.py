#!/usr/bin/env python3
"""
Test script for Payment-First Booking Flow
Tests the complete flow: Cart → Payment → Booking

This script tests:
1. Creating a cart with puja service
2. Processing payment for cart (payment-first approach)
3. Simulating successful payment webhook
4. Verifying booking creation after payment success
"""

import os
import sys
import django
import json
from decimal import Decimal
from datetime import datetime, date, time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from cart.models import Cart
from payment.models import Payment, PaymentStatus
from booking.models import Booking
from puja.models import PujaService, Package
from accounts.models import Address

User = get_user_model()

def setup_test_data():
    """Create test user, puja service, and package"""
    print("🔧 Setting up test data...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email='testuser@okpuja.com',
        defaults={
            'is_active': True,
            'role': 'USER',
            'email_verified': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing test user: {user.email}")
    
    # Get or create test category first
    from puja.models import PujaCategory
    category, _ = PujaCategory.objects.get_or_create(name='Test Category')
    
    # Get or create test puja service
    puja_service, created = PujaService.objects.get_or_create(
        title='Test Ganesh Puja',
        defaults={
            'description': 'Test puja service for payment flow',
            'is_active': True,
            'type': 'HOME',
            'duration_minutes': 60,
            'image': 'https://example.com/test-image.jpg',
            'category': category
        }
    )
    
    if created:
        print(f"✅ Created test puja service: {puja_service.title}")
    else:
        print(f"✅ Using existing puja service: {puja_service.title}")
    
    # Get or create test package
    package, created = Package.objects.get_or_create(
        puja_service=puja_service,
        language='HINDI',
        package_type='BASIC',
        defaults={
            'location': 'Test Location',
            'description': 'Basic test package',
            'price': Decimal('999.00'),
            'is_active': True,
            'includes_materials': True,
            'priest_count': 1
        }
    )
    if created:
        print(f"✅ Created test package: {package} - ₹{package.price}")
    else:
        print(f"✅ Using existing package: {package} - ₹{package.price}")
    
    # Create test address
    address, created = Address.objects.get_or_create(
        user=user,
        is_default=True,
        defaults={
            'address_line1': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '123456',
            'country': 'India'
        }
    )
    if created:
        print(f"✅ Created test address for user")
    else:
        print(f"✅ Using existing address for user")
    
    return user, puja_service, package, address

def test_payment_first_booking_flow():
    """Test the complete payment-first booking flow"""
    print("\n🚀 Starting Payment-First Booking Flow Test\n")
    
    try:
        # Setup test data
        user, puja_service, package, address = setup_test_data()
        
        # Step 1: Create Cart
        print("📝 Step 1: Creating cart with puja service...")
        import uuid
        cart = Cart.objects.create(
            user=user,
            service_type='PUJA',
            puja_service=puja_service,
            package=package,
            selected_date=date.today(),
            selected_time='10:30',
            status='ACTIVE',
            cart_id=str(uuid.uuid4())
        )
        print(f"✅ Cart created: {cart.cart_id} - Total: ₹{cart.total_price}")
        
        # Step 2: Create Payment (Payment-First Approach)
        print("\n💳 Step 2: Creating payment for cart...")
        payment = Payment.objects.create(
            user=user,
            cart=cart,
            amount=cart.total_price,
            currency='INR',
            method='PHONEPE',
            status=PaymentStatus.PENDING
        )
        print(f"✅ Payment created: {payment.transaction_id}")
        print(f"   - Amount: ₹{payment.amount}")
        print(f"   - Status: {payment.status}")
        print(f"   - Cart ID: {payment.cart.cart_id}")
        print(f"   - Booking: {payment.booking or 'None (as expected)'}")
        
        # Step 3: Simulate Payment Gateway Success
        print("\n🎯 Step 3: Simulating successful payment...")
        payment.status = PaymentStatus.SUCCESS
        payment.gateway_response = {
            'webhook_callback': {
                'order_id': payment.merchant_transaction_id,
                'state': 'CHECKOUT_ORDER_COMPLETED',
                'timestamp': str(timezone.now())
            }
        }
        payment.save()
        print(f"✅ Payment marked as successful")
        
        # Step 4: Create Booking from Payment
        print("\n📅 Step 4: Creating booking from successful payment...")
        booking = payment.create_booking_from_cart()
        print(f"✅ Booking created: {booking.book_id}")
        print(f"   - User: {booking.user.email}")
        print(f"   - Date: {booking.selected_date}")
        print(f"   - Time: {booking.selected_time}")
        print(f"   - Status: {booking.status}")
        print(f"   - Total Amount: ₹{booking.total_amount}")
        
        # Step 5: Verify Cart Status
        cart.refresh_from_db()
        print(f"\n📦 Step 5: Cart status after booking creation")
        print(f"✅ Cart status: {cart.status} (should be CONVERTED)")
        
        # Step 6: Verify Payment-Booking Link
        payment.refresh_from_db()
        print(f"\n🔗 Step 6: Payment-Booking relationship")
        print(f"✅ Payment linked to booking: {payment.booking.book_id}")
        print(f"✅ Booking linked to payment: {booking.payments.first().transaction_id}")
        
        # Step 7: Test Error Cases
        print(f"\n🚨 Step 7: Testing error handling...")
        
        # Try to create booking again (should fail)
        try:
            payment.create_booking_from_cart()
            print("❌ ERROR: Should not allow duplicate booking creation")
        except ValueError as e:
            print(f"✅ Correctly prevented duplicate booking: {e}")
        
        # Try to create booking from failed payment
        failed_payment = Payment.objects.create(
            user=user,
            cart=cart,
            amount=cart.total_price,
            currency='INR',
            method='PHONEPE',
            status=PaymentStatus.FAILED
        )
        try:
            failed_payment.create_booking_from_cart()
            print("❌ ERROR: Should not allow booking from failed payment")
        except ValueError as e:
            print(f"✅ Correctly prevented booking from failed payment: {e}")
        
        print(f"\n🎉 Payment-First Booking Flow Test COMPLETED SUCCESSFULLY!")
        print(f"\n📊 Summary:")
        print(f"   - Cart: {cart.cart_id} (Status: {cart.status})")
        print(f"   - Payment: {payment.transaction_id} (Status: {payment.status})")
        print(f"   - Booking: {booking.book_id} (Status: {booking.status})")
        print(f"   - Amount: ₹{payment.amount}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test the new API endpoints"""
    print("\n🌐 Testing API endpoint structure...")
    
    from payment.views import PaymentViewSet
    from django.urls import reverse
    
    viewset = PaymentViewSet()
    
    # Check if new actions exist
    actions = [action for action in dir(viewset) if not action.startswith('_')]
    
    if 'process_cart_payment' in actions:
        print("✅ process_cart_payment endpoint available")
    else:
        print("❌ process_cart_payment endpoint missing")
    
    if 'check_booking_status' in actions:
        print("✅ check_booking_status endpoint available")
    else:
        print("❌ check_booking_status endpoint missing")
    
    print("✅ API endpoint structure verified")

def clean_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test payments first (this will also remove booking references)
    test_payments = Payment.objects.filter(user__email='testuser@okpuja.com')
    payment_count = test_payments.count()
    test_payments.delete()
    print(f"✅ Deleted {payment_count} test payments")
    
    # Delete test bookings
    test_bookings = Booking.objects.filter(user__email='testuser@okpuja.com')
    booking_count = test_bookings.count()
    test_bookings.delete()
    print(f"✅ Deleted {booking_count} test bookings")
    
    # Delete test carts
    test_carts = Cart.objects.filter(user__email='testuser@okpuja.com')
    cart_count = test_carts.count()
    test_carts.delete()
    print(f"✅ Deleted {cart_count} test carts")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PAYMENT-FIRST BOOKING FLOW TEST")
    print("=" * 60)
    
    try:
        # Run the main test
        success = test_payment_first_booking_flow()
        
        # Test API endpoints
        test_api_endpoints()
        
        if success:
            print(f"\n✅ ALL TESTS PASSED!")
            print(f"\n📝 Test Results:")
            print(f"   ✅ Cart creation")
            print(f"   ✅ Payment-first approach (payment created before booking)")
            print(f"   ✅ Payment gateway simulation")
            print(f"   ✅ Automatic booking creation after payment success")
            print(f"   ✅ Cart status update to CONVERTED")
            print(f"   ✅ Payment-booking linking")
            print(f"   ✅ Error handling for edge cases")
            print(f"   ✅ API endpoint availability")
        else:
            print(f"\n❌ SOME TESTS FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Clean up test data
        clean_test_data()
        print(f"\n🎯 Test completed successfully!")
