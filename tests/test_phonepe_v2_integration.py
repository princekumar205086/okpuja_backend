"""
PhonePe V2 Payment Integration Test Suite
Comprehensive tests for the complete payment flow
"""
import os
import django
import sys
import json
import requests
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase
from cart.models import Cart
from payment.models import Payment, PaymentStatus
from payment.services import PaymentService
from payment.phonepe_v2_simple import PhonePeV2ClientSimplified, PhonePeException

User = get_user_model()

class PhonePeV2IntegrationTests:
    """Integration tests for PhonePe V2 payment flow"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.payment_service = PaymentService()
        self.phonepe_client = PhonePeV2ClientSimplified(env="sandbox")
        
    def setup_test_data(self):
        """Setup test user and cart"""
        print("🔧 Setting up test data...")
        
        # Create test user
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
            print(f"✅ Created test user: {user.email}")
        else:
            print(f"✅ Using existing test user: {user.email}")
        
        # Create test cart (assuming you have puja services)
        from puja.models import PujaService, Package
        
        try:
            puja_service = PujaService.objects.first()
            package = Package.objects.first()
            
            if not puja_service or not package:
                print("❌ No puja services or packages found. Creating dummy cart...")
                
                # Create a simple cart without checking for puja service
                cart, created = Cart.objects.get_or_create(
                    user=user,
                    status='ACTIVE',
                    defaults={
                        'selected_date': '2025-08-01',
                        'selected_time': '10:00 AM',
                        'service_type': 'PUJA'
                    }
                )
                
                # Manually set a total price for testing
                cart.save()
                
                print(f"✅ {'Created' if created else 'Using'} dummy test cart: {cart.id}")
                return user, cart
            
            cart, created = Cart.objects.get_or_create(
                user=user,
                status='ACTIVE',
                defaults={
                    'puja_service': puja_service,
                    'package': package,
                    'selected_date': '2025-08-01',
                    'selected_time': '10:00 AM',
                    'service_type': 'PUJA'
                }
            )
            
            print(f"✅ {'Created' if created else 'Using'} test cart: {cart.id}")
            print(f"   Cart total: ₹{cart.total_price}")
            
            return user, cart
            
        except Exception as e:
            print(f"❌ Error creating cart: {str(e)}")
            return user, None
    
    def test_connectivity(self):
        """Test PhonePe API connectivity"""
        print("\n🔗 Testing PhonePe API connectivity...")
        
        try:
            results = self.phonepe_client.test_connectivity()
            
            for result in results:
                status_icon = "✅" if result['status'] == 'OK' else "❌"
                print(f"   {status_icon} {result['url']}: {result.get('status_code', result.get('error'))}")
            
            return all(r['status'] == 'OK' for r in results)
            
        except Exception as e:
            print(f"❌ Connectivity test failed: {str(e)}")
            return False
    
    def test_oauth_token(self):
        """Test OAuth2 token generation"""
        print("\n🔐 Testing OAuth2 token generation...")
        
        try:
            token = self.phonepe_client.get_access_token()
            
            if token:
                print(f"✅ OAuth2 token generated successfully")
                print(f"   Token: {token[:20]}...")
                return True
            else:
                print("❌ No token received")
                return False
                
        except PhonePeException as e:
            print(f"❌ OAuth2 failed: {str(e)}")
            return False
    
    def test_payment_creation(self, user, cart):
        """Test payment creation from cart"""
        print("\n💳 Testing payment creation...")
        
        if not cart:
            print("❌ No cart available for testing")
            return None
        
        try:
            payment = self.payment_service.create_payment_from_cart(cart, user)
            
            print(f"✅ Payment created successfully")
            print(f"   Payment ID: {payment.id}")
            print(f"   Transaction ID: {payment.transaction_id}")
            print(f"   Amount: ₹{payment.amount}")
            print(f"   Status: {payment.status}")
            
            return payment
            
        except Exception as e:
            print(f"❌ Payment creation failed: {str(e)}")
            return None
    
    def test_payment_initiation(self, payment):
        """Test payment initiation with PhonePe"""
        print("\n🚀 Testing payment initiation...")
        
        if not payment:
            print("❌ No payment available for testing")
            return None
        
        try:
            response = self.payment_service.initiate_payment(payment)
            
            if response.get('success'):
                print(f"✅ Payment initiated successfully")
                print(f"   Merchant Transaction ID: {response.get('merchant_transaction_id')}")
                print(f"   Payment URL: {response.get('payment_url')}")
                
                # Refresh payment from database
                payment.refresh_from_db()
                print(f"   Updated Status: {payment.status}")
                
                return response
            else:
                print(f"❌ Payment initiation failed: {response.get('error')}")
                return None
                
        except PhonePeException as e:
            print(f"❌ PhonePe error: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Payment initiation failed: {str(e)}")
            return None
    
    def test_payment_status_check(self, payment):
        """Test payment status verification"""
        print("\n🔍 Testing payment status check...")
        
        if not payment or not payment.merchant_transaction_id:
            print("❌ No payment or merchant transaction ID available")
            return None
        
        try:
            response = self.payment_service.verify_payment(payment.merchant_transaction_id)
            
            print(f"✅ Status check completed")
            print(f"   Success: {response.get('success')}")
            print(f"   Response: {json.dumps(response, indent=2)}")
            
            # Refresh payment
            payment.refresh_from_db()
            print(f"   Current Status: {payment.status}")
            
            return response
            
        except Exception as e:
            print(f"❌ Status check failed: {str(e)}")
            return None
    
    def test_api_endpoints(self):
        """Test REST API endpoints"""
        print("\n🌐 Testing REST API endpoints...")
        
        # Test connectivity endpoint
        try:
            response = requests.get(f"{self.base_url}/api/payments/payments/test-connectivity/")
            print(f"   Connectivity API: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Connectivity endpoint working")
            else:
                print("   ❌ Connectivity endpoint failed")
                
        except Exception as e:
            print(f"   ❌ API test failed: {str(e)}")
    
    def test_webhook_processing(self):
        """Test webhook processing"""
        print("\n🔔 Testing webhook processing...")
        
        # Sample webhook data (base64 encoded)
        sample_webhook = {
            "response": "eyJtZXJjaGFudElkIjoiVEFKRk9PVFdFQVJVQVRfMjUwMzAzMTgzODI3MzU1Njg5NDQzOCIsIm1lcmNoYW50VHJhbnNhY3Rpb25JZCI6IlRYMjAyNTA3MjYxNjQzMTJBQkNERUYiLCJzdGF0ZSI6IkNPTVBMRVRFRCIsInJlc3BvbnNlQ29kZSI6IlNVQ0NFU1MifQ=="
        }
        
        try:
            response = self.payment_service.process_webhook(sample_webhook)
            
            print(f"✅ Webhook processing completed")
            print(f"   Success: {response.get('success')}")
            print(f"   Response: {json.dumps(response, indent=2)}")
            
            return response
            
        except Exception as e:
            print(f"❌ Webhook processing failed: {str(e)}")
            return None
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting PhonePe V2 Integration Test Suite")
        print("=" * 50)
        
        # Setup
        user, cart = self.setup_test_data()
        
        # Test 1: Connectivity
        connectivity_ok = self.test_connectivity()
        
        # Test 2: OAuth
        oauth_ok = self.test_oauth_token()
        
        # Test 3: Payment Creation
        payment = self.test_payment_creation(user, cart)
        
        # Test 4: Payment Initiation
        initiation_response = self.test_payment_initiation(payment)
        
        # Test 5: Status Check
        status_response = self.test_payment_status_check(payment)
        
        # Test 6: API Endpoints
        self.test_api_endpoints()
        
        # Test 7: Webhook Processing
        webhook_response = self.test_webhook_processing()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        print(f"   Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
        print(f"   OAuth: {'✅ PASS' if oauth_ok else '❌ FAIL'}")
        print(f"   Payment Creation: {'✅ PASS' if payment else '❌ FAIL'}")
        print(f"   Payment Initiation: {'✅ PASS' if initiation_response else '❌ FAIL'}")
        print(f"   Status Check: {'✅ PASS' if status_response else '❌ FAIL'}")
        print(f"   Webhook Processing: {'✅ PASS' if webhook_response else '❌ FAIL'}")
        
        # Overall result
        all_passed = all([
            connectivity_ok, oauth_ok, payment, 
            initiation_response, status_response, webhook_response
        ])
        
        print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        if initiation_response and initiation_response.get('payment_url'):
            print(f"\n🔗 Test Payment URL:")
            print(f"   {initiation_response['payment_url']}")
            print("   Open this URL to complete the test payment")

if __name__ == "__main__":
    tester = PhonePeV2IntegrationTests()
    tester.run_all_tests()
