#!/usr/bin/env python3
"""
Production Flow Test for OkPuja Backend
Tests the complete cart -> payment -> booking flow with real production API
"""

import requests
import json
import time
from datetime import datetime, timedelta

class ProductionFlowTest:
    def __init__(self):
        self.base_url = "https://api.okpuja.com/api"
        self.frontend_url = "https://www.okpuja.com"
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'OkPuja-ProductionTest/1.0'
        }
        self.session = requests.Session()
        self.test_credentials = {
            'email': 'asliprinceraj@gmail.com',
            'password': 'Testpass@123'
        }
        self.auth_token = None
        self.test_data = {}
        
    def print_step(self, step_name, emoji="🔍"):
        print(f"\n{'='*20} {step_name} {'='*20}")
        print(f"{emoji} Testing {step_name.lower()}...")
        
    def print_success(self, message):
        print(f"   ✅ {message}")
        
    def print_error(self, message):
        print(f"   ❌ {message}")
        
    def print_info(self, message):
        print(f"   📊 {message}")
        
    def test_authentication(self):
        """Test user authentication"""
        self.print_step("User Authentication", "🔐")
        
        try:
            # Login request
            login_data = {
                'email': self.test_credentials['email'],
                'password': self.test_credentials['password']
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login/",
                json=login_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access' in data:
                    self.auth_token = data['access']
                    self.headers['Authorization'] = f'Bearer {self.auth_token}'
                    self.session.headers.update(self.headers)
                    self.print_success(f"Authentication successful")
                    self.print_info(f"User: {self.test_credentials['email']}")
                    return True
                else:
                    self.print_error(f"No access token in response: {data}")
                    return False
            else:
                self.print_error(f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Authentication error: {str(e)}")
            return False
    
    def test_cart_creation(self):
        """Test cart creation"""
        self.print_step("Cart Creation", "🛒")
        
        try:
            # Get available services first
            services_response = self.session.get(f"{self.base_url}/puja/services/")
            if services_response.status_code != 200:
                self.print_error(f"Failed to get services: {services_response.status_code}")
                return False
                
            services = services_response.json()
            if not services or len(services) == 0:
                self.print_error("No services available")
                return False
                
            # Use first available service
            service = services[0] if isinstance(services, list) else services.get('results', [{}])[0]
            service_id = service['id']
            
            # Create cart
            cart_data = {
                'puja_service': service_id,  # Use puja_service instead of service
                'selected_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'selected_time': '10:00'
            }
            
            response = self.session.post(
                f"{self.base_url}/cart/carts/",
                json=cart_data
            )
            
            if response.status_code == 201:
                cart = response.json()
                self.test_data['cart_id'] = cart['id']
                service_data = cart.get('puja_service') or cart.get('service') or {}
                self.test_data['service_name'] = service_data.get('name', 'N/A')
                self.test_data['total_amount'] = cart['total_amount']
                
                self.print_success(f"Cart created: {cart['id']}")
                self.print_info(f"Service: {service_data.get('name', 'N/A')}")
                self.print_info(f"Total: ₹{cart['total_amount']}")
                self.print_info(f"Date: {cart['selected_date']}")
                self.print_info(f"Time: {cart['selected_time']}")
                return True
            else:
                self.print_error(f"Cart creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Cart creation error: {str(e)}")
            return False
    
    def test_payment_initiation(self):
        """Test payment initiation"""
        self.print_step("Payment Initiation", "💳")
        
        try:
            payment_data = {
                'cart_id': self.test_data['cart_id']
            }
            
            response = self.session.post(
                f"{self.base_url}/payments/create/",
                json=payment_data
            )
            
            if response.status_code == 200:
                payment = response.json()
                self.test_data['payment_id'] = payment.get('payment_id') or payment.get('merchant_order_id')
                self.test_data['payment_url'] = payment.get('payment_url')
                
                self.print_success(f"Payment initiated: {self.test_data['payment_id']}")
                self.print_info(f"Amount: ₹{payment.get('amount', 'N/A')}")
                self.print_info(f"Payment URL available: {'Yes' if payment.get('payment_url') else 'No'}")
                return True
            else:
                self.print_error(f"Payment initiation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Payment initiation error: {str(e)}")
            return False
    
    def test_payment_status(self):
        """Test payment status check"""
        self.print_step("Payment Status Check", "🔍")
        
        try:
            response = self.session.get(
                f"{self.base_url}/payments/status/{self.test_data['payment_id']}/"
            )
            
            if response.status_code == 200:
                status = response.json()
                self.print_success(f"Payment status retrieved")
                self.print_info(f"Status: {status.get('status', 'Unknown')}")
                self.print_info(f"Payment ID: {self.test_data['payment_id']}")
                return True
            else:
                self.print_error(f"Payment status check failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Payment status error: {str(e)}")
            return False
    
    def test_booking_list(self):
        """Test booking list retrieval"""
        self.print_step("Booking List", "📋")
        
        try:
            response = self.session.get(f"{self.base_url}/booking/bookings/")
            
            if response.status_code == 200:
                bookings = response.json()
                booking_count = len(bookings) if isinstance(bookings, list) else len(bookings.get('results', []))
                self.print_success(f"Booking list retrieved")
                self.print_info(f"Total bookings: {booking_count}")
                
                if booking_count > 0:
                    latest_booking = bookings[0] if isinstance(bookings, list) else bookings.get('results', [{}])[0]
                    self.print_info(f"Latest booking: {latest_booking.get('book_id', 'N/A')}")
                    self.print_info(f"Status: {latest_booking.get('status', 'N/A')}")
                
                return True
            else:
                self.print_error(f"Booking list failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Booking list error: {str(e)}")
            return False
    
    def test_services_api(self):
        """Test services API"""
        self.print_step("Services API", "🕉️")
        
        try:
            response = self.session.get(f"{self.base_url}/puja/services/")
            
            if response.status_code == 200:
                services = response.json()
                service_count = len(services) if isinstance(services, list) else len(services.get('results', []))
                self.print_success(f"Services API working")
                self.print_info(f"Total services: {service_count}")
                
                if service_count > 0:
                    first_service = services[0] if isinstance(services, list) else services.get('results', [{}])[0]
                    self.print_info(f"First service: {first_service.get('name', 'N/A')}")
                    self.print_info(f"Price: ₹{first_service.get('price', 'N/A')}")
                
                return True
            else:
                self.print_error(f"Services API failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Services API error: {str(e)}")
            return False
    
    def test_profile_api(self):
        """Test user profile API"""
        self.print_step("User Profile", "👤")
        
        try:
            response = self.session.get(f"{self.base_url}/auth/profile/")
            
            if response.status_code == 200:
                profile = response.json()
                self.print_success(f"Profile retrieved")
                self.print_info(f"Email: {profile.get('email', 'N/A')}")
                self.print_info(f"Name: {profile.get('first_name', '')} {profile.get('last_name', '')}")
                return True
            else:
                self.print_error(f"Profile API failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Profile API error: {str(e)}")
            return False
    
    def test_webhooks_endpoint(self):
        """Test webhooks endpoint accessibility"""
        self.print_step("Webhooks Endpoint", "🔗")
        
        try:
            # Note: We can't actually test webhook processing without PhonePe,
            # but we can check if the endpoint is accessible
            response = requests.get(f"{self.base_url}/payments/webhook/phonepe/")
            
            # Webhook should return 405 (Method Not Allowed) for GET, which means it exists
            if response.status_code == 405:
                self.print_success("Webhook endpoint is accessible")
                self.print_info("Endpoint responds to requests (405 for GET is expected)")
                return True
            elif response.status_code == 404:
                self.print_error("Webhook endpoint not found")
                return False
            else:
                self.print_success(f"Webhook endpoint responds with status: {response.status_code}")
                return True
                
        except Exception as e:
            self.print_error(f"Webhook endpoint error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all production tests"""
        print("=" * 80)
        print("🚀 PRODUCTION FLOW TEST FOR OKPUJA BACKEND")
        print("=" * 80)
        print(f"🌐 Base URL: {self.base_url}")
        print(f"👤 Test User: {self.test_credentials['email']}")
        print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("User Authentication", self.test_authentication),
            ("Services API", self.test_services_api),
            ("User Profile", self.test_profile_api),
            ("Cart Creation", self.test_cart_creation),
            ("Payment Initiation", self.test_payment_initiation),
            ("Payment Status Check", self.test_payment_status),
            ("Booking List", self.test_booking_list),
            ("Webhooks Endpoint", self.test_webhooks_endpoint),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(1)  # Small delay between tests
            except Exception as e:
                self.print_error(f"Unexpected error in {test_name}: {str(e)}")
        
        # Print results
        print("\n" + "=" * 80)
        print("📊 PRODUCTION TEST RESULTS")
        print("=" * 80)
        print(f"Steps Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL PRODUCTION TESTS PASSED!")
            print("✅ Production environment is ready!")
        elif passed >= total * 0.8:
            print("🎯 PRODUCTION TESTS MOSTLY SUCCESSFUL!")
            print("✅ Core functionality is working!")
            print("🔧 Minor issues can be fixed easily.")
        else:
            print("⚠️ PRODUCTION TESTS NEED ATTENTION!")
            print("🔧 Some core functionality may need fixing.")
        
        print("\n🎯 PRODUCTION TEST SUMMARY:")
        if self.test_data.get('cart_id'):
            print(f"   🛒 Test Cart: {self.test_data['cart_id']}")
        if self.test_data.get('payment_id'):
            print(f"   💳 Test Payment: {self.test_data['payment_id']}")
        if self.test_data.get('service_name'):
            print(f"   🕉️ Test Service: {self.test_data['service_name']}")
        
        print(f"\n🌟 Production flow test completed!")
        print(f"🔍 Use the above data to verify the complete flow in production.")
        
        return passed == total

if __name__ == "__main__":
    tester = ProductionFlowTest()
    tester.run_all_tests()
