#!/usr/bin/env python
"""
Test PhonePe OAuth connectivity
"""
import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_phonepe_connectivity():
    """Test connectivity to PhonePe OAuth and API endpoints"""
    try:
        from django.conf import settings
        
        # Test URLs
        oauth_url = getattr(settings, 'PHONEPE_OAUTH_BASE_URL', 'https://oauth-preprod.phonepe.com')
        payment_url = getattr(settings, 'PHONEPE_PAYMENT_BASE_URL', 'https://api-preprod.phonepe.com/apis/pg-sandbox')
        
        print("🔌 Testing PhonePe connectivity...")
        print(f"OAuth URL: {oauth_url}")
        print(f"Payment URL: {payment_url}")
        
        # Test OAuth endpoint connectivity
        try:
            full_oauth_url = f"{oauth_url}/oauth2/v2/token"
            print(f"\n🧪 Testing OAuth endpoint: {full_oauth_url}")
            
            response = requests.get(full_oauth_url, timeout=10)
            print(f"✅ OAuth endpoint reachable (Status: {response.status_code})")
            
        except requests.exceptions.ConnectionError as e:
            print(f"❌ OAuth endpoint unreachable: {str(e)}")
            print("💡 Trying alternative OAuth URL...")
            
            # Try alternative URLs
            alternative_urls = [
                "https://oauth.phonepe.com",
                "https://auth-preprod.phonepe.com", 
                "https://api-preprod.phonepe.com"
            ]
            
            for alt_url in alternative_urls:
                try:
                    test_url = f"{alt_url}/oauth2/v2/token"
                    print(f"   Testing: {test_url}")
                    response = requests.get(test_url, timeout=10)
                    print(f"   ✅ Alternative URL works: {alt_url} (Status: {response.status_code})")
                    break
                except Exception as e:
                    print(f"   ❌ {alt_url} failed: {str(e)}")
        
        except Exception as e:
            print(f"❌ OAuth test error: {str(e)}")
        
        # Test payment endpoint connectivity
        try:
            print(f"\n🧪 Testing Payment endpoint: {payment_url}")
            response = requests.get(payment_url, timeout=10)
            print(f"✅ Payment endpoint reachable (Status: {response.status_code})")
            
        except Exception as e:
            print(f"❌ Payment endpoint error: {str(e)}")
        
        # Check if we should bypass OAuth for testing
        print(f"\n🔑 PhonePe Credentials Check:")
        client_id = getattr(settings, 'PHONEPE_CLIENT_ID', '')
        client_secret = getattr(settings, 'PHONEPE_CLIENT_SECRET', '')
        merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', '')
        
        print(f"   CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}")
        print(f"   CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Not set'}")
        print(f"   MERCHANT_ID: {'✅ Set' if merchant_id else '❌ Not set'}")
        
        if not client_id or not client_secret:
            print("💡 Missing OAuth credentials - you may need to use a different authentication method for testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Connectivity test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phonepe_connectivity()
    sys.exit(0 if success else 1)
