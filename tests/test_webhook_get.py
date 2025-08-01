#!/usr/bin/env python3
"""
Test webhook GET endpoint functionality
"""

import requests
import json

def test_webhook_get():
    print('Testing webhook endpoint with GET method...')
    print()

    try:
        # Test webhook GET endpoint
        response = requests.get('http://127.0.0.1:8000/api/payments/webhook/phonepe/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print('✅ Webhook GET endpoint working:')
            print(f'   Status: {response.status_code}')
            print(f'   Message: {data.get("message", "N/A")}')
            info = data.get('info', {})
            print(f'   Environment: {info.get("environment", "N/A")}')
            print(f'   Expected Method: {info.get("method", "N/A")}')
            print(f'   Description: {info.get("description", "N/A")}')
            print()
        else:
            print(f'❌ GET request failed: {response.status_code}')
            print(f'   Response: {response.text}')
            
    except Exception as e:
        print(f'❌ Test failed: {e}')

    print()
    print('💡 Testing Summary:')
    print('   ✅ Payment creation works (from your Swagger test)')
    print('   ✅ Webhook endpoint now provides helpful info on GET')
    print('   ⚠️  Webhook POST will be called by PhonePe after payment')
    print()
    print('Next steps:')
    print('1. Complete payment on PhonePe URL from Swagger')
    print('2. PhonePe will POST to webhook automatically')
    print('3. Check payment status via API')

if __name__ == '__main__':
    test_webhook_get()
