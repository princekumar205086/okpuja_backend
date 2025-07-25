#!/usr/bin/env python
"""
Test Enhanced PhonePe Gateway
Tests the improved connection handling
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.gateways import get_payment_gateway

def test_enhanced_gateway():
    """Test the enhanced PhonePe gateway"""
    print("🚀 TESTING ENHANCED PHONEPE GATEWAY")
    print("=" * 50)
    
    try:
        # Get the gateway
        gateway = get_payment_gateway('phonepe')
        print(f"✅ Gateway loaded: {type(gateway).__name__}")
        
        # Check enhanced settings
        print(f"⏰ Timeout: {gateway.timeout}s")
        print(f"🔄 Max Retries: {gateway.max_retries}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gateway test failed: {str(e)}")
        return False

def test_direct_api_call():
    """Test direct API call with enhanced settings"""
    print("\n📞 TESTING DIRECT API CALL WITH ENHANCEMENTS")
    print("=" * 50)
    
    try:
        # Configure session like the enhanced gateway
        session = requests.Session()
        
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=10)
        session.mount("https://", adapter)
        
        headers = {
            'User-Agent': 'okpuja-backend/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        }
        
        # Test endpoint
        response = session.get(
            "https://api.phonepe.com/apis/hermes/pg/v1/pay",
            headers=headers,
            timeout=30
        )
        
        print(f"✅ Enhanced request successful: {response.status_code}")
        print(f"📄 Response preview: {response.text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced request failed: {str(e)}")
        return False

def create_production_deployment_script():
    """Create script for production deployment"""
    
    script = '''#!/bin/bash
# Production PhonePe Fix Deployment Script

echo "🚀 Deploying PhonePe Connection Fixes"

# 1. Update environment variables
echo "📝 Updating environment settings..."
echo "PHONEPE_TIMEOUT=180" >> .env
echo "PHONEPE_MAX_RETRIES=7" >> .env
echo "PHONEPE_CONNECTION_POOL_SIZE=10" >> .env
echo "PHONEPE_USER_AGENT=okpuja-backend/1.0" >> .env

# 2. Install/update required packages
echo "📦 Installing required packages..."
pip install --upgrade requests urllib3

# 3. Test network connectivity to PhonePe
echo "🌐 Testing PhonePe connectivity..."
curl -I https://api.phonepe.com/apis/hermes/pg/v1/pay || echo "❌ PhonePe API not accessible"

# 4. Restart services
echo "🔄 Restarting services..."
# sudo systemctl restart your-app-service
# sudo systemctl restart nginx

echo "✅ Deployment complete!"
echo "📞 If issues persist, contact hosting provider about:"
echo "   - Outbound HTTPS connections to api.phonepe.com"
echo "   - Firewall rules for payment gateway APIs"
echo "   - IP whitelisting requirements"
'''
    
    with open('deploy_phonepe_fix.sh', 'w') as f:
        f.write(script)
    
    print("\n📜 Created deployment script: deploy_phonepe_fix.sh")
    return script

def main():
    print("🔧 ENHANCED PHONEPE GATEWAY TESTER")
    print("=" * 60)
    
    # Test enhanced gateway
    gateway_ok = test_enhanced_gateway()
    
    # Test direct API with enhancements
    api_ok = test_direct_api_call()
    
    # Create deployment script
    create_production_deployment_script()
    
    print("\n" + "=" * 60)
    print("📋 ENHANCEMENT SUMMARY")
    print("=" * 60)
    
    if gateway_ok:
        print("✅ Enhanced gateway loaded successfully")
    else:
        print("❌ Gateway loading issues detected")
    
    if api_ok:
        print("✅ Enhanced API calls working")
    else:
        print("❌ API connectivity issues remain")
    
    print("\n🎯 NEXT STEPS:")
    if not api_ok:
        print("1. Deploy to production server and test there")
        print("2. Contact hosting provider about firewall settings")
        print("3. Check server logs for detailed error messages")
        print("4. Consider using a different server or CDN")
    else:
        print("1. Deploy enhanced gateway to production")
        print("2. Monitor payment processing for improvements")
        print("3. Check production logs for connection issues")
    
    print("\n📞 HOSTING PROVIDER CHECKLIST:")
    print("□ Outbound HTTPS to api.phonepe.com allowed")
    print("□ No firewall blocking payment gateway APIs")
    print("□ SSL/TLS properly configured")
    print("□ Server IP not blocked by PhonePe")
    print("□ Network routing properly configured")

if __name__ == "__main__":
    main()
