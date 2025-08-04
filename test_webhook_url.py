#!/usr/bin/env python
"""
Test Webhook URL Accessibility
Verify the correct webhook URL configuration
"""

import os
import sys
import django
import requests
from urllib.parse import urljoin

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from django.test import Client
from django.urls import reverse

def test_webhook_url_construction():
    """Test how the webhook URL should be constructed"""
    print("🔧 Webhook URL Configuration Analysis")
    print("=" * 60)
    
    # From your URL patterns:
    # okpuja_backend/urls.py: path('api/payments/', include('payments.urls'))
    # payments/urls.py: path('webhook/phonepe/', views.PhonePeWebhookView.as_view())
    
    # This creates: /api/payments/webhook/phonepe/
    
    print("📋 URL Pattern Analysis:")
    print("Main URLs: api/payments/ -> payments.urls")
    print("Payment URLs: webhook/phonepe/ -> PhonePeWebhookView")
    print("Combined: /api/payments/webhook/phonepe/")
    
    # Check your domains
    allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
    print(f"\n🌐 Configured Domains: {allowed_hosts}")
    
    # API domain check
    if 'api.okpuja.com' in allowed_hosts:
        webhook_url = "https://api.okpuja.com/api/payments/webhook/phonepe/"
        print(f"✅ API Domain Webhook: {webhook_url}")
        return webhook_url
    elif 'www.okpuja.com' in allowed_hosts:
        webhook_url = "https://www.okpuja.com/api/payments/webhook/phonepe/"
        print(f"✅ WWW Domain Webhook: {webhook_url}")
        return webhook_url
    else:
        print("❌ No production domain found in ALLOWED_HOSTS")
        return None

def test_local_webhook():
    """Test webhook endpoint locally"""
    print("\n🧪 Testing Local Webhook Endpoint")
    print("-" * 40)
    
    try:
        client = Client()
        
        # Test GET request (should return method info)
        response = client.get('/api/payments/webhook/phonepe/')
        print(f"GET /api/payments/webhook/phonepe/ -> Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook endpoint is accessible")
            try:
                import json
                data = json.loads(response.content)
                print(f"Response: {data}")
            except:
                print(f"Response: {response.content.decode()[:100]}...")
        else:
            print(f"❌ Webhook endpoint returned: {response.status_code}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        return False

def test_production_accessibility():
    """Test if the production webhook URL is accessible"""
    print("\n🌐 Testing Production Webhook Accessibility")
    print("-" * 40)
    
    # Test both possible URLs
    test_urls = [
        "https://api.okpuja.com/api/payments/webhook/phonepe/",
        "https://www.okpuja.com/api/payments/webhook/phonepe/"
    ]
    
    for url in test_urls:
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ {url} is accessible")
                return url
            elif response.status_code == 404:
                print(f"❌ {url} returns 404 (not found)")
            else:
                print(f"⚠️  {url} returns {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {url} connection failed: {e}")
    
    return None

def main():
    """Run webhook URL tests"""
    print("🔗 PhonePe Webhook URL Configuration Test")
    print("=" * 60)
    
    # Test 1: URL Construction
    recommended_url = test_webhook_url_construction()
    
    # Test 2: Local Accessibility
    local_works = test_local_webhook()
    
    # Test 3: Production Accessibility
    working_url = test_production_accessibility()
    
    # Summary and Recommendations
    print("\n📊 Summary & Recommendations")
    print("=" * 60)
    
    if local_works:
        print("✅ Django webhook endpoint is working locally")
    else:
        print("❌ Django webhook endpoint has issues")
    
    if working_url:
        print(f"✅ Production webhook URL that works: {working_url}")
        print(f"\n🔧 CONFIGURE IN PHONEPE DASHBOARD:")
        print(f"Webhook URL: {working_url}")
        print(f"Username: okpuja_webhook_user")
        print(f"Password: Okpuja2025")
    else:
        print("❌ No working production URL found")
        print("\n🔧 TROUBLESHOOTING NEEDED:")
        print("1. Check if Django server is running on production")
        print("2. Verify domain DNS configuration")
        print("3. Check firewall/proxy settings")
    
    # Environment file recommendation
    if working_url:
        print(f"\n📝 UPDATE YOUR .ENV FILE:")
        print(f"PHONEPE_CALLBACK_URL={working_url}")

if __name__ == "__main__":
    main()
