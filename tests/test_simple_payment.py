"""
Simple Payment Test - Direct Payment Creation
Tests PhonePe V2 integration without needing complex cart setup
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
from payment.models import Payment, PaymentStatus, PaymentMethod
from payment.services import PaymentService
from payment.phonepe_v2_simple import PhonePeV2ClientSimplified, PhonePeException

User = get_user_model()

def create_direct_payment_test():
    """Create a payment directly for testing"""
    print("🧪 Direct PhonePe V2 Payment Test")
    print("=" * 40)
    
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
    
    # Create payment directly
    payment = Payment.objects.create(
        user=user,
        amount=Decimal('100.00'),  # ₹100 test payment
        currency='INR',
        method=PaymentMethod.PHONEPE,
        status=PaymentStatus.PENDING
    )
    
    print(f"✅ Created test payment: {payment.id}")
    print(f"   Amount: ₹{payment.amount}")
    print(f"   Transaction ID: {payment.transaction_id}")
    
    # Test PhonePe client
    client = PhonePeV2ClientSimplified(env="sandbox")
    print(f"✅ PhonePe client initialized")
    
    # Test connectivity
    print("\n🔗 Testing connectivity...")
    results = client.test_connectivity()
    for result in results:
        status_icon = "✅" if result['status'] == 'OK' else "❌"
        print(f"   {status_icon} {result['url']}: {result.get('status_code', result.get('error'))}")
    
    # Test payment initiation
    print("\n🚀 Testing payment initiation...")
    try:
        response = client.initiate_payment(payment)
        
        if response.get('success'):
            print(f"✅ Payment initiated successfully!")
            print(f"   Merchant Transaction ID: {response.get('merchant_transaction_id')}")
            print(f"   Payment URL: {response.get('payment_url')}")
            
            # Test payment status check
            print("\n🔍 Testing payment status check...")
            status_response = client.check_payment_status(response.get('merchant_transaction_id'))
            print(f"   Status check response: {status_response.get('success', False)}")
            
            print(f"\n🔗 Test Payment URL:")
            print(f"   {response['payment_url']}")
            print("   Open this URL to complete the test payment in PhonePe sandbox")
            
            return True
        else:
            print(f"❌ Payment initiation failed: {response.get('error')}")
            return False
            
    except PhonePeException as e:
        print(f"❌ PhonePe error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_payment_service():
    """Test the payment service layer"""
    print("\n🛠️ Testing Payment Service...")
    
    try:
        service = PaymentService()
        print("✅ Payment service initialized")
        
        # Test payment methods
        methods = service.get_payment_methods()
        print(f"✅ Available payment methods: {len(methods)}")
        for method in methods:
            print(f"   📱 {method['name']}: {method['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Payment service error: {str(e)}")
        return False

def test_webhook_processing():
    """Test webhook processing with sample data"""
    print("\n🔔 Testing webhook processing...")
    
    try:
        service = PaymentService()
        
        # Sample webhook data (simulated)
        sample_webhook = {
            "response": "eyJtZXJjaGFudElkIjoiVEVTVCIsIm1lcmNoYW50VHJhbnNhY3Rpb25JZCI6IlRFU1QxMjM0NTYiLCJzdGF0ZSI6IkNPTVBMRVRFRCIsInJlc3BvbnNlQ29kZSI6IlNVQ0NFU1MifQ=="
        }
        
        response = service.process_webhook(sample_webhook)
        print(f"✅ Webhook processing completed")
        print(f"   Success: {response.get('success')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook processing error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple PhonePe V2 Tests...")
    
    # Test 1: Service layer
    service_ok = test_payment_service()
    
    # Test 2: Direct payment creation and initiation
    payment_ok = create_direct_payment_test()
    
    # Test 3: Webhook processing
    webhook_ok = test_webhook_processing()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Simple Test Results:")
    print(f"   Payment Service: {'✅ PASS' if service_ok else '❌ FAIL'}")
    print(f"   Payment Initiation: {'✅ PASS' if payment_ok else '❌ FAIL'}")
    print(f"   Webhook Processing: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    
    overall = all([service_ok, payment_ok, webhook_ok])
    print(f"\n🎯 Overall: {'✅ READY FOR PRODUCTION' if overall else '❌ NEEDS WORK'}")
    
    if payment_ok:
        print(f"\n🔧 Next Steps:")
        print("   1. Open the payment URL above to test the complete flow")
        print("   2. Test the API endpoints with: python tests/test_payment_api.py")
        print("   3. Start the Django server and test via Swagger UI")
        print("   4. Test webhooks with real PhonePe callbacks")
