#!/usr/bin/env python
"""
PhonePe Connection Diagnostic Tool
This script will diagnose and fix the PhonePe connection issues
"""

import os
import sys
import django
import json
import requests
import hashlib
import base64
import socket
import urllib3
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

class PhonePeDiagnostics:
    def __init__(self):
        self.merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', '')
        self.merchant_key = getattr(settings, 'PHONEPE_MERCHANT_KEY', '')
        self.salt_index = getattr(settings, 'PHONEPE_SALT_INDEX', 1)
        self.base_url = getattr(settings, 'PHONEPE_BASE_URL', 'https://api.phonepe.com/apis/hermes')
        
    def print_banner(self):
        print("=" * 80)
        print("PhonePe Connection Diagnostic Tool")
        print("=" * 80)
        print()

    def check_environment_config(self):
        print("🔍 STEP 1: Checking Environment Configuration")
        print("-" * 50)
        
        config_items = [
            ('PHONEPE_MERCHANT_ID', self.merchant_id),
            ('PHONEPE_MERCHANT_KEY', self.merchant_key),
            ('PHONEPE_SALT_INDEX', self.salt_index),
            ('PHONEPE_BASE_URL', self.base_url),
            ('PHONEPE_ENV', getattr(settings, 'PHONEPE_ENV', 'UAT')),
            ('PRODUCTION_SERVER', getattr(settings, 'PRODUCTION_SERVER', False)),
        ]
        
        missing_configs = []
        for name, value in config_items:
            if not value or (isinstance(value, str) and value.strip() == ''):
                print(f"❌ {name}: NOT SET")
                missing_configs.append(name)
            else:
                # Mask sensitive data
                display_value = value
                if 'KEY' in name and len(str(value)) > 8:
                    display_value = str(value)[:4] + "*" * (len(str(value)) - 8) + str(value)[-4:]
                print(f"✅ {name}: {display_value}")
        
        print()
        if missing_configs:
            print(f"⚠️  Missing configurations: {', '.join(missing_configs)}")
            return False
        else:
            print("✅ All configurations are set")
            return True

    def check_network_connectivity(self):
        print("🌐 STEP 2: Checking Network Connectivity")
        print("-" * 50)
        
        # Test basic internet connectivity
        test_urls = [
            'https://google.com',
            'https://api.phonepe.com',
            'https://api-preprod.phonepe.com',
            'https://mercury-t2.phonepe.com'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                print(f"✅ {url}: Connected (Status: {response.status_code})")
            except requests.exceptions.ConnectionError:
                print(f"❌ {url}: Connection refused")
            except requests.exceptions.Timeout:
                print(f"⚠️  {url}: Timeout")
            except Exception as e:
                print(f"❌ {url}: Error - {str(e)}")
        
        print()

    def check_dns_resolution(self):
        print("🔍 STEP 3: Checking DNS Resolution")
        print("-" * 50)
        
        hostnames = [
            'api.phonepe.com',
            'api-preprod.phonepe.com',
            'mercury-t2.phonepe.com'
        ]
        
        for hostname in hostnames:
            try:
                ip = socket.gethostbyname(hostname)
                print(f"✅ {hostname}: Resolved to {ip}")
            except socket.gaierror as e:
                print(f"❌ {hostname}: DNS resolution failed - {str(e)}")
        
        print()

    def test_phonepe_endpoints(self):
        print("🚀 STEP 4: Testing PhonePe API Endpoints")
        print("-" * 50)
        
        endpoints = [
            'https://api.phonepe.com/apis/hermes/pg/v1/pay',
            'https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay',
            'https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay'
        ]
        
        # Create a minimal test payload
        test_payload = {
            "merchantId": self.merchant_id or "TEST_MERCHANT",
            "merchantTransactionId": f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "merchantUserId": "TEST_USER",
            "amount": 100,  # 1 rupee in paisa
            "redirectUrl": "https://backend.okpuja.com/api/payments/webhook/phonepe/",
            "redirectMode": "POST",
            "callbackUrl": "https://backend.okpuja.com/api/payments/webhook/phonepe/",
            "mobileNumber": "9000000000",
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
        
        data = base64.b64encode(json.dumps(test_payload).encode()).decode()
        
        # Generate checksum
        checksum_str = data + "/pg/v1/pay" + (self.merchant_key or "TEST_KEY")
        checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + '###' + str(self.salt_index)
        
        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': checksum,
            'X-MERCHANT-ID': self.merchant_id or "TEST_MERCHANT",
            'User-Agent': 'OkPuja-Backend/1.0',
            'Accept': 'application/json'
        }
        
        final_payload = {"request": data}
        
        for endpoint in endpoints:
            print(f"\nTesting: {endpoint}")
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=final_payload,
                    timeout=30,
                    verify=True
                )
                
                print(f"  Status Code: {response.status_code}")
                print(f"  Response: {response.text[:200]}...")
                
                if response.status_code == 200:
                    print(f"  ✅ Endpoint is accessible")
                elif response.status_code == 400:
                    print(f"  ⚠️  Endpoint accessible but request invalid (expected for test data)")
                elif response.status_code == 401:
                    print(f"  ⚠️  Authentication issue - check merchant credentials")
                else:
                    print(f"  ❌ Unexpected response")
                    
            except requests.exceptions.ConnectionError as e:
                print(f"  ❌ Connection Error: {str(e)}")
            except requests.exceptions.Timeout:
                print(f"  ❌ Timeout Error")
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
        
        print()

    def check_server_environment(self):
        print("🖥️  STEP 5: Checking Server Environment")
        print("-" * 50)
        
        print(f"Python Version: {sys.version}")
        print(f"Django Version: {django.get_version()}")
        print(f"Requests Version: {requests.__version__}")
        print(f"Server Time: {datetime.now()}")
        
        # Check if running in production environment
        if hasattr(settings, 'PRODUCTION_SERVER') and settings.PRODUCTION_SERVER:
            print("🏭 Running in PRODUCTION mode")
        else:
            print("🧪 Running in DEVELOPMENT mode")
        
        # Check CORS settings
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        print(f"CORS Origins: {cors_origins}")
        
        print()

    def suggest_fixes(self):
        print("🔧 STEP 6: Suggested Fixes")
        print("-" * 50)
        
        fixes = [
            "1. URL Whitelisting:",
            "   - Frontend URL (https://www.okpuja.com) should be whitelisted ✅",
            "   - Backend URL whitelisting is NOT required for API calls",
            "   - PhonePe needs only your redirect/callback URLs to be accessible",
            "",
            "2. Check Server Firewall:",
            "   - Ensure outbound HTTPS (port 443) is allowed",
            "   - Check if your hosting provider blocks external API calls",
            "",
            "3. DNS and Network:",
            "   - Verify server can resolve api.phonepe.com",
            "   - Test with different PhonePe endpoints",
            "",
            "4. SSL/TLS Issues:",
            "   - Update certificates if needed",
            "   - Try with SSL verification disabled (temporary)",
            "",
            "5. Production Environment:",
            "   - Set PRODUCTION_SERVER=True in environment",
            "   - Use production PhonePe endpoints",
            "   - Verify merchant credentials are for production",
        ]
        
        for fix in fixes:
            print(fix)
        
        print()

    def run_diagnostics(self):
        self.print_banner()
        
        # Run all diagnostic steps
        config_ok = self.check_environment_config()
        self.check_network_connectivity()
        self.check_dns_resolution()
        
        if config_ok and self.merchant_id and self.merchant_key:
            self.test_phonepe_endpoints()
        else:
            print("⚠️  Skipping API tests due to missing configuration")
            print()
        
        self.check_server_environment()
        self.suggest_fixes()
        
        print("=" * 80)
        print("Diagnosis Complete!")
        print("=" * 80)

if __name__ == "__main__":
    diagnostics = PhonePeDiagnostics()
    diagnostics.run_diagnostics()
