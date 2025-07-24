#!/usr/bin/env python
"""
End-to-end PhonePe Payment Test Script
This script tests the complete payment flow including the fix
"""

import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from cart.models import Cart
from payment.models import Payment, PaymentStatus

User = get_user_model()

class EndToEndPaymentTest:
    def __init__(self):
        self.base_url = "https://backend.okpuja.com" if hasattr(settings, 'PRODUCTION_SERVER') and settings.PRODUCTION_SERVER else "http://localhost:8000"
        
    def create_test_user_and_cart(self):
        """Create test user and cart for payment testing"""
        
        # Create test user
        test_user, created = User.objects.get_or_create(
            email='payment_test@okpuja.com',
            defaults={
                'phone_number': '9876543210',
                'first_name': 'Payment',
                'last_name': 'Test',
                'is_verified': True
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            
        # Create test cart
        test_cart = Cart.objects.create(
            user=test_user,
            total_amount=999.00,  # Test with 999 rupees
            status='ACTIVE'
        )
        
        print(f"✅ Created test user: {test_user.email}")
        print(f"✅ Created test cart: {test_cart.id} (₹{test_cart.total_amount})")
        
        return test_user, test_cart
    
    def get_auth_token(self, user):
        """Get JWT token for the user"""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_payment_api(self, user, cart):
        """Test the payment API endpoint"""
        
        token = self.get_auth_token(user)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'cart_id': cart.id,
            'method': 'PHONEPE'
        }
        
        url = f"{self.base_url}/api/payments/payments/process-cart/"
        
        print(f"\n🚀 Testing Payment API:")
        print(f"   URL: {url}")
        print(f"   Payload: {payload}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:500]}...")
            
            if response.status_code == 201:
                response_data = response.json()
                print("   ✅ PAYMENT API SUCCESS!")
                print(f"   Payment URL: {response_data.get('payment_url', 'N/A')}")
                return response_data
            elif response.status_code == 400:
                response_data = response.json()
                error_category = response_data.get('error_category', 'UNKNOWN')
                print(f"   ❌ Payment API failed with category: {error_category}")
                
                if error_category == 'CONNECTION_REFUSED':
                    print("   🔧 This confirms the connection issue!")
                    print("   💡 Try the simulate endpoint for testing")
                    
                    # Test simulate endpoint
                    if 'payment_id' in response_data:
                        self.test_simulate_endpoint(response_data['payment_id'], token)
                
                return response_data
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Cannot connect to backend server")
            return None
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None
    
    def test_simulate_endpoint(self, payment_id, token):
        """Test the payment simulation endpoint"""
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/api/payments/payments/{payment_id}/simulate-success/"
        
        print(f"\n🧪 Testing Simulation Endpoint:")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, headers=headers, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 200:
                print("   ✅ PAYMENT SIMULATION SUCCESS!")
                return response.json()
            else:
                print("   ❌ Simulation failed")
                return None
                
        except Exception as e:
            print(f"   ❌ Simulation error: {str(e)}")
            return None
    
    def test_debug_endpoint(self, token):
        """Test the debug connectivity endpoint (admin only)"""
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/api/payments/payments/debug-connectivity/"
        
        print(f"\n🔍 Testing Debug Endpoint:")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ DEBUG ENDPOINT SUCCESS!")
                debug_data = response.json()
                
                # Show connectivity results
                connectivity = debug_data.get('connectivity_test', [])
                working = [c for c in connectivity if c.get('status') == 'connected']
                failed = [c for c in connectivity if c.get('status') != 'connected']
                
                print(f"   Working endpoints: {len(working)}")
                print(f"   Failed endpoints: {len(failed)}")
                
                return debug_data
            else:
                print(f"   ❌ Debug endpoint failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Debug error: {str(e)}")
            return None
    
    def cleanup(self, user, cart):
        """Clean up test data"""
        
        # Delete payments for this cart
        Payment.objects.filter(cart=cart).delete()
        
        # Delete cart
        cart.delete()
        
        # Delete user if it was created for testing
        if user.email == 'payment_test@okpuja.com':
            user.delete()
        
        print("🧹 Cleaned up test data")
    
    def run_complete_test(self):
        """Run the complete end-to-end test"""
        
        print("=" * 80)
        print("END-TO-END PHONEPE PAYMENT TEST")
        print("=" * 80)
        
        # Setup
        print("\n1. SETUP:")
        user, cart = self.create_test_user_and_cart()
        
        try:
            # Test payment API
            print("\n2. PAYMENT API TEST:")
            payment_result = self.test_payment_api(user, cart)
            
            # Test debug endpoint (if user is admin)
            if user.is_staff or user.is_superuser:
                print("\n3. DEBUG CONNECTIVITY TEST:")
                debug_result = self.test_debug_endpoint(self.get_auth_token(user))
            
            # Show results
            print("\n" + "=" * 80)
            print("TEST RESULTS:")
            
            if payment_result and payment_result.get('success'):
                print("🎉 PAYMENT TEST: SUCCESS!")
                print("Your PhonePe integration is working correctly.")
            elif payment_result and payment_result.get('error_category') == 'CONNECTION_REFUSED':
                print("⚠️  PAYMENT TEST: CONNECTION ISSUE DETECTED")
                print("PhonePe API connection is being refused by your server.")
                print("\nSolution Steps:")
                print("1. Contact your hosting provider about outbound HTTPS connections")
                print("2. Check firewall rules for port 443")
                print("3. Ensure DNS resolution works for api.phonepe.com")
                print("4. Use the simulation endpoint for testing meanwhile")
            else:
                print("❌ PAYMENT TEST: FAILED")
                print("Check the error details above")
            
            print("=" * 80)
            
        finally:
            # Cleanup
            print("\n4. CLEANUP:")
            self.cleanup(user, cart)

if __name__ == "__main__":
    test = EndToEndPaymentTest()
    test.run_complete_test()
