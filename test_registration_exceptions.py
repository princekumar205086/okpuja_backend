#!/usr/bin/env python
"""
Test script to verify registration exception handling
"""
import os
import sys
import django
import requests
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from accounts.models import User

class RegistrationExceptionTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
    
    def test_duplicate_phone_registration(self):
        """Test registration with duplicate phone number"""
        print("🔍 Testing duplicate phone number registration...")
        
        # Use unique test data to avoid conflicts
        import time
        timestamp = int(time.time())
        existing_phone = f"+91987654{timestamp % 10000:04d}"
        existing_email = f"existing{timestamp}@test.com"
        new_email = f"new{timestamp}@test.com"
        
        # Create an existing user
        existing_user = User.objects.create_user(
            email=existing_email,
            phone=existing_phone,
            password="test123"
        )
        print(f"✅ Created existing user with phone: {existing_phone}")
        
        # Now try to register a new user with the same phone number
        url = f"{self.base_url}/api/auth/register/"
        data = {
            'email': new_email,
            'phone': existing_phone,  # Same phone number
            'password': 'newpass123',
            'password2': 'newpass123'
        }
        
        print(f"🔄 Attempting registration with duplicate phone: {existing_phone}")
        
        try:
            response = requests.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Clean up
            existing_user.delete()
            
            if response.status_code == 400:
                response_data = response.json()
                if 'phone' in response_data or 'field_errors' in response_data:
                    print("✅ SUCCESS: Duplicate phone number properly handled with user-friendly message")
                    return True
                else:
                    print("⚠️  WARNING: Got 400 status but error format is not ideal")
                    return False
            else:
                print("❌ FAILED: Expected 400 status code for duplicate phone")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: Exception occurred: {e}")
            # Clean up on error
            try:
                existing_user.delete()
            except:
                pass
            return False
    
    def test_duplicate_email_registration(self):
        """Test registration with duplicate email"""
        print("\\n🔍 Testing duplicate email registration...")
        
        # Use unique test data to avoid conflicts  
        import time
        timestamp = int(time.time()) + 1  # Different timestamp
        existing_phone = f"+91987654{timestamp % 10000:04d}"
        existing_email = f"duplicate{timestamp}@test.com"
        new_phone = f"+91987654{(timestamp + 1) % 10000:04d}"
        
        # Create an existing user
        existing_user = User.objects.create_user(
            email=existing_email,
            phone=existing_phone,
            password="test123"
        )
        print(f"✅ Created existing user with email: {existing_email}")
        
        # Now try to register a new user with the same email
        url = f"{self.base_url}/api/auth/register/"
        data = {
            'email': existing_email,  # Same email
            'phone': new_phone,  # Different phone
            'password': 'newpass123',
            'password2': 'newpass123'
        }
        
        print(f"🔄 Attempting registration with duplicate email: {existing_email}")
        
        try:
            response = requests.post(url, json=data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Clean up
            existing_user.delete()
            
            if response.status_code == 400:
                response_data = response.json()
                if 'email' in response_data or 'field_errors' in response_data:
                    print("✅ SUCCESS: Duplicate email properly handled with user-friendly message")
                    return True
                else:
                    print("⚠️  WARNING: Got 400 status but error format is not ideal")
                    return False
            else:
                print("❌ FAILED: Expected 400 status code for duplicate email")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: Exception occurred: {e}")
            # Clean up on error
            try:
                existing_user.delete()
            except:
                pass
            return False
    
    def run_tests(self):
        """Run all registration exception tests"""
        print("🚀 Testing Registration Exception Handling")
        print("=" * 50)
        
        phone_test = self.test_duplicate_phone_registration()
        email_test = self.test_duplicate_email_registration()
        
        print("\\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)
        print(f"Duplicate Phone Test: {'✅ PASS' if phone_test else '❌ FAIL'}")
        print(f"Duplicate Email Test: {'✅ PASS' if email_test else '❌ FAIL'}")
        
        if phone_test and email_test:
            print("\\n🎉 All tests passed! Registration exception handling is working correctly.")
        else:
            print(f"\\n⚠️  {2 - sum([phone_test, email_test])} test(s) failed. Check the error handling.")

if __name__ == "__main__":
    tester = RegistrationExceptionTester()
    tester.run_tests()
