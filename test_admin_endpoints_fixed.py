#!/usr/bin/env python3
"""
Test script to verify all admin endpoint fixes are working correctly
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def get_admin_token():
    """Get JWT token for admin user"""
    try:
        admin_user = User.objects.get(email='admin@okpuja.com')
        refresh = RefreshToken.for_user(admin_user)
        return str(refresh.access_token)
    except User.DoesNotExist:
        print("❌ Admin user not found. Please run create_admin.py first.")
        return None

def test_endpoint(url, method='GET', token=None, data=None):
    """Test an API endpoint"""
    headers = {
        'Content-Type': 'application/json',
    }
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        
        return {
            'status_code': response.status_code,
            'success': response.status_code < 400,
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except requests.exceptions.RequestException as e:
        return {
            'status_code': 0,
            'success': False,
            'error': str(e)
        }

def main():
    """Run comprehensive tests on all admin endpoints"""
    print("🔧 Testing Fixed Admin Endpoints")
    print("=" * 50)
    
    # Base URL
    BASE_URL = "http://127.0.0.1:8000/api"
    
    # Get admin token
    token = get_admin_token()
    if not token:
        return
    
    print(f"✅ Admin token acquired")
    
    # Test endpoints
    endpoints_to_test = [
        # Dashboard endpoints
        {
            'name': 'Astrology Dashboard',
            'url': f'{BASE_URL}/astrology/admin/dashboard/',
            'method': 'GET'
        },
        {
            'name': 'Puja Dashboard', 
            'url': f'{BASE_URL}/puja/admin/dashboard/',
            'method': 'GET'
        },
        {
            'name': 'Booking Dashboard',
            'url': f'{BASE_URL}/booking/admin/dashboard/',
            'method': 'GET'
        },
        
        # Booking list endpoints (to test first_name/last_name fixes)
        {
            'name': 'Astrology Bookings',
            'url': f'{BASE_URL}/astrology/admin/bookings/',
            'method': 'GET'
        },
        {
            'name': 'Puja Bookings',
            'url': f'{BASE_URL}/puja/admin/bookings/',
            'method': 'GET'
        },
        {
            'name': 'Booking Management',
            'url': f'{BASE_URL}/booking/admin/bookings/',
            'method': 'GET'
        },
        
        # Bulk action endpoints (to test URL routing fixes)
        {
            'name': 'Astrology Bulk Actions',
            'url': f'{BASE_URL}/astrology/admin/bookings/bulk-actions/',
            'method': 'POST',
            'data': {
                'booking_ids': [],
                'action': 'update_status',
                'params': {'status': 'CONFIRMED'}
            }
        },
        {
            'name': 'Puja Bulk Actions',
            'url': f'{BASE_URL}/puja/admin/bookings/bulk-actions/',
            'method': 'POST',
            'data': {
                'booking_ids': [],
                'action': 'confirm_bookings',
                'params': {}
            }
        },
        {
            'name': 'Booking Bulk Actions',
            'url': f'{BASE_URL}/booking/admin/bookings/bulk-actions/',
            'method': 'POST',
            'data': {
                'booking_ids': [],
                'action': 'confirm_bookings',
                'params': {}
            }
        },
        
        # Reports endpoints
        {
            'name': 'Astrology Reports',
            'url': f'{BASE_URL}/astrology/admin/reports/',
            'method': 'GET'
        },
        {
            'name': 'Puja Reports',
            'url': f'{BASE_URL}/puja/admin/reports/',
            'method': 'GET'
        },
        {
            'name': 'Booking Reports',
            'url': f'{BASE_URL}/booking/admin/reports/',
            'method': 'GET'
        }
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        print(f"   Method: {endpoint['method']}")
        
        result = test_endpoint(
            endpoint['url'], 
            endpoint['method'], 
            token,
            endpoint.get('data')
        )
        
        results.append({
            'name': endpoint['name'],
            'success': result['success'],
            'status_code': result['status_code'],
            'method': endpoint['method']
        })
        
        if result['success']:
            print(f"   ✅ Status: {result['status_code']} - SUCCESS")
            if endpoint['method'] == 'GET' and isinstance(result.get('data'), dict):
                if 'success' in result['data']:
                    print(f"   📊 Response Success: {result['data']['success']}")
        else:
            print(f"   ❌ Status: {result['status_code']} - FAILED")
            if 'error' in result:
                print(f"   🚨 Error: {result['error']}")
            elif 'data' in result:
                print(f"   🚨 Response: {result['data']}")
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {total-successful}/{total}")
    
    # Group by type
    get_endpoints = [r for r in results if r['method'] == 'GET']
    post_endpoints = [r for r in results if r['method'] == 'POST']
    
    print(f"\n📊 GET Endpoints: {sum(1 for r in get_endpoints if r['success'])}/{len(get_endpoints)}")
    print(f"📊 POST Endpoints: {sum(1 for r in post_endpoints if r['success'])}/{len(post_endpoints)}")
    
    # Show any failures
    failures = [r for r in results if not r['success']]
    if failures:
        print(f"\n❌ Failed Endpoints:")
        for failure in failures:
            print(f"   - {failure['name']} ({failure['status_code']})")
    
    print(f"\n🎉 Testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
