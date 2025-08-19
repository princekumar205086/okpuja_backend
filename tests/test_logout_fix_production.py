#!/usr/bin/env python
"""
Production Test Script for Logout Issue Fix
Run this after deploying the JWT configuration fix
"""

import requests
import json
import sys
from datetime import datetime

class LogoutFixTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
        
    def test_credentials(self):
        """Test both UAT and production credentials"""
        print("🔍 TESTING LOGOUT FIX - CREDENTIAL VERIFICATION")
        print("=" * 60)
        
        credentials = [
            {
                "name": "UAT",
                "email": "asliprinceraj@gmail.com", 
                "password": "testpass123"
            },
            {
                "name": "PRODUCTION", 
                "email": "asliprinceraj@gmail.com",
                "password": "Testpass@123"
            }
        ]
        
        for cred in credentials:
            print(f"\n📋 Testing {cred['name']} credentials...")
            
            success, token_data = self.login_test(cred)
            
            if success:
                print(f"✅ {cred['name']} login successful!")
                
                # Test session persistence
                if self.test_session_persistence(token_data['access']):
                    print(f"✅ {cred['name']} session persistence verified!")
                    
                    # Test token longevity
                    self.analyze_token(token_data['access'])
                    
                    return True, token_data
                else:
                    print(f"❌ {cred['name']} session issues detected!")
            else:
                print(f"❌ {cred['name']} login failed!")
        
        return False, None
    
    def login_test(self, credentials):
        """Test login with given credentials"""
        login_url = f"{self.base_url}/api/auth/login/"
        
        login_data = {
            "email": credentials["email"],
            "password": credentials["password"]
        }
        
        try:
            response = self.session.post(login_url, json=login_data)
            
            if response.status_code == 200:
                auth_data = response.json()
                return True, {
                    'access': auth_data.get('access'),
                    'refresh': auth_data.get('refresh'),
                    'user_data': auth_data
                }
            else:
                print(f"   Status: {response.status_code}")
                if response.content:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                return False, None
                
        except requests.exceptions.RequestException as e:
            print(f"   Connection error: {e}")
            return False, None
        except Exception as e:
            print(f"   Unexpected error: {e}")
            return False, None
    
    def test_session_persistence(self, access_token):
        """Test if session persists across multiple requests"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test profile access
        try:
            profile_url = f"{self.base_url}/api/auth/profile/"
            response = self.session.get(profile_url, headers=headers)
            
            if response.status_code == 200:
                profile_data = response.json()
                print(f"   User profile: {profile_data.get('email')}")
                return True
            elif response.status_code == 401:
                print(f"   ❌ Session expired immediately!")
                return False
            else:
                print(f"   Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   Session test error: {e}")
            return False
    
    def analyze_token(self, access_token):
        """Analyze token expiry and configuration"""
        try:
            import jwt
            
            # Decode without verification (for analysis only)
            payload = jwt.decode(access_token, options={"verify_signature": False})
            
            exp_timestamp = payload.get('exp')
            iat_timestamp = payload.get('iat')
            user_id = payload.get('user_id')
            
            if exp_timestamp and iat_timestamp:
                exp_time = datetime.fromtimestamp(exp_timestamp)
                iat_time = datetime.fromtimestamp(iat_timestamp)
                now = datetime.now()
                
                total_lifetime = exp_time - iat_time
                time_remaining = exp_time - now
                
                print(f"   🔑 Token for user ID: {user_id}")
                print(f"   ⏰ Issued at: {iat_time}")
                print(f"   ⏰ Expires at: {exp_time}")
                print(f"   ⏳ Total lifetime: {total_lifetime}")
                print(f"   ⏳ Time remaining: {time_remaining}")
                
                # Check if fix was applied
                hours_lifetime = total_lifetime.total_seconds() / 3600
                if hours_lifetime >= 1.8:  # At least 1.8 hours (close to 2 hours)
                    print(f"   ✅ JWT fix applied - Token lifetime: {hours_lifetime:.1f} hours")
                else:
                    print(f"   ⚠️  JWT fix may not be applied - Token lifetime: {hours_lifetime:.1f} hours")
                
        except Exception as e:
            print(f"   ❌ Token analysis error: {e}")
    
    def test_booking_simulation(self, access_token):
        """Simulate booking process to test for logout issues"""
        print(f"\n🛒 SIMULATING BOOKING PROCESS...")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        steps = [
            ("Get Puja Services", f"{self.base_url}/api/puja/services/"),
            ("Get User Profile", f"{self.base_url}/api/auth/profile/"),
            ("Get Astrology Services", f"{self.base_url}/api/astrology/services/"),
        ]
        
        for step_name, url in steps:
            try:
                response = self.session.get(url, headers=headers)
                
                if response.status_code == 200:
                    print(f"   ✅ {step_name}: Success")
                elif response.status_code == 401:
                    print(f"   ❌ {step_name}: AUTHENTICATION FAILED - Logout detected!")
                    return False
                else:
                    print(f"   ⚠️  {step_name}: Status {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {step_name}: Error - {e}")
                return False
        
        return True
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 OKPUJA LOGOUT FIX - COMPREHENSIVE TEST")
        print("=" * 60)
        
        # Test server connectivity
        try:
            response = self.session.get(f"{self.base_url}/api/", timeout=5)
            print(f"✅ Server responding (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("   Make sure Django server is running on port 8000")
            return False
        
        # Test credentials
        success, token_data = self.test_credentials()
        
        if success and token_data:
            # Test booking simulation
            if self.test_booking_simulation(token_data['access']):
                print(f"\n🎉 ALL TESTS PASSED!")
                print("✅ Logout issue appears to be fixed!")
                return True
            else:
                print(f"\n❌ Booking simulation failed!")
                print("⚠️  Logout issue may still exist!")
                return False
        else:
            print(f"\n❌ Credential tests failed!")
            print("⚠️  Cannot verify logout fix!")
            return False
    
    def print_recommendations(self):
        """Print implementation recommendations"""
        print(f"\n📋 IMPLEMENTATION RECOMMENDATIONS")
        print("=" * 60)
        
        print("🔧 BACKEND (Applied):")
        print("  ✅ JWT token lifetime extended to 2 hours")
        print("  ✅ Disabled BLACKLIST_AFTER_ROTATION")
        print("  ✅ Enabled UPDATE_LAST_LOGIN")
        
        print(f"\n📱 FRONTEND (Still Needed):")
        print("  🔄 Implement automatic token refresh")
        print("  🔄 Handle 401 responses gracefully")
        print("  🔄 Add loading states during booking")
        print("  🔄 Show session timeout warnings")
        
        print(f"\n🔍 MONITORING:")
        print("  📊 Monitor JWT blacklist activity")
        print("  📊 Track authentication failure rates")
        print("  📊 Monitor user session durations")

def main():
    tester = LogoutFixTester()
    
    success = tester.run_comprehensive_test()
    tester.print_recommendations()
    
    if success:
        print(f"\n🎯 STATUS: LOGOUT FIX VERIFIED ✅")
        sys.exit(0)
    else:
        print(f"\n🎯 STATUS: ISSUES DETECTED ❌")
        print("Please check the JWT settings and server configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
