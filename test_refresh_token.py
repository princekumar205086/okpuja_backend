#!/usr/bin/env python
"""
Test script to verify JWT refresh token functionality
"""
import os
import sys
import django
import requests
import json
import time
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User

class RefreshTokenTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        
    def create_test_user(self):
        """Create a test user for token testing"""
        try:
            # Delete existing test user if exists
            User.objects.filter(email="tokentest@example.com").delete()
            
            user = User.objects.create_user(
                email="tokentest@example.com",
                password="testpass123",
                role="USER"
            )
            # Mark as verified to bypass OTP
            user.otp_verified = True
            user.account_status = "ACTIVE"
            user.save()
            
            print(f"✅ Created test user: {user.email}")
            return user
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            return None
    
    def login_and_get_tokens(self):
        """Login and get initial access and refresh tokens"""
        try:
            url = f"{self.base_url}/api/auth/login/"
            data = {
                "email": "tokentest@example.com",
                "password": "testpass123"
            }
            
            response = requests.post(url, json=data)
            print(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                
                print(f"✅ Login successful")
                print(f"Access token (first 50 chars): {self.access_token[:50]}...")
                print(f"Refresh token (first 50 chars): {self.refresh_token[:50]}...")
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_access_token(self):
        """Test if access token works for authenticated endpoints"""
        try:
            url = f"{self.base_url}/api/auth/profile/"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = requests.get(url, headers=headers)
            print(f"Profile access response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Access token is valid")
                return True
            else:
                print(f"❌ Access token invalid: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Access token test error: {e}")
            return False
    
    def refresh_access_token(self):
        """Use refresh token to get new access token"""
        try:
            url = f"{self.base_url}/api/auth/refresh/"
            data = {"refresh": self.refresh_token}
            
            response = requests.post(url, json=data)
            print(f"Token refresh response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                old_access_token = self.access_token[:50]
                
                self.access_token = data.get('access')
                
                # Check if new refresh token is provided (rotation enabled)
                if 'refresh' in data:
                    self.refresh_token = data.get('refresh')
                    print("✅ Token rotation enabled - new refresh token received")
                else:
                    print("ℹ️ Token rotation disabled - same refresh token")
                
                print(f"✅ Token refresh successful")
                print(f"Old access token: {old_access_token}...")
                print(f"New access token: {self.access_token[:50]}...")
                return True
            else:
                print(f"❌ Token refresh failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return False
    
    def test_token_expiry_simulation(self):
        """Simulate token expiry by waiting and testing"""
        print("\n🕐 Testing token expiry simulation...")
        
        # Get current token lifetime from settings
        access_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        print(f"Access token lifetime: {access_lifetime}")
        
        # Test with current token
        if self.test_access_token():
            print("Token valid before expiry simulation")
        
        # For testing, we'll simulate an expired token by modifying it
        print("Simulating expired token...")
        original_token = self.access_token
        self.access_token = self.access_token[:-10] + "0000000000"  # Corrupt token
        
        if not self.test_access_token():
            print("✅ Correctly detected invalid/expired token")
            
        # Restore original token
        self.access_token = original_token
        
        # Try to refresh
        if self.refresh_access_token():
            print("✅ Successfully refreshed after simulated expiry")
            return True
        
        return False
    
    def test_blacklisted_refresh_token(self):
        """Test behavior with blacklisted refresh token"""
        try:
            print("\n🚫 Testing blacklisted refresh token...")
            
            # Store current refresh token
            current_refresh = self.refresh_token
            
            # Logout to blacklist the token
            url = f"{self.base_url}/api/auth/logout/"
            data = {"refresh": current_refresh}
            
            response = requests.post(url, json=data)
            print(f"Logout response status: {response.status_code}")
            
            if response.status_code == 205:
                print("✅ Logout successful - token should be blacklisted")
                
                # Try to use the blacklisted token
                url = f"{self.base_url}/api/auth/refresh/"
                data = {"refresh": current_refresh}
                
                response = requests.post(url, json=data)
                print(f"Refresh with blacklisted token status: {response.status_code}")
                
                if response.status_code == 401 or response.status_code == 400:
                    print("✅ Blacklisted token correctly rejected")
                    return True
                else:
                    print(f"❌ Blacklisted token was accepted: {response.text}")
                    return False
            else:
                print(f"❌ Logout failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Blacklist test error: {e}")
            return False
    
    def check_jwt_settings(self):
        """Check current JWT settings"""
        print("🔧 Current JWT Settings:")
        jwt_settings = settings.SIMPLE_JWT
        
        for key, value in jwt_settings.items():
            print(f"  {key}: {value}")
        
        # Check if token blacklist app is installed
        if 'rest_framework_simplejwt.token_blacklist' in settings.INSTALLED_APPS:
            print("✅ Token blacklist app is installed")
        else:
            print("⚠️ Token blacklist app is NOT installed")
    
    def run_comprehensive_test(self):
        """Run all refresh token tests"""
        print("🚀 Starting Comprehensive Refresh Token Test")
        print("=" * 50)
        
        # Check settings
        self.check_jwt_settings()
        print()
        
        # Create test user
        if not self.create_test_user():
            return False
        
        # Login and get tokens
        if not self.login_and_get_tokens():
            return False
        
        print()
        
        # Test initial access token
        if not self.test_access_token():
            return False
        
        print()
        
        # Test token refresh
        if not self.refresh_access_token():
            return False
        
        print()
        
        # Test with new token after refresh
        if not self.test_access_token():
            print("❌ New access token after refresh doesn't work")
            return False
        
        print()
        
        # Test token expiry simulation
        self.test_token_expiry_simulation()
        
        print()
        
        # Test blacklisted token
        self.test_blacklisted_refresh_token()
        
        print("\n✅ All tests completed!")
        return True

def main():
    print("JWT Refresh Token Functionality Test")
    print("====================================")
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000")
        print(f"✅ Server is running (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start Django server first:")
        print("python manage.py runserver")
        return
    
    # Run tests
    tester = RefreshTokenTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
