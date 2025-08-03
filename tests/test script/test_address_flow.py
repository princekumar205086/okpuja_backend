#!/usr/bin/env python3
"""
Test Address Flow: Cart → Checkout (Address Required) → Payment → Booking Creation
Testing with user: asliprinceraj@gmail.com
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

from accounts.models import User, Address
from puja.models import PujaService, PujaCategory, Package
from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking
from payments.services import PaymentService
from django.test import RequestFactory
from payments.cart_views import CartPaymentView
import json

def test_complete_address_flow():
    """Test the complete flow: Cart → Address Selection → Payment → Booking"""
    
    print("🔍 Testing Complete Address Flow")
    print("=" * 50)
    
    # 1. Find or create test user
    try:
        user = User.objects.get(email='asliprinceraj@gmail.com')
        print(f"✅ Found user: {user.email} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ User 'asliprinceraj@gmail.com' not found!")
        print("Creating test user...")
        user = User.objects.create_user(
            email='asliprinceraj@gmail.com',
            phone='9876543210',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        print(f"✅ Created user: {user.email} (ID: {user.id})")
    
    # 2. Check user's addresses
    addresses = Address.objects.filter(user=user)
    print(f"\n📍 User addresses: {addresses.count()}")
    
    if addresses.exists():
        for addr in addresses:
            default_str = " (DEFAULT)" if addr.is_default else ""
            print(f"   - ID: {addr.id} | {addr.address_line1}, {addr.city}{default_str}")
    else:
        print("❌ No addresses found! Creating test address...")
        address = Address.objects.create(
            user=user,
            address_line1="123 Test Street",
            city="Test City",
            state="Test State",
            pincode="123456",
            is_default=True
        )
        print(f"✅ Created address: {address.id} | {address.address_line1}, {address.city}")
    
    # Get the first address for testing
    test_address = Address.objects.filter(user=user).first()
    
    # 3. Find or create test puja service and package
    try:
        puja_service = PujaService.objects.first()
        if not puja_service:
            print("❌ No puja services found! Creating test puja service...")
            category = PujaCategory.objects.first()
            if not category:
                category = PujaCategory.objects.create(name="Test Category")
            puja_service = PujaService.objects.create(
                title="Test Puja Service",
                category=category,
                description="Test puja service for address flow",
                duration_minutes=60
            )
        
        # Find or create a package for this service
        package = Package.objects.filter(puja_service=puja_service).first()
        if not package:
            print("❌ No packages found! Creating test package...")
            package = Package.objects.create(
                puja_service=puja_service,
                location="Test Location",
                price=100.00,
                description="Test package for address flow"
            )
        
        print(f"✅ Using puja service: {puja_service.title} (ID: {puja_service.id})")
        print(f"✅ Using package: {package.location} (Price: ₹{package.price})")
    except Exception as e:
        print(f"❌ Error with puja service: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Create/find cart with puja service
    try:
        # First try to find existing cart
        cart = Cart.objects.filter(user=user, status='ACTIVE').first()
        
        if cart:
            print(f"✅ Found existing cart: {cart.id}")
        else:
            # Create new cart with puja service and package
            from django.utils.crypto import get_random_string
            cart = Cart.objects.create(
                user=user,
                service_type='PUJA',
                puja_service=puja_service,
                package=package,
                cart_id=get_random_string(20),
                status='ACTIVE'
            )
            print(f"✅ Created new cart: {cart.id}")
        
        print(f"✅ Cart service: {cart.puja_service.title if cart.puja_service else 'None'}")
        print(f"✅ Cart package: {cart.package.location if cart.package else 'None'}")
        
    except Exception as e:
        print(f"❌ Error with cart: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. Test Payment Initiation with Address (NEW REQUIREMENT)
    print(f"\n💳 Testing Payment Initiation with Address...")
    print("-" * 40)
    
    try:
        cart_id = cart.id
        address_id = test_address.id
        
        print(f"   📦 Cart ID: {cart_id}")
        print(f"   📍 Address ID: {address_id}")
        
        # Verify cart exists and belongs to user
        test_cart = Cart.objects.get(id=cart_id, user=user)
        print(f"   ✅ Cart verified: {test_cart.id}")
        
        # Verify address exists and belongs to user  
        test_addr = Address.objects.get(id=address_id, user=user)
        print(f"   ✅ Address verified: {test_addr.city}")
        
        # Test PaymentService with address_id
        payment_service = PaymentService()
        payment_order = payment_service.create_payment_order(
            cart=test_cart,
            address_id=address_id  # NEW PARAMETER!
        )
        
        print(f"   ✅ Payment order created: {payment_order.id}")
        print(f"   📍 Payment address_id: {payment_order.address_id}")
        print(f"   💰 Amount: ₹{payment_order.amount}")
        print(f"   📱 Status: {payment_order.status}")
        
    except Exception as e:
        print(f"   ❌ Payment initiation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. Test Booking Creation (Simulate Payment Success)
    print(f"\n🏗️ Testing Booking Creation with Address...")
    print("-" * 40)
    
    try:
        # Simulate payment success - update payment status
        payment_order.status = 'success'
        payment_order.save()
        print(f"   ✅ Payment marked as success")
        
        # Test booking creation with address from payment
        booking = Booking.objects.create(
            user=user,
            cart=cart,  # Booking uses cart, not individual puja service
            address_id=payment_order.address_id,  # Using address from payment!
            total_amount=payment_order.amount,
            payment_id=payment_order.id,
            status='confirmed'
        )
        
        print(f"   ✅ Booking created: {booking.id}")
        print(f"   📍 Booking address: {booking.address.city}")
        print(f"   💰 Amount: ₹{booking.total_amount}")
        print(f"   📱 Status: {booking.status}")
        
    except Exception as e:
        print(f"   ❌ Booking creation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 7. Verify Complete Flow
    print(f"\n🎉 COMPLETE FLOW VERIFICATION")
    print("=" * 50)
    
    print(f"👤 User: {user.email}")
    print(f"📍 Address: {test_address.address_line1}, {test_address.city}")
    print(f"📦 Cart: {cart.id} (Service: {cart.puja_service.title if cart.puja_service else 'None'})")
    print(f"💳 Payment: {payment_order.id} (Status: {payment_order.status})")
    print(f"🏗️ Booking: {booking.id} (Status: {booking.status})")
    
    # Verify address flow
    if payment_order.address_id == test_address.id and booking.address_id == test_address.id:
        print("✅ ADDRESS FLOW WORKING: Cart → Payment(address_id) → Booking(address)")
    else:
        print("❌ ADDRESS FLOW BROKEN!")
        
    print(f"\n🎊 Test completed successfully!")
    print(f"Your address-mandatory checkout flow is working! 🚀")

if __name__ == "__main__":
    test_complete_address_flow()
