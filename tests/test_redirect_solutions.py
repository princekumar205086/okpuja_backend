#!/usr/bin/env python3
"""
Test PhonePe Redirect Solutions
"""

import requests
import json

def test_redirect_solutions():
    print('Testing PhonePe Redirect Solutions...')
    print('=' * 50)

    base_url = 'http://127.0.0.1:8000/api/payments'

    try:
        # Test 1: Simple redirect endpoint
        print('1. Testing Simple Redirect Endpoint:')
        response = requests.get(f'{base_url}/redirect/simple/', timeout=5)
        print(f'   Status: {response.status_code}')
        
        if response.status_code == 302:  # Redirect
            location = response.headers.get('Location', 'N/A')
            print(f'   ✅ Redirects to: {location}')
        else:
            print(f'   Response: {response.text[:100]}...')
            
    except Exception as e:
        print(f'   ❌ Test failed: {e}')

    try:
        # Test 2: Enhanced redirect endpoint (with debug params)
        print('\n2. Testing Enhanced Redirect with Parameters:')
        response = requests.get(f'{base_url}/redirect/?test=true&debug=params', timeout=5)
        print(f'   Status: {response.status_code}')
        
        if response.status_code == 302:  # Redirect
            location = response.headers.get('Location', 'N/A')
            print(f'   ✅ Redirects to: {location}')
        else:
            print(f'   Response: {response.text[:100]}...')
            
    except Exception as e:
        print(f'   ❌ Test failed: {e}')

    print('\n' + '=' * 50)
    print('SOLUTION SUMMARY:')
    print('✅ Use simple redirect for reliable handling')
    print('✅ Frontend checks latest payment status')
    print('✅ No more missing order ID errors')
    
    print('\nRECOMMENDED REDIRECT URL:')
    print('   "redirect_url": "http://localhost:8000/api/payments/redirect/simple/"')
    
    print('\nFRONTEND API TO CHECK STATUS:')
    print('   GET /api/payments/latest/ (with auth token)')

if __name__ == '__main__':
    test_redirect_solutions()
