"""
Comprehensive Test for PhonePe V2 Integration (Final Implementation)
Tests the complete payment and refund flow with corrected client and webhook handling
"""
import requests
import json
import time
import uuid
from datetime import datetime, timedelta

class PhonePeV2ComprehensiveTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000/api"
        self.test_user_id = 1
        self.test_cart_id = 1
        self.session = requests.Session()
        
        # Test results
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
    
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        self.results['tests_run'] += 1
        if success:
            self.results['tests_passed'] += 1
            status = "✅ PASSED"
        else:
            self.results['tests_failed'] += 1
            status = "❌ FAILED"
        
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        
        print(result)
        self.results['details'].append(result)
    
    def test_payment_service_integration(self):
        """Test payment service with corrected client"""
        print("\n🔍 Testing Payment Service Integration...")
        
        try:
            # Test data
            test_data = {
                'cart_id': self.test_cart_id,
                'payment_method': 'PHONEPE'
            }
            
            # Create payment via service
            response = self.session.post(
                f"{self.base_url}/payment/payments/",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                payment_id = data.get('id')
                payment_url = data.get('payment_url')
                
                self.log_test(
                    "Payment Service Creation", 
                    True, 
                    f"Payment ID: {payment_id}, URL present: {bool(payment_url)}"
                )
                
                return payment_id
            else:
                self.log_test(
                    "Payment Service Creation", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                return None
                
        except Exception as e:
            self.log_test("Payment Service Creation", False, f"Exception: {str(e)}")
            return None
    
    def test_oauth_token_flow(self):
        """Test OAuth token generation with corrected client"""
        print("\n🔐 Testing OAuth Token Flow...")
        
        try:
            # Import and test the corrected client directly
            import sys, os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
            
            client = PhonePeV2ClientCorrected(env="sandbox")
            
            # Test OAuth token generation
            token_response = client.get_access_token()
            
            if token_response.get('success'):
                token = token_response.get('token')
                expires_at = token_response.get('expires_at')
                
                self.log_test(
                    "OAuth Token Generation", 
                    True, 
                    f"Token obtained, expires at: {expires_at}"
                )
                
                # Test token usage
                headers = client._get_auth_headers()
                self.log_test(
                    "OAuth Token Headers", 
                    'Authorization' in headers, 
                    f"Headers: {list(headers.keys())}"
                )
                
                return True
            else:
                self.log_test(
                    "OAuth Token Generation", 
                    False, 
                    f"Error: {token_response.get('error')}"
                )
                return False
                
        except Exception as e:
            self.log_test("OAuth Token Flow", False, f"Exception: {str(e)}")
            return False
    
    def test_payment_initiation_endpoint(self):
        """Test payment initiation with V2 endpoints"""
        print("\n💳 Testing Payment Initiation Endpoint...")
        
        try:
            from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
            
            client = PhonePeV2ClientCorrected(env="sandbox")
            
            # Test payment initiation
            merchant_order_id = f"TEST_ORDER_{int(time.time())}"
            
            response = client.initiate_payment(
                merchant_transaction_id=merchant_order_id,
                amount=100.00,
                merchant_user_id="test_user_123",
                redirect_url="https://example.com/callback",
                callback_url="https://example.com/webhook"
            )
            
            if response.get('success'):
                data = response.get('data', {})
                payment_url = data.get('payment_url')
                
                self.log_test(
                    "Payment Initiation", 
                    True, 
                    f"Payment URL generated: {bool(payment_url)}"
                )
                
                # Test URL format
                if payment_url and 'phoenixuat.phonepe.com' in payment_url:
                    self.log_test("Payment URL Format", True, "Correct UAT URL")
                else:
                    self.log_test("Payment URL Format", False, f"URL: {payment_url}")
                
                return merchant_order_id
            else:
                self.log_test(
                    "Payment Initiation", 
                    False, 
                    f"Error: {response.get('error')}"
                )
                return None
                
        except Exception as e:
            self.log_test("Payment Initiation Endpoint", False, f"Exception: {str(e)}")
            return None
    
    def test_payment_status_check(self, merchant_order_id):
        """Test payment status check with V2 endpoints"""
        if not merchant_order_id:
            return
            
        print("\n📊 Testing Payment Status Check...")
        
        try:
            from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
            
            client = PhonePeV2ClientCorrected(env="sandbox")
            
            # Test status check
            response = client.check_payment_status(merchant_order_id)
            
            if response.get('success'):
                data = response.get('data', {})
                state = data.get('state')
                
                self.log_test(
                    "Payment Status Check", 
                    True, 
                    f"Status retrieved, state: {state}"
                )
                
                # Check response format
                expected_fields = ['merchantTransactionId', 'state']
                has_fields = all(field in data for field in expected_fields)
                
                self.log_test(
                    "Status Response Format", 
                    has_fields, 
                    f"Has expected fields: {has_fields}"
                )
                
            else:
                self.log_test(
                    "Payment Status Check", 
                    False, 
                    f"Error: {response.get('error')}"
                )
                
        except Exception as e:
            self.log_test("Payment Status Check", False, f"Exception: {str(e)}")
    
    def test_refund_initiation(self):
        """Test refund initiation with V2 endpoints"""
        print("\n💰 Testing Refund Initiation...")
        
        try:
            from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
            
            client = PhonePeV2ClientCorrected(env="sandbox")
            
            # Test refund initiation
            merchant_refund_id = f"REFUND_{int(time.time())}"
            original_order_id = f"ORIGINAL_ORDER_{int(time.time())}"
            
            response = client.initiate_refund(
                merchant_refund_id=merchant_refund_id,
                original_merchant_order_id=original_order_id,
                amount=50.00
            )
            
            if response.get('success'):
                data = response.get('data', {})
                
                self.log_test(
                    "Refund Initiation", 
                    True, 
                    f"Refund initiated: {data.get('merchantRefundId')}"
                )
                
                return merchant_refund_id
            else:
                self.log_test(
                    "Refund Initiation", 
                    False, 
                    f"Error: {response.get('error')}"
                )
                return None
                
        except Exception as e:
            self.log_test("Refund Initiation", False, f"Exception: {str(e)}")
            return None
    
    def test_refund_status_check(self, merchant_refund_id):
        """Test refund status check with V2 endpoints"""
        if not merchant_refund_id:
            return
            
        print("\n📈 Testing Refund Status Check...")
        
        try:
            from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
            
            client = PhonePeV2ClientCorrected(env="sandbox")
            
            # Test refund status check
            response = client.check_refund_status(merchant_refund_id)
            
            if response.get('success'):
                data = response.get('data', {})
                state = data.get('state')
                
                self.log_test(
                    "Refund Status Check", 
                    True, 
                    f"Status retrieved, state: {state}"
                )
                
            else:
                self.log_test(
                    "Refund Status Check", 
                    False, 
                    f"Error: {response.get('error')}"
                )
                
        except Exception as e:
            self.log_test("Refund Status Check", False, f"Exception: {str(e)}")
    
    def test_webhook_validation(self):
        """Test webhook validation logic"""
        print("\n🔗 Testing Webhook Validation...")
        
        try:
            from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
            
            client = PhonePeV2ClientCorrected(env="sandbox")
            
            # Test webhook authorization validation
            username = "test_user"
            password = "test_pass"
            
            # Create proper authorization header
            import hashlib
            auth_string = f"{username}:{password}"
            auth_hash = hashlib.sha256(auth_string.encode()).hexdigest()
            
            is_valid = client.validate_webhook_authorization(auth_hash, username, password)
            
            self.log_test(
                "Webhook Authorization", 
                is_valid, 
                f"Auth validation: {is_valid}"
            )
            
            # Test webhook payload processing
            test_payload = {
                "event": "checkout.order.completed",
                "payload": {
                    "merchantTransactionId": "TEST_TXN_123",
                    "orderId": "ORDER_123",
                    "state": "COMPLETED",
                    "amount": 10000
                }
            }
            
            webhook_info = client.process_webhook_payload(test_payload)
            
            self.log_test(
                "Webhook Payload Processing", 
                webhook_info.get('valid', False), 
                f"Processed: {webhook_info.get('event')}"
            )
            
        except Exception as e:
            self.log_test("Webhook Validation", False, f"Exception: {str(e)}")
    
    def test_webhook_endpoint(self):
        """Test webhook endpoint"""
        print("\n🎯 Testing Webhook Endpoint...")
        
        try:
            # Test webhook endpoint
            webhook_payload = {
                "event": "checkout.order.completed",
                "payload": {
                    "merchantTransactionId": "TEST_WEBHOOK_123",
                    "orderId": "ORDER_WEBHOOK_123",
                    "state": "COMPLETED",
                    "amount": 10000
                }
            }
            
            # Create authorization header
            import hashlib
            auth_string = "webhook_user:webhook_pass"
            auth_hash = hashlib.sha256(auth_string.encode()).hexdigest()
            
            response = self.session.post(
                f"{self.base_url}/payment/webhook/phonepe/v2/",
                json=webhook_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': auth_hash
                }
            )
            
            if response.status_code == 200:
                self.log_test(
                    "Webhook Endpoint", 
                    True, 
                    f"Status: {response.status_code}"
                )
            else:
                self.log_test(
                    "Webhook Endpoint", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
                
        except Exception as e:
            self.log_test("Webhook Endpoint", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting PhonePe V2 Comprehensive Integration Tests...\n")
        
        # Test OAuth flow
        oauth_success = self.test_oauth_token_flow()
        
        # Test payment initiation
        merchant_order_id = self.test_payment_initiation_endpoint()
        
        # Test payment status
        self.test_payment_status_check(merchant_order_id)
        
        # Test refund flow
        merchant_refund_id = self.test_refund_initiation()
        self.test_refund_status_check(merchant_refund_id)
        
        # Test webhook validation
        self.test_webhook_validation()
        
        # Test webhook endpoint
        self.test_webhook_endpoint()
        
        # Test payment service integration
        self.test_payment_service_integration()
        
        # Print final results
        self.print_final_results()
    
    def print_final_results(self):
        """Print final test results"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("="*80)
        
        for detail in self.results['details']:
            print(detail)
        
        print("\n" + "-"*80)
        print(f"📈 SUMMARY:")
        print(f"   Total Tests: {self.results['tests_run']}")
        print(f"   ✅ Passed: {self.results['tests_passed']}")
        print(f"   ❌ Failed: {self.results['tests_failed']}")
        
        success_rate = (self.results['tests_passed'] / self.results['tests_run'] * 100) if self.results['tests_run'] > 0 else 0
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        
        if self.results['tests_failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! PhonePe V2 integration is fully functional.")
        else:
            print(f"\n⚠️  {self.results['tests_failed']} tests failed. Please review the issues above.")
        
        print("="*80)

if __name__ == "__main__":
    tester = PhonePeV2ComprehensiveTest()
    tester.run_all_tests()
