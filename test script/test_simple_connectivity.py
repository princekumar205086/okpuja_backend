#!/usr/bin/env python3
"""
Simple Production Connectivity Test for PhonePe
Run this on your production server to diagnose connectivity issues
"""

import os
import sys
import socket
import requests
import time
import subprocess
from urllib.parse import urlparse

# Add Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

import django
django.setup()

from django.conf import settings

def test_basic_connectivity():
    """Test basic connectivity to PhonePe"""
    print("🚀 Testing PhonePe Connectivity from Production Server")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        "https://api.phonepe.com/apis/hermes/pg/v1/pay",
        "https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay",
        "https://google.com"  # Control test
    ]
    
    print(f"📍 Server Info:")
    print(f"   PhonePe Merchant ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'Not Set')}")
    print(f"   PhonePe Environment: {getattr(settings, 'PHONEPE_ENV', 'Not Set')}")
    print(f"   Production Flag: {getattr(settings, 'PRODUCTION_SERVER', False)}")
    
    # Test 1: Basic socket connectivity
    print(f"\n🔌 Testing Socket Connectivity...")
    hosts = [("api.phonepe.com", 443), ("google.com", 443)]
    
    for host, port in hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ {host}:{port} - Connection successful")
            else:
                print(f"   ❌ {host}:{port} - Connection failed (error: {result})")
        except Exception as e:
            print(f"   ❌ {host}:{port} - Error: {e}")
    
    # Test 2: HTTP requests
    print(f"\n🌐 Testing HTTP Requests...")
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testing: {endpoint}")
            
            # Basic GET request first
            try:
                response = requests.get(endpoint.replace('/pg/v1/pay', ''), timeout=30)
                print(f"   ✅ GET request successful (Status: {response.status_code})")
            except Exception as e:
                print(f"   ❌ GET request failed: {e}")
            
            # POST request (like PhonePe payment)
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'OkPuja-Backend/1.0',
                'Accept': 'application/json'
            }
            
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json={"test": "connectivity"},
                    timeout=60
                )
                print(f"   ✅ POST request successful (Status: {response.status_code})")
                if response.status_code != 200:
                    print(f"   📝 Response: {response.text[:200]}...")
            except requests.exceptions.ConnectionError as e:
                print(f"   ❌ POST Connection Error: {e}")
                print(f"   🔍 This indicates network/firewall blocking")
            except requests.exceptions.Timeout as e:
                print(f"   ❌ POST Timeout Error: {e}")
                print(f"   🔍 This indicates slow network or server issues")
            except Exception as e:
                print(f"   ❌ POST Request Error: {e}")
                
        except Exception as e:
            print(f"   ❌ General error for {endpoint}: {e}")
    
    # Test 3: Check proxy settings
    print(f"\n🌐 Checking Environment...")
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
    proxy_found = False
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ⚠️  Proxy detected: {var}={value}")
            proxy_found = True
    
    if not proxy_found:
        print(f"   ✅ No proxy settings detected")
    
    # Test 4: Server recommendations
    print(f"\n" + "=" * 60)
    print(f"🔧 Production Server Troubleshooting Guide:")
    print(f"")
    print(f"If you see connection errors above:")
    print(f"1. Check firewall rules - ensure outbound HTTPS (port 443) is allowed")
    print(f"2. Whitelist these domains in your firewall:")
    print(f"   - api.phonepe.com")
    print(f"   - mercury-t2.phonepe.com")
    print(f"3. Check with your hosting provider about:")
    print(f"   - Outbound connection restrictions")
    print(f"   - Corporate firewall/proxy settings")
    print(f"   - DDoS protection that might block API calls")
    print(f"4. Test from server command line:")
    print(f"   curl -v https://api.phonepe.com")
    print(f"5. Check server logs for network-related errors")
    
    print(f"\n📞 If issues persist:")
    print(f"- Contact your hosting provider with this test output")
    print(f"- Ask them to check outbound HTTPS connectivity")
    print(f"- Request whitelisting of PhonePe domains")

if __name__ == "__main__":
    test_basic_connectivity()
