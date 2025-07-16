#!/usr/bin/env python3
"""
Production Connectivity Test Script for PhonePe Integration
Run this on your production server to diagnose connectivity issues
"""

import os
import sys
import socket
import requests
import time
import dns.resolver
from urllib.parse import urlparse
import ssl
import subprocess

# Add Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

import django
django.setup()

from django.conf import settings

class ProductionConnectivityTester:
    def __init__(self):
        self.phonepe_endpoints = [
            "https://api.phonepe.com/apis/hermes/pg/v1/pay",
            "https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay",
            "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
        ]
        
    def test_dns_resolution(self):
        """Test DNS resolution for PhonePe domains"""
        print("🔍 Testing DNS Resolution...")
        domains = ["api.phonepe.com", "mercury-t2.phonepe.com", "api-preprod.phonepe.com"]
        
        for domain in domains:
            try:
                result = dns.resolver.resolve(domain, 'A')
                ips = [str(ip) for ip in result]
                print(f"✅ {domain} resolves to: {', '.join(ips)}")
            except Exception as e:
                print(f"❌ DNS resolution failed for {domain}: {e}")
                
    def test_ping_connectivity(self):
        """Test basic ping connectivity"""
        print("\n🏓 Testing Ping Connectivity...")
        domains = ["api.phonepe.com", "google.com", "cloudflare.com"]
        
        for domain in domains:
            try:
                # Use ping command
                result = subprocess.run(['ping', '-c', '3', domain], 
                                      capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    print(f"✅ Ping to {domain} successful")
                else:
                    print(f"❌ Ping to {domain} failed")
            except Exception as e:
                print(f"❌ Ping test failed for {domain}: {e}")
                
    def test_port_connectivity(self):
        """Test port 443 connectivity"""
        print("\n🔌 Testing Port 443 Connectivity...")
        hosts = [
            ("api.phonepe.com", 443),
            ("mercury-t2.phonepe.com", 443),
            ("google.com", 443)
        ]
        
        for host, port in hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    print(f"✅ Port {port} open on {host}")
                else:
                    print(f"❌ Port {port} closed on {host} (error: {result})")
            except Exception as e:
                print(f"❌ Port test failed for {host}:{port}: {e}")
                
    def test_ssl_certificate(self):
        """Test SSL certificate validity"""
        print("\n🔒 Testing SSL Certificates...")
        hosts = ["api.phonepe.com", "mercury-t2.phonepe.com"]
        
        for host in hosts:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((host, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        cert = ssock.getpeercert()
                        print(f"✅ SSL certificate valid for {host}")
                        print(f"   Subject: {cert.get('subject', 'Unknown')}")
                        print(f"   Issuer: {cert.get('issuer', 'Unknown')}")
            except Exception as e:
                print(f"❌ SSL test failed for {host}: {e}")
                
    def test_http_requests(self):
        """Test actual HTTP requests"""
        print("\n🌐 Testing HTTP Requests...")
        
        # Test simple GET requests first
        test_urls = [
            "https://httpbin.org/get",  # External test service
            "https://api.phonepe.com",  # PhonePe base URL
            "https://google.com"
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=15)
                print(f"✅ GET request to {url} successful (Status: {response.status_code})")
            except requests.exceptions.ConnectionError as e:
                print(f"❌ Connection error to {url}: {e}")
            except requests.exceptions.Timeout as e:
                print(f"❌ Timeout error to {url}: {e}")
            except Exception as e:
                print(f"❌ Request failed to {url}: {e}")
                
    def test_phonepe_endpoints(self):
        """Test PhonePe specific endpoints"""
        print("\n📱 Testing PhonePe Endpoints...")
        
        # Basic headers for PhonePe
        headers = {
            'Content-Type': 'application/json',
            'X-MERCHANT-ID': getattr(settings, 'PHONEPE_MERCHANT_ID', 'TEST'),
            'User-Agent': 'OkPuja-Backend/1.0',
            'Accept': 'application/json'
        }
        
        for endpoint in self.phonepe_endpoints:
            try:
                print(f"\n🔗 Testing endpoint: {endpoint}")
                
                # Try multiple timeout and retry strategies
                timeouts = [30, 60, 90]
                
                for timeout in timeouts:
                    try:
                        print(f"   Timeout: {timeout}s")
                        response = requests.post(
                            endpoint,
                            headers=headers,
                            json={"test": "connectivity"},
                            timeout=timeout
                        )
                        print(f"   ✅ Response received (Status: {response.status_code})")
                        print(f"   Response: {response.text[:200]}...")
                        break
                    except requests.exceptions.ConnectionError as e:
                        print(f"   ❌ Connection error (timeout {timeout}s): {e}")
                        if timeout == timeouts[-1]:
                            raise
                    except requests.exceptions.Timeout as e:
                        print(f"   ❌ Timeout error ({timeout}s): {e}")
                        if timeout == timeouts[-1]:
                            raise
                            
            except Exception as e:
                print(f"   ❌ Endpoint test failed: {e}")
                
    def test_proxy_settings(self):
        """Check if proxy settings are interfering"""
        print("\n🌐 Checking Proxy Settings...")
        
        proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
        for var in proxy_vars:
            value = os.environ.get(var)
            if value:
                print(f"⚠️  Proxy detected: {var}={value}")
            else:
                print(f"✅ No proxy set for {var}")
                
    def test_firewall_trace(self):
        """Test traceroute to PhonePe"""
        print("\n🛣️  Testing Route to PhonePe...")
        
        try:
            result = subprocess.run(['traceroute', 'api.phonepe.com'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Traceroute successful:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            else:
                print(f"❌ Traceroute failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("❌ Traceroute timed out")
        except FileNotFoundError:
            print("⚠️  Traceroute command not found, skipping...")
        except Exception as e:
            print(f"❌ Traceroute error: {e}")
            
    def run_all_tests(self):
        """Run all connectivity tests"""
        print("🚀 Starting Production Connectivity Tests for PhonePe Integration")
        print("=" * 70)
        
        print(f"🏢 Server Environment:")
        print(f"   Python: {sys.version}")
        print(f"   Django: {django.get_version()}")
        print(f"   PhonePe Merchant ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'Not Set')}")
        print(f"   PhonePe Environment: {getattr(settings, 'PHONEPE_ENV', 'Not Set')}")
        print(f"   Production Server Flag: {getattr(settings, 'PRODUCTION_SERVER', False)}")
        
        # Run all tests
        self.test_dns_resolution()
        self.test_ping_connectivity()
        self.test_port_connectivity()
        self.test_ssl_certificate()
        self.test_proxy_settings()
        self.test_http_requests()
        self.test_phonepe_endpoints()
        self.test_firewall_trace()
        
        print("\n" + "=" * 70)
        print("🏁 Connectivity tests completed!")
        print("\n📋 Summary & Recommendations:")
        print("1. If DNS resolution fails: Check your server's DNS settings")
        print("2. If ping fails: Check network connectivity and firewall rules")
        print("3. If port 443 is closed: Check outbound firewall rules")
        print("4. If SSL fails: Check certificate trust store")
        print("5. If HTTP requests fail: Check proxy settings and firewall")
        print("6. If PhonePe endpoints fail: Contact your hosting provider")
        
        print("\n🔧 Production Server Checklist:")
        print("- Ensure outbound HTTPS (port 443) is allowed")
        print("- Whitelist PhonePe domains in firewall")
        print("- Check if corporate proxy is blocking requests")
        print("- Verify DNS resolution is working")
        print("- Contact hosting provider if issues persist")

if __name__ == "__main__":
    tester = ProductionConnectivityTester()
    tester.run_all_tests()
