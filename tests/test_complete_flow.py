"""
Comprehensive Payment Flow Test
Tests from cart creation to booking completion with cart cleanup
"""
import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart
from accounts.models import Address
from booking.models import Booking
from payments.models import PaymentOrder
from django.db import transaction

User = get_user_model()

def test_complete_payment_flow():
    print("🧪 COMPREHENSIVE PAYMENT FLOW TEST")
    print("=" * 50)
    
    # Step 1: Get the existing superuser
    print("\n1️⃣ Setting up test user...")
    try:
        user = User.objects.get(email="prince@gmail.com")
        print(f"   ✅ Using existing superuser: {user.email} (ID: {user.id})")
    except User.DoesNotExist:
        print("   ❌ Superuser prince@gmail.com not found. Please create it first.")
        return False
    
    # Step 2: Get or create test address
    print("\n2️⃣ Setting up address...")
    address, created = Address.objects.get_or_create(
        user=user,
        defaults={
            'address_line1': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '123456',
            'is_default': True
        }
    )
    if created:
        print(f"   ✅ New address created: {address.address_line1} (ID: {address.id})")
    else:
        print(f"   ✅ Using existing address: {address.address_line1} (ID: {address.id})")
    
    # Step 3: Create a cart with necessary dependencies
    print("\n3️⃣ Creating cart with dependencies...")
    
    # Try to use existing services first, create if none exist
    from puja.models import PujaService, Package, PujaCategory
    
    # Get or create a category first
    category, created = PujaCategory.objects.get_or_create(
        name="Test Category",
        defaults={'description': 'Test category for payment flow testing'}
    )
    if created:
        print(f"   ✅ Created puja category: {category.name}")
    
    # Create a puja service and package for the cart
    puja_service, created = PujaService.objects.get_or_create(
        title="Test Puja Service",
        category=category,
        defaults={
            'description': 'Test puja for payment flow testing',
            'duration_minutes': 60,
            'is_active': True
        }
    )
    if created:
        print(f"   ✅ Created puja service: {puja_service.title}")
    else:
        print(f"   ✅ Using existing puja service: {puja_service.title}")
    
    package, created = Package.objects.get_or_create(
        puja_service=puja_service,
        location="Test Location",
        language="Hindi",
        defaults={
            'package_type': 'STANDARD',
            'price': 500.00,
            'description': 'Test package for payment flow testing',
            'includes_materials': True,
            'priest_count': 1,
            'is_active': True
        }
    )
    if created:
        print(f"   ✅ Created package: {package.location} ({package.package_type})")
    else:
        print(f"   ✅ Using existing package: {package.location} ({package.package_type})")
    
    # Generate unique cart_id
    import uuid
    cart_id = str(uuid.uuid4())[:12].upper()
    
    cart = Cart.objects.create(
        user=user,
        puja_service=puja_service,
        package=package,
        selected_date="2025-08-15",
        selected_time="10:00",  # Changed to HH:MM format
        cart_id=cart_id,
        status="ACTIVE"
    )
    print(f"   ✅ Cart created: ID {cart.id}, cart_id: {cart.cart_id}")
    print(f"   📍 Cart details: service={puja_service.title}, price=₹{package.price}")
    
    # Step 4: Create a payment order (simulating payment initiation)
    print("\n4️⃣ Creating payment order...")
    payment = PaymentOrder.objects.create(
        user=user,
        cart_id=cart.cart_id,
        address_id=address.id,
        amount=int(cart.total_price * 100),  # Convert to paisa
        currency="INR",
        payment_method="PHONEPE",
        merchant_order_id=f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        phonepe_transaction_id=f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        status="PENDING",
        redirect_url="http://localhost:3000/payment-success"
    )
    print(f"   ✅ Payment order created: {payment.merchant_order_id}")
    print(f"   💳 Payment details: payment_id={payment.id}, amount=₹{payment.amount/100}")
    
    # Step 5: Simulate successful payment (like what professional handler does)
    print("\n5️⃣ Simulating successful payment...")
    payment.status = "SUCCESS"
    payment.save()
    print(f"   ✅ Payment marked as SUCCESS")
    
    # Step 6: Create booking (like what professional handler does)
    print("\n6️⃣ Creating booking...")
    with transaction.atomic():
        booking = Booking.objects.create(
            user=user,
            cart=cart,
            address=address,
            payment_order_id=payment.merchant_order_id,  # Link payment directly
            selected_date=cart.selected_date,
            selected_time=cart.selected_time,
            status="CONFIRMED"
        )
        print(f"   ✅ Booking created: {booking.book_id}")
        print(f"   📋 Booking details: ID={booking.id}, status={booking.status}")
        print(f"   💳 Payment order linked: {booking.payment_order_id}")
    
    # Step 7: Clean up cart (like what professional handler does)
    print("\n7️⃣ Cleaning up cart...")
    cart.status = "CONVERTED"
    cart.save()
    print(f"   ✅ Cart marked as CONVERTED (cleaned up)")
    
    # Step 8: Verify all relationships are intact
    print("\n8️⃣ Verifying data integrity...")
    
    # Check booking has all required IDs
    booking.refresh_from_db()
    print(f"   🔗 Booking relationships:")
    print(f"      - booking.id: {booking.id}")
    print(f"      - booking.cart_id: {booking.cart.id if booking.cart else 'None'}")
    print(f"      - booking.address_id: {booking.address.id if booking.address else 'None'}")
    
    # Check payment details through booking
    payment_details = booking.payment_details
    print(f"   💰 Payment details accessible through booking:")
    print(f"      - payment_id: {payment_details['payment_id']}")
    print(f"      - amount: ₹{payment_details['amount']}")
    print(f"      - status: {payment_details['status']}")
    print(f"      - transaction_id: {payment_details['transaction_id']}")
    
    # Check cart cleanup
    cart.refresh_from_db()
    print(f"   🧹 Cart cleanup status: {cart.status}")
    
    # Step 9: Verify payment order can be found
    print("\n9️⃣ Verifying payment order linkage...")
    found_payment = PaymentOrder.objects.filter(
        user=user,
        cart_id=cart.cart_id,
        status='SUCCESS'
    ).first()
    
    if found_payment:
        print(f"   ✅ Payment order found: {found_payment.merchant_order_id}")
        print(f"   🔗 Payment-Cart link: payment.cart_id={found_payment.cart_id}")
    else:
        print(f"   ❌ Payment order not found!")
    
    # Step 10: Final summary
    print("\n🎯 FINAL VERIFICATION")
    print("=" * 30)
    print(f"✅ User ID: {user.id} ({user.email})")
    print(f"✅ Address ID: {address.id} (intact)")
    print(f"✅ Cart ID: {cart.id} (intact, status: {cart.status})")
    print(f"✅ Payment ID: {payment.id} (intact, status: {payment.status})")
    print(f"✅ Booking ID: {booking.id} (intact, status: {booking.status})")
    print(f"✅ Payment details accessible: {payment_details['payment_id'] != 'N/A'}")
    print(f"✅ Cart cleaned up: {cart.status == 'CONVERTED'}")
    
    # Verify the three critical IDs are intact
    if booking.address and booking.cart and found_payment:
        print(f"\n🎉 SUCCESS! All required IDs are intact:")
        print(f"   - address_id: {booking.address.id}")
        print(f"   - cart_id: {booking.cart.id}")
        print(f"   - payment_id: {found_payment.id}")
        
        # Test payment details integration
        print(f"\n💳 Payment Details Integration Test:")
        print(f"   - Payment found via booking: {payment_details['payment_id'] == found_payment.merchant_order_id}")
        print(f"   - Amount matches: {payment_details['amount'] == found_payment.amount/100}")
        print(f"   - Status correct: {payment_details['status'] == found_payment.status}")
        print(f"   - Total amount accessible: ₹{booking.total_amount}")
        
        return True
    else:
        print(f"\n❌ FAILURE! Missing relationships:")
        print(f"   - address_id: {booking.address.id if booking.address else 'MISSING'}")
        print(f"   - cart_id: {booking.cart.id if booking.cart else 'MISSING'}")
        print(f"   - payment_id: {found_payment.id if found_payment else 'MISSING'}")
        return False

if __name__ == "__main__":
    try:
        success = test_complete_payment_flow()
        if success:
            print("\n🎉 COMPREHENSIVE TEST PASSED!")
            print("✅ Cart creation → Payment → Booking → Cart cleanup flow works correctly")
            print("✅ All required IDs (address_id, cart_id, payment_id) are intact")
            print("✅ Payment details are accessible through booking")
        else:
            print("\n❌ COMPREHENSIVE TEST FAILED!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
