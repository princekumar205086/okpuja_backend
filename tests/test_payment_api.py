"""
Simple API Test Script for PhonePe V2 Payment Integration
Tests the REST API endpoints directly
"""
import requests
import json
from datetime import datetime

class PaymentAPITester:
    """Test the payment API endpoints"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
    
    def login(self, email="test@okpuja.com", password="testpass123"):
        """Login and get authentication token"""
        print("🔐 Logging in...")
        
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login/",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                print(f"✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def test_connectivity(self):
        """Test connectivity endpoint"""
        print("\n🔗 Testing connectivity endpoint...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/payments/payments/test-connectivity/"
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success')}")
                
                for result in data.get('connectivity_results', []):
                    status_icon = "✅" if result.get('status') == 'OK' else "❌"
                    print(f"   {status_icon} {result.get('url')}")
                
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    def test_payment_methods(self):
        """Test payment methods endpoint"""
        print("\n💳 Testing payment methods endpoint...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/payments/payments/methods/"
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success')}")
                
                for method in data.get('methods', []):
                    print(f"   📱 {method.get('name')}: {method.get('description')}")
                
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    def create_test_cart(self):
        """Create a test cart"""
        print("\n🛒 Creating test cart...")
        
        # First get available puja services
        try:
            response = self.session.get(f"{self.base_url}/api/puja/services/")
            
            if response.status_code == 200:
                services = response.json().get('results', [])
                
                if not services:
                    print("   ❌ No puja services available")
                    return None
                
                service = services[0]
                print(f"   Using service: {service.get('name')}")
                
                # Get packages for this service
                service_id = service.get('id')
                packages_response = self.session.get(
                    f"{self.base_url}/api/puja/services/{service_id}/"
                )
                
                if packages_response.status_code == 200:
                    service_detail = packages_response.json()
                    packages = service_detail.get('packages', [])
                    
                    if not packages:
                        print("   ❌ No packages available")
                        return None
                    
                    package = packages[0]
                    print(f"   Using package: {package.get('name')} - ₹{package.get('price')}")
                    
                    # Create cart
                    cart_data = {
                        'service_type': 'PUJA',
                        'puja_service': service_id,
                        'package_id': package.get('id'),
                        'selected_date': '2025-08-01',
                        'selected_time': '10:00 AM'
                    }
                    
                    cart_response = self.session.post(
                        f"{self.base_url}/api/cart/carts/",
                        json=cart_data
                    )
                    
                    if cart_response.status_code == 201:
                        cart = cart_response.json()
                        print(f"   ✅ Cart created: ID {cart.get('id')}, Total: ₹{cart.get('total_price')}")
                        return cart
                    else:
                        print(f"   ❌ Cart creation failed: {cart_response.text}")
                        return None
                else:
                    print(f"   ❌ Failed to get service details: {packages_response.text}")
                    return None
            else:
                print(f"   ❌ Failed to get services: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None
    
    def test_payment_creation(self, cart_id):
        """Test payment creation"""
        print(f"\n💰 Testing payment creation for cart {cart_id}...")
        
        payment_data = {
            'cart_id': cart_id
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/payments/payments/",
                json=payment_data
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"   ✅ Payment created successfully")
                print(f"   Payment ID: {data.get('payment_id')}")
                print(f"   Transaction ID: {data.get('transaction_id')}")
                print(f"   Merchant Transaction ID: {data.get('merchant_transaction_id')}")
                print(f"   Amount: ₹{data.get('amount')}")
                print(f"   Payment URL: {data.get('payment_url')}")
                
                return data
            else:
                print(f"   ❌ Payment creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None
    
    def test_payment_verification(self, payment_id):
        """Test payment verification"""
        print(f"\n🔍 Testing payment verification for payment {payment_id}...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/payments/payments/{payment_id}/verify/"
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Verification completed")
                print(f"   Success: {data.get('success')}")
                print(f"   Payment Status: {data.get('status')}")
                
                return data
            else:
                print(f"   ❌ Verification failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None
    
    def test_webhook_debug(self):
        """Test webhook debug endpoint"""
        print("\n🔔 Testing webhook debug endpoint...")
        
        test_webhook_data = {
            "response": "eyJ0ZXN0IjogInRydWUifQ==",  # base64 for {"test": "true"}
            "merchantTransactionId": "TEST123456"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/payments/webhook/debug/",
                json=test_webhook_data
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Webhook debug successful")
                return True
            else:
                print(f"   ❌ Webhook debug failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    def run_full_test(self):
        """Run complete API test suite"""
        print("🧪 Starting Payment API Test Suite")
        print("=" * 50)
        
        # Step 1: Login
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return
        
        # Step 2: Test connectivity
        connectivity_ok = self.test_connectivity()
        
        # Step 3: Test payment methods
        methods_ok = self.test_payment_methods()
        
        # Step 4: Create test cart
        cart = self.create_test_cart()
        
        # Step 5: Create payment
        payment = None
        if cart:
            payment = self.test_payment_creation(cart.get('id'))
        
        # Step 6: Verify payment
        verification = None
        if payment:
            verification = self.test_payment_verification(payment.get('payment_id'))
        
        # Step 7: Test webhook debug
        webhook_ok = self.test_webhook_debug()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 API Test Summary:")
        print(f"   Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
        print(f"   Payment Methods: {'✅ PASS' if methods_ok else '❌ FAIL'}")
        print(f"   Cart Creation: {'✅ PASS' if cart else '❌ FAIL'}")
        print(f"   Payment Creation: {'✅ PASS' if payment else '❌ FAIL'}")
        print(f"   Payment Verification: {'✅ PASS' if verification else '❌ FAIL'}")
        print(f"   Webhook Debug: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
        
        if payment and payment.get('payment_url'):
            print(f"\n🔗 Test Payment URL:")
            print(f"   {payment['payment_url']}")
            print("   Open this URL in browser to complete test payment")

if __name__ == "__main__":
    tester = PaymentAPITester()
    tester.run_full_test()
