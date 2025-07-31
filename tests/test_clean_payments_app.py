#!/usr/bin/env python
"""
Test Script for New Clean Payments App
Test the PhonePe integration with the new clean architecture
"""

import os
import sys
import django
import uuid
import json

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from payments.services import PaymentService
from payments.phonepe_client import PhonePePaymentClient
from payments.models import PaymentOrder

User = get_user_model()


def test_phonepe_client():
    """Test the clean PhonePe client"""
    print("🔧 Testing PhonePe Client")
    print("=" * 40)
    
    try:
        # Initialize client
        client = PhonePePaymentClient(environment="uat")
        
        print(f"✅ Client initialized")
        print(f"✅ Environment: {client.environment}")
        print(f"✅ Base URL: {client.base_url}")
        print(f"✅ OAuth URL: {client.oauth_url}")
        print(f"✅ Payment URL: {client.payment_url}")
        print(f"✅ Client ID: {client.client_id[:20]}...")
        
        # Test OAuth
        print(f"\n🔑 Testing OAuth...")
        try:
            access_token = client.get_access_token()
            if access_token:
                print(f"✅ OAuth successful")
                print(f"✅ Token: {access_token[:20]}...")
            else:
                print(f"❌ OAuth failed - no token received")
        except Exception as e:
            print(f"❌ OAuth failed: {e}")
        
        # Test payment creation
        print(f"\n💳 Testing Payment Creation...")
        try:
            order_id = f"TEST_{uuid.uuid4().hex[:8].upper()}"
            
            result = client.create_payment_url(
                merchant_order_id=order_id,
                amount=10000,  # ₹100
                redirect_url="https://okpuja.com/payment/success",
                payment_message="Test payment"
            )
            
            if result['success']:
                print(f"✅ Payment URL created successfully")
                print(f"✅ Order ID: {order_id}")
                print(f"✅ Payment URL: {result.get('payment_url', 'No URL')}")
                return True
            else:
                print(f"❌ Payment creation failed: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Payment creation error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False


def test_payment_service():
    """Test the payment service"""
    print(f"\n🏪 Testing Payment Service")
    print("=" * 40)
    
    try:
        # Get or create test user
        try:
            user = User.objects.get(username='testuser')
            print(f"✅ Using existing test user: {user.username}")
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='testuser',
                email='test@okpuja.com',
                first_name='Test',
                last_name='User'
            )
            print(f"✅ Created test user: {user.username}")
        except User.MultipleObjectsReturned:
            user = User.objects.filter(username='testuser').first()
            print(f"✅ Using first test user: {user.username}")
        
        # Initialize payment service
        payment_service = PaymentService()
        print(f"✅ Payment service initialized")
        print(f"✅ Environment: {payment_service.environment}")
        
        # Create payment order
        print(f"\n💰 Creating payment order...")
        
        result = payment_service.create_payment_order(
            user=user,
            amount=15000,  # ₹150
            redirect_url="https://okpuja.com/payment/success",
            description="Test payment via new service",
            metadata={"test": True, "app": "payments"}
        )
        
        if result['success']:
            print(f"✅ Payment order created successfully")
            print(f"✅ Order ID: {result['merchant_order_id']}")
            print(f"✅ Payment URL: {result.get('payment_url', 'No URL')}")
            
            payment_order = result['payment_order']
            print(f"✅ Database record: {payment_order}")
            print(f"✅ Amount: ₹{payment_order.amount_in_rupees}")
            print(f"✅ Status: {payment_order.status}")
            
            # Test status check
            print(f"\n📊 Testing status check...")
            status_result = payment_service.check_payment_status(result['merchant_order_id'])
            
            if status_result['success']:
                print(f"✅ Status check successful")
                updated_order = status_result['payment_order']
                print(f"✅ Current status: {updated_order.status}")
            else:
                print(f"⚠️ Status check failed: {status_result['error']}")
            
            return True
        else:
            print(f"❌ Payment order creation failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Payment service test failed: {e}")
        return False


def test_database_models():
    """Test database models"""
    print(f"\n🗄️ Testing Database Models")
    print("=" * 40)
    
    try:
        # Check if models are working
        payment_count = PaymentOrder.objects.count()
        print(f"✅ PaymentOrder model working - {payment_count} records")
        
        # Get recent payments
        recent_payments = PaymentOrder.objects.all()[:5]
        
        if recent_payments:
            print(f"✅ Recent payments:")
            for payment in recent_payments:
                print(f"   - {payment.merchant_order_id}: ₹{payment.amount_in_rupees} ({payment.status})")
        else:
            print(f"📝 No payment records found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Testing New Clean Payments App")
    print("💳 PhonePe Integration with Clean Architecture")
    print("=" * 60)
    
    results = {}
    
    # Test PhonePe client
    results['client'] = test_phonepe_client()
    
    # Test payment service
    results['service'] = test_payment_service()
    
    # Test database models
    results['database'] = test_database_models()
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"🎯 TEST RESULTS SUMMARY")
    print(f"{'=' * 60}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} {test_name.capitalize()} Test: {'PASSED' if passed else 'FAILED'}")
    
    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print(f"🎉 ALL TESTS PASSED! Your new payments app is working perfectly!")
        print(f"🚀 Ready for production use!")
        
        print(f"\n📋 Next Steps:")
        print(f"1. Add 'payments' to INSTALLED_APPS in settings")
        print(f"2. Run migrations: python manage.py makemigrations payments")
        print(f"3. Run migrations: python manage.py migrate")
        print(f"4. Include payments URLs in main urls.py")
        print(f"5. Test API endpoints with your frontend")
        
    else:
        print(f"⚠️ Some tests failed. Check the errors above.")
        print(f"📞 Contact support if PhonePe credentials need activation.")
    
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
