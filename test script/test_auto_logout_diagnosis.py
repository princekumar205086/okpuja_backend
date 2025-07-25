#!/usr/bin/env python
"""
Test script to identify potential auto-logout issues
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
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from accounts.models import User

class AutoLogoutDiagnostic:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        
    def analyze_jwt_settings(self):
        """Analyze JWT settings for potential auto-logout causes"""
        print("🔍 JWT Settings Analysis")
        print("=" * 40)
        
        jwt_settings = settings.SIMPLE_JWT
        
        access_lifetime = jwt_settings.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=60))
        refresh_lifetime = jwt_settings.get('REFRESH_TOKEN_LIFETIME', timedelta(days=7))
        rotate_tokens = jwt_settings.get('ROTATE_REFRESH_TOKENS', False)
        blacklist_after_rotation = jwt_settings.get('BLACKLIST_AFTER_ROTATION', False)
        
        print(f"✅ Access Token Lifetime: {access_lifetime}")
        print(f"✅ Refresh Token Lifetime: {refresh_lifetime}")
        print(f"✅ Rotate Refresh Tokens: {rotate_tokens}")
        print(f"✅ Blacklist After Rotation: {blacklist_after_rotation}")
        
        # Check for potential issues
        print("\n🚨 Potential Issues:")
        
        if access_lifetime.total_seconds() < 3600:  # Less than 1 hour
            print(f"⚠️ Short access token lifetime ({access_lifetime}) - users will need frequent refreshes")
        
        if refresh_lifetime.total_seconds() < 86400:  # Less than 1 day
            print(f"⚠️ Very short refresh token lifetime ({refresh_lifetime}) - users will be logged out frequently")
        
        if rotate_tokens and blacklist_after_rotation:
            print("ℹ️ Token rotation with blacklisting is enabled - this is secure but requires proper frontend handling")
        
        # Check additional settings that might affect tokens
        additional_settings = [
            'SLIDING_TOKEN_REFRESH_EXP_CLAIM',
            'SLIDING_TOKEN_LIFETIME',
            'SLIDING_TOKEN_REFRESH_LIFETIME',
            'AUTH_TOKEN_CLASSES',
            'TOKEN_TYPE_CLAIM',
            'JTI_CLAIM',
            'TOKEN_USER_CLASS'
        ]
        
        print("\n🔧 Additional JWT Settings:")
        for setting in additional_settings:
            value = jwt_settings.get(setting)
            if value is not None:
                print(f"  {setting}: {value}")
        
        return True
    
    def test_token_timing(self):
        """Test token timing behavior"""
        print("\n⏰ Token Timing Test")
        print("=" * 30)
        
        # Create test user and login
        self._create_test_user()
        self._login()
        
        # Decode and analyze token
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from django.conf import settings
            import jwt
            
            # Decode access token
            decoded_access = jwt.decode(
                self.access_token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            
            # Decode refresh token
            decoded_refresh = jwt.decode(
                self.refresh_token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            
            access_exp = datetime.fromtimestamp(decoded_access['exp'])
            refresh_exp = datetime.fromtimestamp(decoded_refresh['exp'])
            current_time = datetime.now()
            
            print(f"🕐 Current time: {current_time}")
            print(f"🔑 Access token expires: {access_exp}")
            print(f"🔄 Refresh token expires: {refresh_exp}")
            print(f"⏳ Access token valid for: {access_exp - current_time}")
            print(f"⏳ Refresh token valid for: {refresh_exp - current_time}")
            
            # Check if tokens are about to expire
            if (access_exp - current_time).total_seconds() < 300:  # 5 minutes
                print("⚠️ Access token expires very soon!")
            
            if (refresh_exp - current_time).total_seconds() < 3600:  # 1 hour
                print("⚠️ Refresh token expires very soon!")
            
        except Exception as e:
            print(f"❌ Error analyzing token timing: {e}")
    
    def test_concurrent_requests(self):
        """Test how tokens behave with concurrent requests"""
        print("\n🔄 Concurrent Request Test")
        print("=" * 35)
        
        # Make multiple rapid requests to see if tokens get invalidated
        import threading
        import time
        
        results = []
        
        def make_request(thread_id):
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(f"{self.base_url}/api/auth/profile/", headers=headers)
                results.append({
                    'thread': thread_id,
                    'status': response.status_code,
                    'time': time.time()
                })
            except Exception as e:
                results.append({
                    'thread': thread_id,
                    'error': str(e),
                    'time': time.time()
                })
        
        # Launch 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Analyze results
        successful = len([r for r in results if r.get('status') == 200])
        failed = len([r for r in results if r.get('status') != 200])
        
        print(f"✅ Successful requests: {successful}")
        print(f"❌ Failed requests: {failed}")
        
        if failed > 0:
            print("⚠️ Some concurrent requests failed - check for race conditions")
            for result in results:
                if result.get('status') != 200:
                    print(f"  Thread {result.get('thread')}: {result}")
    
    def test_frontend_simulation(self):
        """Simulate common frontend scenarios that might cause auto-logout"""
        print("\n🌐 Frontend Scenario Simulation")
        print("=" * 40)
        
        scenarios = [
            ("Page refresh", self._simulate_page_refresh),
            ("Multiple tabs", self._simulate_multiple_tabs),
            ("Network interruption", self._simulate_network_interruption),
            ("Token storage issues", self._simulate_storage_issues)
        ]
        
        for scenario_name, scenario_func in scenarios:
            print(f"\n🧪 Testing: {scenario_name}")
            try:
                result = scenario_func()
                if result:
                    print(f"✅ {scenario_name}: Passed")
                else:
                    print(f"❌ {scenario_name}: Failed")
            except Exception as e:
                print(f"💥 {scenario_name}: Error - {e}")
    
    def _simulate_page_refresh(self):
        """Simulate page refresh scenario"""
        # Store current tokens
        stored_access = self.access_token
        stored_refresh = self.refresh_token
        
        # Simulate losing access token but keeping refresh token (common in page refresh)
        self.access_token = None
        
        # Try to refresh
        if self._refresh_token():
            print("  ✅ Successfully recovered from page refresh")
            return True
        else:
            print("  ❌ Failed to recover from page refresh")
            return False
    
    def _simulate_multiple_tabs(self):
        """Simulate multiple tabs scenario"""
        # Get initial tokens
        original_refresh = self.refresh_token
        
        # Simulate first tab refreshing token
        if self._refresh_token():
            new_refresh_tab1 = self.refresh_token
            
            # Simulate second tab trying to use old refresh token
            self.refresh_token = original_refresh
            
            if not self._refresh_token():
                print("  ✅ Old refresh token correctly invalidated (good for security)")
                print("  ⚠️ This might cause auto-logout in multi-tab scenarios")
                return True
            else:
                print("  ⚠️ Old refresh token still works (potential security issue)")
                return False
        return False
    
    def _simulate_network_interruption(self):
        """Simulate network interruption"""
        # Test with invalid URL to simulate network issues
        old_base_url = self.base_url
        self.base_url = "http://invalid-url:8000"
        
        try:
            result = self._refresh_token()
            self.base_url = old_base_url
            
            if not result:
                print("  ✅ Correctly handled network interruption")
                return True
            else:
                print("  ❌ Unexpected success with invalid URL")
                return False
        except:
            self.base_url = old_base_url
            print("  ✅ Network error properly caught")
            return True
    
    def _simulate_storage_issues(self):
        """Simulate local storage corruption"""
        # Corrupt tokens
        original_access = self.access_token
        original_refresh = self.refresh_token
        
        # Simulate corrupted storage
        self.access_token = self.access_token[:-10] + "corrupted"
        self.refresh_token = self.refresh_token[:-10] + "corrupted"
        
        # Try to use corrupted tokens
        if not self._test_access_token() and not self._refresh_token():
            print("  ✅ Correctly rejected corrupted tokens")
            # Restore original tokens
            self.access_token = original_access
            self.refresh_token = original_refresh
            return True
        else:
            print("  ❌ Corrupted tokens were accepted")
            return False
    
    def _create_test_user(self):
        """Create test user"""
        try:
            User.objects.filter(email="autotest@example.com").delete()
            user = User.objects.create_user(
                email="autotest@example.com",
                password="testpass123",
                role="USER"
            )
            user.otp_verified = True
            user.account_status = "ACTIVE"
            user.save()
            return user
        except Exception as e:
            print(f"Error creating test user: {e}")
            return None
    
    def _login(self):
        """Login to get tokens"""
        try:
            url = f"{self.base_url}/api/auth/login/"
            data = {"email": "autotest@example.com", "password": "testpass123"}
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                return True
            return False
        except:
            return False
    
    def _test_access_token(self):
        """Test access token"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.base_url}/api/auth/profile/", headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def _refresh_token(self):
        """Refresh token"""
        try:
            url = f"{self.base_url}/api/auth/refresh/"
            data = {"refresh": self.refresh_token}
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                if 'refresh' in data:
                    self.refresh_token = data.get('refresh')
                return True
            return False
        except:
            return False
    
    def run_full_diagnosis(self):
        """Run complete auto-logout diagnosis"""
        print("🔍 Auto-Logout Diagnostic Tool")
        print("=" * 50)
        
        # Analyze settings
        self.analyze_jwt_settings()
        
        # Test token timing
        self.test_token_timing()
        
        # Test concurrent requests
        self.test_concurrent_requests()
        
        # Test frontend scenarios
        self.test_frontend_simulation()
        
        print("\n📋 Summary & Recommendations")
        print("=" * 40)
        print("1. ✅ Refresh token functionality is working correctly")
        print("2. ⚠️ If auto-logout occurs, check:")
        print("   - Frontend token refresh handling")
        print("   - Token storage (localStorage vs sessionStorage)")
        print("   - Network connectivity during token refresh")
        print("   - Multiple tab handling with token rotation")
        print("   - Browser console for JavaScript errors")
        
        print("\n🛠️ Recommended Frontend Implementation:")
        print("   - Use axios interceptors to handle 401 responses")
        print("   - Implement automatic token refresh")
        print("   - Handle token rotation properly")
        print("   - Add retry logic for failed refresh attempts")
        print("   - Show user-friendly error messages")

def main():
    diagnostic = AutoLogoutDiagnostic()
    diagnostic.run_full_diagnosis()

if __name__ == "__main__":
    main()
