"""
Production PhonePe Connection Test
Tests the production PhonePe configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payments.phonepe_client import PhonePePaymentClient
from payments.services import PaymentService
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_production_phonepe():
    """Test production PhonePe configuration"""
    
    print("🔍 PRODUCTION PHONEPE CONNECTION TEST")
    print("=" * 60)
    
    # Show current configuration
    print(f"📋 Configuration:")
    print(f"   Environment: {getattr(settings, 'PHONEPE_ENV', 'NOT_SET')}")
    print(f"   Client ID: {getattr(settings, 'PHONEPE_CLIENT_ID', 'NOT_SET')}")
    print(f"   Merchant ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT_SET')}")
    print(f"   Auth Base URL: {getattr(settings, 'PHONEPE_AUTH_BASE_URL', 'NOT_SET')}")
    print(f"   Payment Base URL: {getattr(settings, 'PHONEPE_PAYMENT_BASE_URL', 'NOT_SET')}")
    
    # Test PhonePe client initialization
    try:
        print(f"\n🔧 Testing PhonePe Client:")
        client = PhonePePaymentClient(environment="production")
        print(f"   ✅ Client initialized successfully")
        print(f"   Base URL: {client.base_url}")
        print(f"   OAuth URL: {client.oauth_url}")
        print(f"   Payment URL: {client.payment_url}")
        
    except Exception as e:
        print(f"   ❌ Client initialization failed: {e}")
        return False
    
    # Test OAuth token
    try:
        print(f"\n🔑 Testing OAuth Token:")
        token = client.get_access_token()
        if token:
            print(f"   ✅ OAuth token obtained successfully")
            print(f"   Token: {token[:20]}...")
        else:
            print(f"   ❌ No token received")
            return False
            
    except Exception as e:
        print(f"   ❌ OAuth failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test Payment Service
    try:
        print(f"\n💳 Testing Payment Service:")
        payment_service = PaymentService(environment="production")
        print(f"   ✅ Payment service initialized")
        
    except Exception as e:
        print(f"   ❌ Payment service failed: {e}")
        return False
    
    print(f"\n🎉 All tests passed! PhonePe production connection is working")
    return True

def check_missing_config():
    """Check for missing configuration"""
    print(f"\n🔍 CHECKING CONFIGURATION:")
    
    required_settings = [
        'PHONEPE_ENV',
        'PHONEPE_CLIENT_ID', 
        'PHONEPE_CLIENT_SECRET',
        'PHONEPE_MERCHANT_ID',
        'PHONEPE_AUTH_BASE_URL',
        'PHONEPE_PAYMENT_BASE_URL',
        'PHONEPE_CALLBACK_URL',
        'PHONEPE_SUCCESS_REDIRECT_URL',
        'PHONEPE_FAILED_REDIRECT_URL'
    ]
    
    missing = []
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if not value:
            missing.append(setting)
            print(f"   ❌ Missing: {setting}")
        else:
            print(f"   ✅ Found: {setting}")
    
    if missing:
        print(f"\n⚠️ Missing configuration: {missing}")
        return False
    else:
        print(f"\n✅ All required configuration found")
        return True

if __name__ == "__main__":
    print("Testing PhonePe Production Configuration...\n")
    
    config_ok = check_missing_config()
    if config_ok:
        connection_ok = test_production_phonepe()
        
        if connection_ok:
            print(f"\n🎉 PRODUCTION PHONEPE IS READY!")
        else:
            print(f"\n❌ PRODUCTION PHONEPE CONNECTION FAILED!")
    else:
        print(f"\n❌ CONFIGURATION INCOMPLETE!")
