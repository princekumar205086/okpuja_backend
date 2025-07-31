"""
Minimal Cart Payment Test
Creates a cart with necessary data to have a valid total_price
"""
import os
import django
import sys
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart
from puja.models import Puja, PujaService  # Assuming these exist
from payment.services import PaymentService
from payment.phonepe_v2_simple import PhonePeV2ClientSimplified

User = get_user_model()

def create_minimal_test_cart():
    """Create a minimal cart with valid total_price"""
    print("🛒 Creating minimal test cart...")
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        email="test@okpuja.com",
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '9999999999',
            'is_verified': True
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    print(f"✅ User: {user.email}")
    
    # Try to find an existing puja service or create a simple one
    try:
        # First check if we have any puja services
        puja_service = PujaService.objects.first()
        
        if not puja_service:
            # Try to create a minimal puja and service
            puja = Puja.objects.create(
                name="Test Puja",
                description="Test puja for payment testing",
                category="test",
                price=Decimal('100.00')
            )
            
            puja_service = PujaService.objects.create(
                puja=puja,
                name="Basic Test Service",
                description="Basic test service",
                price=Decimal('100.00')
            )
        
        print(f"✅ Using puja service: {puja_service.name}")
        
        # Create or get cart
        cart, created = Cart.objects.get_or_create(
            user=user,
            defaults={'puja_service': puja_service}
        )
        
        if not created and not cart.puja_service:
            cart.puja_service = puja_service
            cart.save()
        
        print(f"✅ Cart created: {cart.id}")
        print(f"   Total Price: ₹{cart.total_price}")
        
        return cart
        
    except Exception as e:
        print(f"⚠️  Could not create puja service: {e}")
        print("   Creating cart without puja service (will need manual total_price)")
        
        # Create a simple cart and manually set some data
        cart = Cart.objects.create(user=user)
        
        # Since we can't easily create the full puja structure,
        # let's check if we can override total_price in the model
        print(f"✅ Cart created: {cart.id}")
        print(f"   Total Price: ₹{cart.total_price}")
        
        return cart

def test_cart_payment_flow():
    """Test payment creation from a cart"""
    print("\n💳 Testing cart payment flow...")
    
    try:
        cart = create_minimal_test_cart()
        
        if cart.total_price <= 0:
            print("⚠️  Cart has zero total_price, cannot create payment")
            print("   This indicates missing puja services or packages in the database")
            return False
        
        # Test payment creation through service
        service = PaymentService()
        
        # Create payment from cart
        print(f"   Creating payment for cart {cart.id} (₹{cart.total_price})")
        
        # Initialize PhonePe client
        client = PhonePeV2ClientSimplified(env="sandbox")
        
        # Create payment object manually since we don't have the full cart flow
        from payment.models import Payment, PaymentStatus, PaymentMethod
        
        payment = Payment.objects.create(
            user=cart.user,
            cart=cart,
            amount=cart.total_price,  # This should work now
            currency='INR',
            method=PaymentMethod.PHONEPE,
            status=PaymentStatus.PENDING
        )
        
        print(f"✅ Payment created: {payment.id}")
        print(f"   Amount: ₹{payment.amount}")
        print(f"   Transaction ID: {payment.transaction_id}")
        
        # Test payment initiation
        response = client.initiate_payment(payment)
        
        if response.get('success'):
            print(f"✅ Payment initiated successfully!")
            print(f"   Payment URL: {response.get('payment_url')}")
            return True
        else:
            print(f"❌ Payment initiation failed: {response.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Cart payment flow error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Minimal Cart Payment Test...")
    
    success = test_cart_payment_flow()
    
    print("\n" + "=" * 40)
    print(f"📊 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("   1. Check if puja.models has Puja and PujaService models")
        print("   2. Ensure the database has some test puja services")
        print("   3. Consider running: python manage.py shell")
        print("      and manually creating test data")
        print("   4. Use the simple payment test instead: python tests/test_simple_payment.py")
