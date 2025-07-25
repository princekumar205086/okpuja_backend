#!/usr/bin/env python
"""
PhonePe Connection Diagnostic Script
Identifies network connectivity issues with PhonePe API
"""

import os
import django
import requests
import socket
import json
import base64
import hashlib
import time
from urllib.parse import urlparse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def test_basic_connectivity():
    """Test basic internet connectivity"""
    print("🌐 TESTING BASIC CONNECTIVITY")
    print("=" * 50)
    
    test_urls = [
        "https://www.google.com",
        "https://httpbin.org/get",
        "https://api.github.com"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {str(e)}")

def test_phonepe_connectivity():
    """Test PhonePe API connectivity"""
    print("\n📱 TESTING PHONEPE API CONNECTIVITY")
    print("=" * 50)
    
    phonepe_endpoints = [
        "https://api.phonepe.com",
        "https://api.phonepe.com/apis/hermes",
        "https://api.phonepe.com/apis/hermes/pg/v1/pay",
        "https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay",
        "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
    ]
    
    for endpoint in phonepe_endpoints:
        try:
            print(f"\n🔍 Testing: {endpoint}")
            response = requests.get(endpoint, timeout=30)
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Response: {response.text[:100]}...")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {str(e)}")
        except requests.exceptions.Timeout as e:
            print(f"⏰ Timeout Error: {str(e)}")
        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL Error: {str(e)}")
        except Exception as e:
            print(f"💥 Other Error: {str(e)}")

def test_dns_resolution():
    """Test DNS resolution for PhonePe domains"""
    print("\n🔍 TESTING DNS RESOLUTION")
    print("=" * 50)
    
    domains = [
        "api.phonepe.com",
        "mercury-t2.phonepe.com", 
        "api-preprod.phonepe.com"
    ]
    
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ {domain}: {ip}")
        except Exception as e:
            print(f"❌ {domain}: {str(e)}")

def test_port_connectivity():
    """Test port connectivity to PhonePe servers"""
    print("\n🔌 TESTING PORT CONNECTIVITY")
    print("=" * 50)
    
    test_connections = [
        ("api.phonepe.com", 443),
        ("api.phonepe.com", 80),
        ("mercury-t2.phonepe.com", 443),
    ]
    
    for host, port in test_connections:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ {host}:{port} - Connected")
            else:
                print(f"❌ {host}:{port} - Connection failed (code: {result})")
        except Exception as e:
            print(f"❌ {host}:{port} - Error: {str(e)}")

def test_phonepe_api_call():
    """Test actual PhonePe API call"""
    print("\n📞 TESTING ACTUAL PHONEPE API CALL")
    print("=" * 50)
    
    try:
        # Create a test payload
        merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', 'TEST')
        merchant_key = getattr(settings, 'PHONEPE_MERCHANT_KEY', 'test-key')
        salt_index = getattr(settings, 'PHONEPE_SALT_INDEX', 1)
        
        payload = {
            "merchantId": merchant_id,
            "merchantTransactionId": f"TEST_{int(time.time())}",
            "merchantUserId": "TEST_USER",
            "amount": 100,  # 1 rupee
            "redirectUrl": "https://api.okpuja.com/success",
            "redirectMode": "POST",
            "callbackUrl": "https://api.okpuja.com/api/payments/webhook/phonepe/",
            "mobileNumber": "9999999999",
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
        
        # Encode payload
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        
        # Generate checksum
        string_to_hash = data + "/pg/v1/pay" + merchant_key
        checksum = hashlib.sha256(string_to_hash.encode()).hexdigest()
        final_checksum = f"{checksum}###{salt_index}"
        
        # Prepare request
        final_payload = {"request": data}
        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': final_checksum,
        }
        
        # Test different endpoints
        endpoints = [
            "https://api.phonepe.com/apis/hermes/pg/v1/pay",
            "https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay"
        ]
        
        for endpoint in endpoints:
            print(f"\n🎯 Testing endpoint: {endpoint}")
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=final_payload,
                    timeout=60,
                    verify=True
                )
                
                print(f"✅ Status: {response.status_code}")
                print(f"📄 Response: {response.text[:200]}...")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("🎉 PhonePe API call successful!")
                        return True
                        
            except requests.exceptions.ConnectionError as e:
                print(f"❌ Connection Error: {str(e)}")
            except requests.exceptions.Timeout as e:
                print(f"⏰ Timeout: {str(e)}")
            except Exception as e:
                print(f"💥 Error: {str(e)}")
                
    except Exception as e:
        print(f"💥 Setup Error: {str(e)}")
        
    return False

def check_firewall_and_proxy():
    """Check for firewall/proxy issues"""
    print("\n🔥 CHECKING FIREWALL/PROXY SETTINGS")
    print("=" * 50)
    
    # Check environment variables for proxy
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"🌐 Proxy detected - {var}: {value}")
        else:
            print(f"✅ No proxy - {var}: Not set")
    
    # Test with and without SSL verification
    print("\n🔒 Testing SSL verification:")
    test_url = "https://api.phonepe.com"
    
    try:
        # With SSL verification
        response = requests.get(test_url, timeout=10, verify=True)
        print(f"✅ SSL verification ON: {response.status_code}")
    except Exception as e:
        print(f"❌ SSL verification ON: {str(e)}")
    
    try:
        # Without SSL verification
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(test_url, timeout=10, verify=False)
        print(f"⚠️ SSL verification OFF: {response.status_code}")
    except Exception as e:
        print(f"❌ SSL verification OFF: {str(e)}")

def get_server_info():
    """Get server environment information"""
    print("\n🖥️ SERVER ENVIRONMENT INFO")
    print("=" * 50)
    
    try:
        # Get external IP
        ip_response = requests.get('https://httpbin.org/ip', timeout=10)
        external_ip = ip_response.json().get('origin', 'Unknown')
        print(f"🌐 External IP: {external_ip}")
    except:
        print("❌ Could not determine external IP")
    
    print(f"🐍 Python version: {os.sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔧 Environment: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}")
    
    # Check settings
    print(f"📱 PhonePe Environment: {getattr(settings, 'PHONEPE_ENV', 'Not set')}")
    print(f"🔗 PhonePe Base URL: {getattr(settings, 'PHONEPE_BASE_URL', 'Not set')}")
    print(f"⏰ PhonePe Timeout: {getattr(settings, 'PHONEPE_TIMEOUT', 'Not set')}")

def main():
    print("🚀 PHONEPE CONNECTION DIAGNOSTIC TOOL")
    print("=" * 60)
    print("This script will diagnose connection issues with PhonePe API")
    print("=" * 60)
    
    get_server_info()
    test_basic_connectivity()
    test_dns_resolution()
    test_port_connectivity() 
    check_firewall_and_proxy()
    test_phonepe_connectivity()
    
    print("\n" + "=" * 60)
    print("🔧 ATTEMPTING PHONEPE API CALL")
    print("=" * 60)
    
    success = test_phonepe_api_call()
    
    print("\n" + "=" * 60)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ PhonePe API is accessible!")
        print("💡 The connection issue might be intermittent or configuration-related.")
    else:
        print("❌ PhonePe API is not accessible from this server.")
        print("\n🔧 POSSIBLE SOLUTIONS:")
        print("1. Check hosting provider firewall settings")
        print("2. Verify outbound HTTPS connections are allowed")
        print("3. Check if IP is blocked by PhonePe")
        print("4. Contact hosting provider about API connectivity")
        print("5. Try using a different server or hosting provider")
        print("6. Check if VPN or proxy is interfering")
        
    print("\n📞 Next Steps:")
    print("1. Share this diagnostic report with your hosting provider")
    print("2. Check PhonePe merchant dashboard for IP restrictions")
    print("3. Consider using a reverse proxy or different server")

if __name__ == "__main__":
    main()
