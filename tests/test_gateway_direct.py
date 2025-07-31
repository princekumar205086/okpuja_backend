#!/usr/bin/env python3
"""
Direct PhonePe Gateway Test - Verify HTTP 400 Fix
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.gateways_v2 import PhonePeGatewayV2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gateway_directly():
    """Test the PhonePe gateway directly"""
    
    print("🔧 Direct PhonePe Gateway Test")
    print("=" * 40)
    
    try:
        # Initialize gateway
        print("\n1️⃣ Initializing PhonePe Gateway...")
        gateway = PhonePeGatewayV2()
        
        print(f"✅ Gateway initialized:")
        print(f"   Auth URL: {gateway.auth_base_url}")
        print(f"   Payment URL: {gateway.payment_base_url}")
        print(f"   Merchant ID: {gateway.merchant_id}")
        print(f"   Client ID: {gateway.client_id}")
        
        # Test connectivity
        print(f"\n2️⃣ Testing API connectivity...")
        connectivity_results = gateway.test_connectivity()
        
        for result in connectivity_results:
            status_icon = "✅" if result['status'] == 'connected' else "❌"
            print(f"   {status_icon} {result['endpoint']}: {result.get('response_code', result.get('error'))}")
        
        # Test OAuth token
        print(f"\n3️⃣ Testing OAuth token generation...")
        try:
            token = gateway.get_access_token()
            if token:
                print(f"✅ OAuth token generated: {token[:20]}...")
                
                # Test API call with token
                print(f"\n4️⃣ Testing authenticated API call...")
                import requests
                
                test_url = f"{gateway.payment_base_url}/apis/hermes/pg/v1/status/{gateway.merchant_id}/TEST123"
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/json',
                    'X-MERCHANT-ID': gateway.merchant_id
                }
                
                response = requests.get(test_url, headers=headers, timeout=10)
                print(f"   API call status: {response.status_code}")
                
                if response.status_code in [200, 404]:  # 404 expected for non-existent transaction
                    print("   ✅ Authentication working correctly")
                    return True
                else:
                    print(f"   ⚠️ Unexpected response: {response.text[:100]}...")
                    return False
            else:
                print("❌ Failed to generate OAuth token")
                return False
                
        except Exception as token_error:
            print(f"❌ OAuth token error: {str(token_error)}")
            return False
        
    except Exception as e:
        print(f"❌ Gateway test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_configuration():
    """Check PhonePe configuration"""
    
    print("\n📋 PhonePe Configuration Check")
    print("=" * 40)
    
    config_items = [
        ('PHONEPE_CLIENT_ID', getattr(settings, 'PHONEPE_CLIENT_ID', 'NOT SET')),
        ('PHONEPE_CLIENT_SECRET', '***' if hasattr(settings, 'PHONEPE_CLIENT_SECRET') else 'NOT SET'),
        ('PHONEPE_AUTH_BASE_URL', getattr(settings, 'PHONEPE_AUTH_BASE_URL', 'NOT SET')),
        ('PHONEPE_PAYMENT_BASE_URL', getattr(settings, 'PHONEPE_PAYMENT_BASE_URL', 'NOT SET')),
        ('PHONEPE_MERCHANT_ID', getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT SET')),
        ('PHONEPE_CALLBACK_URL', getattr(settings, 'PHONEPE_CALLBACK_URL', 'NOT SET')),
    ]
    
    all_configured = True
    
    for key, value in config_items:
        if value == 'NOT SET':
            print(f"❌ {key}: {value}")
            all_configured = False
        else:
            print(f"✅ {key}: {value}")
    
    if all_configured:
        print("\n✅ All PhonePe configuration items are set")
    else:
        print("\n❌ Some PhonePe configuration items are missing")
    
    return all_configured

def main():
    """Main test function"""
    
    print("🧪 PhonePe Gateway HTTP 400 Fix Verification")
    print("=" * 60)
    
    # Check configuration
    config_ok = check_configuration()
    
    if not config_ok:
        print("\n❌ Configuration issues found")
        return False
    
    # Test gateway
    gateway_ok = test_gateway_directly()
    
    if gateway_ok:
        print(f"\n🎉 SUCCESS: PhonePe Gateway is working correctly!")
        print(f"\n✅ The HTTP 400 error fix is working!")
        print(f"\n📋 Fixed Issues:")
        print(f"   1. ✅ Corrected API base URLs")
        print(f"   2. ✅ Fixed OAuth2 endpoint path")
        print(f"   3. ✅ Updated payment endpoint path")
        print(f"   4. ✅ Configured proper authentication")
        
        return True
    else:
        print(f"\n❌ FAILED: Gateway still has issues")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🚀 Ready to test payment with cart ID 40!")
        print(f"   Run: python test_cart_40.py")
    else:
        print(f"\n🔧 Additional configuration needed")
        
    sys.exit(0 if success else 1)
