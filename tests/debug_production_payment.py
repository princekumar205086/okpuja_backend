"""
Production Payment Debug Script
Diagnose payment issues in production environment
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payments.phonepe_client import PhonePePaymentClient
from payments.services import PaymentService
import requests
import json

def test_production_payment_setup():
    """Test production payment configuration"""
    
    print("🔍 PRODUCTION PAYMENT DIAGNOSTICS")
    print("=" * 50)
    
    # 1. Check environment configuration
    print(f"\n📊 Environment Configuration:")
    print(f"   PHONEPE_ENV: {getattr(settings, 'PHONEPE_ENV', 'NOT_SET')}")
    print(f"   PHONEPE_CLIENT_ID: {getattr(settings, 'PHONEPE_CLIENT_ID', 'NOT_SET')[:20]}...")
    print(f"   PHONEPE_CLIENT_SECRET: {getattr(settings, 'PHONEPE_CLIENT_SECRET', 'NOT_SET')[:10]}...")
    print(f"   PHONEPE_MERCHANT_ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT_SET')}")
    print(f"   PHONEPE_BASE_URL: {getattr(settings, 'PHONEPE_PAYMENT_BASE_URL', 'NOT_SET')}")
    
    # 2. Test PhonePe connectivity
    print(f"\n🌐 Testing PhonePe Connectivity:")
    try:
        client = PhonePePaymentClient()
        
        # Test OAuth URL connectivity
        oauth_url = client.oauth_url
        print(f"   OAuth URL: {oauth_url}")
        
        # Try to reach the OAuth endpoint (without authentication)
        response = requests.get(oauth_url.replace('/token', ''), timeout=10)
        print(f"   Base URL Reachable: ✅ (Status: {response.status_code})")
        
    except Exception as e:
        print(f"   Base URL Reachable: ❌ Error: {e}")
    
    # 3. Test OAuth token generation
    print(f"\n🔑 Testing OAuth Token Generation:")
    try:
        client = PhonePePaymentClient()
        token = client.get_access_token()
        if token:
            print(f"   OAuth Token: ✅ Generated successfully")
            print(f"   Token Length: {len(token)} characters")
        else:
            print(f"   OAuth Token: ❌ No token received")
            
    except Exception as e:
        print(f"   OAuth Token: ❌ Error: {e}")
        print(f"   Error Type: {type(e).__name__}")
    
    # 4. Test Payment Service initialization
    print(f"\n⚙️ Testing Payment Service:")
    try:
        payment_service = PaymentService()
        print(f"   Payment Service: ✅ Initialized successfully")
        print(f"   Environment: {payment_service.environment}")
        
    except Exception as e:
        print(f"   Payment Service: ❌ Error: {e}")
        print(f"   Error Type: {type(e).__name__}")
    
    # 5. Check required URLs
    print(f"\n🔗 Checking Required URLs:")
    required_urls = [
        'PHONEPE_CALLBACK_URL',
        'PHONEPE_PROFESSIONAL_REDIRECT_URL',
        'PHONEPE_SUCCESS_REDIRECT_URL',
        'PHONEPE_FAILED_REDIRECT_URL'
    ]
    
    for url_setting in required_urls:
        url_value = getattr(settings, url_setting, 'NOT_SET')
        if 'localhost' in url_value:
            print(f"   {url_setting}: ⚠️ Still using localhost: {url_value}")
        elif url_value == 'NOT_SET':
            print(f"   {url_setting}: ❌ Not configured")
        else:
            print(f"   {url_setting}: ✅ {url_value}")
    
    # 6. Test network connectivity to PhonePe
    print(f"\n🌍 Testing Network Connectivity:")
    phonepe_hosts = [
        "https://api-preprod.phonepe.com",
        "https://api.phonepe.com"
    ]
    
    for host in phonepe_hosts:
        try:
            response = requests.get(f"{host}/health", timeout=10)
            print(f"   {host}: ✅ Reachable")
        except requests.exceptions.Timeout:
            print(f"   {host}: ⏰ Timeout (may still work)")
        except requests.exceptions.ConnectionError:
            print(f"   {host}: ❌ Connection failed")
        except Exception as e:
            print(f"   {host}: ⚠️ {type(e).__name__}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    
    # Check if using localhost URLs in production
    callback_url = getattr(settings, 'PHONEPE_CALLBACK_URL', '')
    if 'localhost' in callback_url:
        print(f"   ❌ CRITICAL: Update PHONEPE URLs from localhost to production domain")
        print(f"   📝 Change localhost:8000 to api.okpuja.com in .env file")
    
    # Check environment
    env = getattr(settings, 'PHONEPE_ENV', 'UAT')
    if env.upper() == 'UAT':
        print(f"   ⚠️ WARNING: Still using UAT environment in production")
        print(f"   📝 Consider switching to PRODUCTION environment for live payments")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Update all localhost URLs to production URLs in .env")
    print(f"   2. Ensure server can reach PhonePe APIs")
    print(f"   3. Check firewall/security group settings")
    print(f"   4. Test OAuth token generation")

if __name__ == "__main__":
    test_production_payment_setup()
