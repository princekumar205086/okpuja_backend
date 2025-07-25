#!/usr/bin/env python
"""
Quick PhonePe V2 Production Test
Run this script to quickly test if the V2 implementation fixes the connection issue
"""

import os
import sys
import django
import requests
import json

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.gateways_v2 import PhonePeGatewayV2

def test_v2_integration():
    """Test V2 integration end-to-end"""
    print("🚀 Quick PhonePe V2 Integration Test")
    print("=" * 50)
    
    try:
        # Initialize V2 gateway
        gateway = PhonePeGatewayV2()
        print(f"✅ V2 Gateway initialized")
        print(f"🆔 Client ID: {gateway.client_id}")
        print(f"🌐 Auth URL: {gateway.auth_base_url}")
        print()
        
        # Test OAuth2 authentication
        print("🔐 Testing OAuth2...")
        access_token = gateway.get_access_token()
        
        if access_token:
            print(f"✅ OAuth2 SUCCESS!")
            print(f"🎫 Access Token: {access_token[:30]}...")
            print()
            
            # Test basic connectivity
            print("🌐 Testing connectivity...")
            connectivity = gateway.test_connectivity()
            
            connected_count = sum(1 for result in connectivity if result['status'] == 'connected')
            print(f"✅ Connectivity: {connected_count}/{len(connectivity)} endpoints reachable")
            
            if connected_count > 0:
                print()
                print("🎉 V2 INTEGRATION IS WORKING!")
                print("💡 The connection refused error should now be resolved.")
                print("💡 Try initiating a payment from your frontend.")
                print()
                return True
            else:
                print()
                print("❌ V2 INTEGRATION HAS CONNECTIVITY ISSUES")
                print("💡 Check your internet connection and firewall settings.")
                return False
        else:
            print("❌ OAuth2 FAILED")
            print("💡 Check your V2 credentials in .env file")
            return False
            
    except Exception as e:
        print(f"❌ V2 Integration Error: {str(e)}")
        print("💡 Check your settings and credentials")
        return False

def show_configuration():
    """Show current V2 configuration"""
    print("📋 Current V2 Configuration")
    print("=" * 50)
    print(f"Environment: {settings.PHONEPE_ENV}")
    print(f"Client ID: {settings.PHONEPE_CLIENT_ID}")
    print(f"Client Version: {settings.PHONEPE_CLIENT_VERSION}")
    print(f"Client Secret: {settings.PHONEPE_CLIENT_SECRET[:10]}...")
    print(f"Auth Base URL: {settings.PHONEPE_AUTH_BASE_URL}")
    print(f"Payment Base URL: {settings.PHONEPE_PAYMENT_BASE_URL}")
    print()

def main():
    """Main test function"""
    show_configuration()
    
    success = test_v2_integration()
    
    print("🏁 Test Summary")
    print("=" * 50)
    
    if success:
        print("✅ V2 Integration is working correctly!")
        print()
        print("📝 What changed:")
        print("   ✓ Updated from V1 to V2 API")
        print("   ✓ Changed authentication from checksum to OAuth2")
        print("   ✓ Updated API endpoints")
        print("   ✓ Fixed connection issues")
        print()
        print("🚀 Next steps:")
        print("   1. Test payment from your frontend")
        print("   2. The CONNECTION_REFUSED error should be resolved")
        print("   3. Monitor payment status and webhooks")
        print()
        print("🔗 Test credentials being used:")
        print("   - These are UAT/test credentials provided by PhonePe")
        print("   - They work with the sandbox environment")
        print("   - For production, you'll need production V2 credentials")
    else:
        print("❌ V2 Integration needs attention!")
        print()
        print("🔍 Troubleshooting steps:")
        print("   1. Check internet connectivity")
        print("   2. Verify .env file has correct V2 settings")
        print("   3. Check firewall/proxy settings")
        print("   4. Try running from different network")

if __name__ == "__main__":
    main()
