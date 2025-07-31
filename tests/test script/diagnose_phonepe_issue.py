#!/usr/bin/env python
"""
Comprehensive PhonePe Connection Diagnostic
This will help identify the exact cause of Connection refused error
"""

import os
import sys
import django
import requests
import socket
import json
import base64
import hashlib
import uuid
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

class PhonePeNetworkDiagnostic:
    def __init__(self):
        self.merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', '')
        self.merchant_key = getattr(settings, 'PHONEPE_MERCHANT_KEY', '')
        self.salt_index = getattr(settings, 'PHONEPE_SALT_INDEX', 1)
        
        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
    
    def test_basic_connectivity(self):
        self.print_header("🌐 BASIC NETWORK CONNECTIVITY TEST")
        
        test_urls = [
            'https://google.com',
            'https://httpbin.org/ip',
            'https://8.8.8.8',  # Direct IP test
            'https://api.phonepe.com',
            'https://api-preprod.phonepe.com',
            'https://mercury-t2.phonepe.com'
        ]
        
        results = {}
        for url in test_urls:
            try:
                print(f"Testing {url}...", end=" ")
                response = self.session.get(url, timeout=15, verify=True, allow_redirects=True)
                print(f"✅ OK ({response.status_code})")
                results[url] = {'status': 'success', 'code': response.status_code}
            except requests.exceptions.SSLError as e:
                print(f"🔒 SSL ERROR: {str(e)[:100]}")
                results[url] = {'status': 'ssl_error', 'error': str(e)}
            except requests.exceptions.ConnectionError as e:
                print(f"❌ CONNECTION REFUSED: {str(e)[:100]}")
                results[url] = {'status': 'connection_refused', 'error': str(e)}
            except requests.exceptions.Timeout:
                print(f"⏰ TIMEOUT")
                results[url] = {'status': 'timeout'}
            except Exception as e:
                print(f"❌ ERROR: {str(e)[:100]}")
                results[url] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def test_dns_resolution(self):
        self.print_header("🔍 DNS RESOLUTION TEST")
        
        hostnames = [
            'api.phonepe.com',
            'api-preprod.phonepe.com',
            'mercury-t2.phonepe.com',
            'google.com',
            '8.8.8.8'
        ]
        
        results = {}
        for hostname in hostnames:
            try:
                if hostname == '8.8.8.8':
                    print(f"✅ {hostname} → {hostname} (IP address)")
                    results[hostname] = {'status': 'resolved', 'ip': hostname}
                else:
                    ip = socket.gethostbyname(hostname)
                    print(f"✅ {hostname} → {ip}")
                    results[hostname] = {'status': 'resolved', 'ip': ip}
            except socket.gaierror as e:
                print(f"❌ {hostname} → DNS FAILED: {str(e)}")
                results[hostname] = {'status': 'failed', 'error': str(e)}
        
        return results
    
    def test_port_connectivity(self):
        self.print_header("🔌 PORT CONNECTIVITY TEST")
        
        hosts_ports = [
            ('api.phonepe.com', 443),
            ('api.phonepe.com', 80),
            ('google.com', 443),
            ('8.8.8.8', 53),
        ]
        
        results = {}
        for host, port in hosts_ports:
            try:
                print(f"Testing {host}:{port}...", end=" ")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    print(f"✅ OPEN")
                    results[f"{host}:{port}"] = {'status': 'open'}
                else:
                    print(f"❌ CLOSED/FILTERED")
                    results[f"{host}:{port}"] = {'status': 'closed'}
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                results[f"{host}:{port}"] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def test_phonepe_specific_endpoints(self):
        self.print_header("🎯 PHONEPE SPECIFIC ENDPOINT TESTS")
        
        endpoints = [
            'https://api.phonepe.com/apis/hermes/pg/v1/pay',
            'https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay',
            'https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay'
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                print(f"Testing {endpoint}...")
                
                # Test with OPTIONS first (CORS preflight)
                print(f"  OPTIONS request...", end=" ")
                options_response = self.session.options(endpoint, timeout=20)
                print(f"Status: {options_response.status_code}")
                
                # Test with GET
                print(f"  GET request...", end=" ")
                get_response = self.session.get(endpoint, timeout=20, verify=True)
                print(f"Status: {get_response.status_code}")
                
                # Test with POST
                print(f"  POST request...", end=" ")
                post_response = self.session.post(endpoint, json={}, timeout=20, verify=True)
                print(f"Status: {post_response.status_code}")
                
                results[endpoint] = {
                    'status': 'reachable',
                    'options_status': options_response.status_code,
                    'get_status': get_response.status_code,
                    'post_status': post_response.status_code,
                    'post_response': post_response.text[:200] if post_response.text else ''
                }
                
            except requests.exceptions.ConnectionError as e:
                print(f"  ❌ CONNECTION REFUSED: {str(e)[:100]}")
                results[endpoint] = {'status': 'connection_refused', 'error': str(e)}
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)[:100]}")
                results[endpoint] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def test_phonepe_api_with_real_data(self):
        self.print_header("🧪 PHONEPE API TEST WITH ACTUAL PAYLOAD")
        
        if not self.merchant_id or not self.merchant_key:
            print("❌ Missing PhonePe credentials - skipping API test")
            return {'status': 'skipped', 'reason': 'missing_credentials'}
        
        try:
            # Create a test payload
            payload = {
                "merchantId": self.merchant_id,
                "merchantTransactionId": f"TEST_{uuid.uuid4().hex[:8].upper()}",
                "merchantUserId": "TEST_USER",
                "amount": 100,  # 1 rupee
                "redirectUrl": "https://api.okpuja.com/api/payments/webhook/phonepe/",
                "redirectMode": "POST",
                "callbackUrl": "https://api.okpuja.com/api/payments/webhook/phonepe/",
                "mobileNumber": "9000000000",
                "paymentInstrument": {
                    "type": "PAY_PAGE"
                }
            }
            
            # Encode payload
            data = base64.b64encode(json.dumps(payload).encode()).decode()
            
            # Generate checksum
            checksum_str = data + "/pg/v1/pay" + self.merchant_key
            checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + '###' + str(self.salt_index)
            
            final_payload = {"request": data}
            
            headers = {
                'Content-Type': 'application/json',
                'X-VERIFY': checksum,
                'X-MERCHANT-ID': self.merchant_id,
                'User-Agent': 'OkPuja-Backend/1.0',
                'Accept': 'application/json'
            }
            
            # Test with production endpoint
            api_url = 'https://api.phonepe.com/apis/hermes/pg/v1/pay'
            
            print(f"Testing PhonePe API with real payload...")
            print(f"URL: {api_url}")
            print(f"Merchant ID: {self.merchant_id}")
            print(f"Payload size: {len(json.dumps(final_payload))} bytes")
            print(f"Headers: {json.dumps({k: v for k, v in headers.items() if k != 'X-VERIFY'}, indent=2)}")
            
            response = self.session.post(
                api_url,
                headers=headers,
                json=final_payload,
                timeout=30,
                verify=True
            )
            
            print(f"✅ Response received!")
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response: {response.text[:500]}...")
            
            return {
                'status': 'success',
                'status_code': response.status_code,
                'response': response.text,
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.ConnectionError as e:
            print(f"❌ CONNECTION REFUSED: {str(e)}")
            return {'status': 'connection_refused', 'error': str(e)}
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def test_proxy_and_firewall(self):
        self.print_header("🔥 PROXY & FIREWALL DETECTION")
        
        try:
            # Check environment proxy settings
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            print(f"HTTP_PROXY: {http_proxy or 'Not set'}")
            print(f"HTTPS_PROXY: {https_proxy or 'Not set'}")
            
            # Test different user agents
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'curl/7.68.0',
                'Python-requests/2.28.0',
                'OkPuja-Backend/1.0'
            ]
            
            print("\nTesting different User-Agent strings:")
            for ua in user_agents:
                try:
                    response = self.session.get(
                        'https://httpbin.org/user-agent',
                        headers={'User-Agent': ua},
                        timeout=10
                    )
                    print(f"  {ua[:30]}... → {response.status_code}")
                except Exception as e:
                    print(f"  {ua[:30]}... → ERROR: {str(e)[:50]}")
            
            # Test direct IP access vs domain name
            print("\nTesting IP vs Domain access:")
            try:
                # Get IP of api.phonepe.com
                phonepe_ip = socket.gethostbyname('api.phonepe.com')
                print(f"PhonePe IP: {phonepe_ip}")
                
                # Try accessing by IP (this often fails with SSL, but we'll try)
                try:
                    response = self.session.get(f'https://{phonepe_ip}', timeout=10, verify=False)
                    print(f"  Direct IP access: {response.status_code}")
                except Exception as e:
                    print(f"  Direct IP access: FAILED ({str(e)[:50]})")
                    
            except Exception as e:
                print(f"Could not resolve PhonePe IP: {str(e)}")
                
        except Exception as e:
            print(f"Proxy/Firewall test error: {str(e)}")
    
    def test_system_info(self):
        self.print_header("💻 SYSTEM INFORMATION")
        
        try:
            import platform
            import subprocess
            
            print(f"Python Version: {sys.version}")
            print(f"Platform: {platform.platform()}")
            print(f"Hostname: {socket.gethostname()}")
            print(f"FQDN: {socket.getfqdn()}")
            
            # Check installed packages
            try:
                import pkg_resources
                installed_packages = [d.project_name for d in pkg_resources.working_set]
                key_packages = ['requests', 'urllib3', 'certifi', 'django']
                print(f"\nKey packages installed:")
                for pkg in key_packages:
                    if pkg in installed_packages:
                        version = pkg_resources.get_distribution(pkg).version
                        print(f"  {pkg}: {version}")
                    else:
                        print(f"  {pkg}: NOT INSTALLED")
            except:
                print("Could not check package versions")
            
            # Test if curl works (alternative to requests)
            try:
                print("\nTesting with curl...")
                result = subprocess.run([
                    'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}\\n%{time_total}\\n',
                    '--connect-timeout', '10',
                    '--max-time', '30',
                    'https://api.phonepe.com'
                ], capture_output=True, text=True, timeout=35)
                
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    print(f"  curl to api.phonepe.com: HTTP {lines[0]} in {lines[1]}s")
                else:
                    print(f"  curl output: {result.stdout}")
                    
                if result.stderr:
                    print(f"  curl stderr: {result.stderr}")
                    
            except FileNotFoundError:
                print("  curl not available")
            except Exception as e:
                print(f"  curl error: {str(e)}")
            
            # Check environment variables
            print(f"\nDjango Environment:")
            print(f"  PHONEPE_ENV: {getattr(settings, 'PHONEPE_ENV', 'NOT_SET')}")
            print(f"  PRODUCTION_SERVER: {getattr(settings, 'PRODUCTION_SERVER', False)}")
            print(f"  DEBUG: {getattr(settings, 'DEBUG', True)}")
            print(f"  ALLOWED_HOSTS: {getattr(settings, 'ALLOWED_HOSTS', [])}")
            
        except Exception as e:
            print(f"System info error: {str(e)}")
    
    def run_complete_diagnosis(self):
        print("🚀 PHONEPE CONNECTION DIAGNOSTIC TOOL")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Run all tests
        basic_results = self.test_basic_connectivity()
        dns_results = self.test_dns_resolution()
        port_results = self.test_port_connectivity()
        endpoint_results = self.test_phonepe_specific_endpoints()
        api_results = self.test_phonepe_api_with_real_data()
        self.test_proxy_and_firewall()
        self.test_system_info()
        
        # Analyze results
        self.print_header("📊 DIAGNOSIS SUMMARY")
        
        # Check basic connectivity
        google_works = basic_results.get('https://google.com', {}).get('status') == 'success'
        direct_ip_works = basic_results.get('https://8.8.8.8', {}).get('status') == 'success'
        phonepe_basic = basic_results.get('https://api.phonepe.com', {}).get('status') == 'success'
        
        print(f"Internet connectivity (Google): {'✅ Working' if google_works else '❌ Failed'}")
        print(f"Direct IP connectivity: {'✅ Working' if direct_ip_works else '❌ Failed'}")
        print(f"PhonePe domain reachable: {'✅ Yes' if phonepe_basic else '❌ No'}")
        
        # Check DNS
        dns_working = dns_results.get('api.phonepe.com', {}).get('status') == 'resolved'
        print(f"DNS resolution: {'✅ Working' if dns_working else '❌ Failed'}")
        
        # Check ports
        port_443_open = port_results.get('api.phonepe.com:443', {}).get('status') == 'open'
        print(f"Port 443 (HTTPS): {'✅ Open' if port_443_open else '❌ Blocked'}")
        
        # Check API endpoints
        any_endpoint_working = any(
            result.get('status') == 'reachable' 
            for result in endpoint_results.values()
        )
        print(f"API endpoints reachable: {'✅ Yes' if any_endpoint_working else '❌ No'}")
        
        # API test result
        api_working = api_results.get('status') in ['success']
        print(f"PhonePe API responding: {'✅ Yes' if api_working else '❌ No'}")
        
        # Recommendations
        self.print_header("🔧 DETAILED RECOMMENDATIONS")
        
        if not google_works and not direct_ip_works:
            print("🚨 CRITICAL: Complete network isolation")
            print("   Your server has NO outbound internet connectivity")
            print("   Contact Hostinger immediately - this is a server configuration issue")
            
        elif not google_works and direct_ip_works:
            print("🚨 DNS Issue: Can reach IPs but not domain names")
            print("   DNS resolution is completely broken")
            print("   Ask Hostinger to check/fix DNS settings")
            
        elif google_works and not dns_working:
            print("🚨 PhonePe DNS Issue: General DNS works, but PhonePe domain doesn't resolve")
            print("   This is unusual - possibly DNS filtering")
            print("   Ask Hostinger if they block certain domains")
            
        elif dns_working and not port_443_open:
            print("🚨 Firewall Issue: DNS works but HTTPS port blocked")
            print("   Port 443 is being blocked by firewall")
            print("   Ask Hostinger to:")
            print("   1. Allow outbound connections on port 443")
            print("   2. Whitelist api.phonepe.com")
            print("   3. Check if there's DPI (Deep Packet Inspection) blocking")
            
        elif port_443_open and not phonepe_basic:
            print("🚨 Specific Blocking: Port open but PhonePe specifically blocked")
            print("   This suggests application-level or content filtering")
            print("   Ask Hostinger about:")
            print("   1. Web Application Firewall (WAF) rules")
            print("   2. Content filtering on payment domains")
            print("   3. Geographic restrictions on financial APIs")
            
        elif phonepe_basic and not any_endpoint_working:
            print("🚨 API Path Blocking: Domain reachable but API paths blocked")
            print("   Basic connectivity works but specific API endpoints don't")
            print("   This could be:")
            print("   1. Path-based filtering")
            print("   2. Rate limiting on API calls")
            print("   3. User-Agent based blocking")
            
        elif any_endpoint_working and api_results.get('status') == 'connection_refused':
            print("🚨 Authentication/API Level Issue")
            print("   Endpoints are reachable but API calls fail")
            print("   This could be:")
            print("   1. Invalid API credentials")
            print("   2. API rate limiting")
            print("   3. Request format issues")
            print("   4. PhonePe server-side blocking")
            
        else:
            print("✅ Connectivity Analysis:")
            if api_working:
                print("   🎉 Everything appears to be working!")
                print("   The connection issue might be:")
                print("   1. Intermittent/timing related")
                print("   2. Load balancer issues")
                print("   3. Request-specific problems")
            else:
                print("   ⚠️  Partial connectivity detected")
                print("   Check the detailed logs above for specific failures")
        
        # Specific action items for Hostinger
        self.print_header("📞 HOSTINGER SUPPORT CHECKLIST")
        print("When contacting Hostinger support, provide this information:")
        print("\n1. SPECIFIC ISSUE:")
        print("   'Our Django application cannot connect to api.phonepe.com for payment processing'")
        print("   'Getting Connection refused errors on outbound HTTPS requests'")
        
        print("\n2. TECHNICAL DETAILS:")
        print(f"   - Server hostname: {socket.gethostname()}")
        print(f"   - Target: api.phonepe.com:443")
        print(f"   - Error: Connection refused")
        print(f"   - Application: Django payment gateway")
        
        print("\n3. SPECIFIC REQUESTS:")
        print("   ✓ Verify outbound HTTPS (port 443) is allowed")
        print("   ✓ Whitelist these domains:")
        print("     - api.phonepe.com")
        print("     - api-preprod.phonepe.com")
        print("     - mercury-t2.phonepe.com")
        print("   ✓ Check firewall rules for payment/financial domains")
        print("   ✓ Verify no DPI or content filtering on HTTPS")
        print("   ✓ Test connection from server to api.phonepe.com")
        
        print("\n4. TEST COMMAND FOR HOSTINGER:")
        print("   Ask them to run this from your server:")
        print("   curl -v -H 'User-Agent: OkPuja-Backend/1.0' https://api.phonepe.com/apis/hermes/pg/v1/pay")
        
        print(f"\n{'='*60}")
        print("🏁 DIAGNOSTIC COMPLETED!")
        print("Save this output and share with Hostinger support.")
        print(f"{'='*60}")

if __name__ == "__main__":
    diagnostic = PhonePeNetworkDiagnostic()
    diagnostic.run_complete_diagnosis()
