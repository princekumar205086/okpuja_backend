#!/usr/bin/env python
"""
CORS Test Script for OkPuja Backend
This script will validate CORS configuration in your Django server
"""

import os
import sys
import django
import json
import requests

# Set up Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def test_cors():
    """Test CORS configuration on the Django server"""
    print("\n========== OKPUJA CORS TEST ==========\n")
    
    # Get the allowed origins from settings
    allowed_origins = settings.CORS_ALLOWED_ORIGINS
    print(f"Configured CORS allowed origins: {allowed_origins}\n")
    
    # Check CORS middleware position
    middleware = settings.MIDDLEWARE
    cors_position = middleware.index('corsheaders.middleware.CorsMiddleware')
    common_position = middleware.index('django.middleware.common.CommonMiddleware')
    
    if cors_position < common_position:
        print("✅ CORS middleware is correctly positioned before CommonMiddleware")
    else:
        print("❌ CORS middleware should be before CommonMiddleware!")
    
    # Check actual server CORS headers
    print("\nTesting CORS headers from actual server responses...")
    
    # You need to have the server running for this test
    server_running = False
    
    try:
        # Test a simple OPTIONS request to an API endpoint
        test_url = "http://localhost:8000/api/puja/services/"
        
        # Make an OPTIONS request with an allowed origin
        headers = {
            'Origin': 'https://www.okpuja.com',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'content-type'
        }
        
        response = requests.options(test_url, headers=headers, timeout=5)
        server_running = True
        
        # Check if CORS headers are present
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        if all(header in response.headers for header in cors_headers):
            print(f"✅ Server is responding with proper CORS headers!")
            print("\nCORS Headers received:")
            for header in cors_headers:
                if header in response.headers:
                    print(f"  - {header}: {response.headers[header]}")
        else:
            print("❌ Server is NOT responding with all required CORS headers!")
            print("\nHeaders received:")
            for header, value in response.headers.items():
                print(f"  - {header}: {value}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to local server. Is the Django server running?")
        print("   Run 'python manage.py runserver' in another terminal to test CORS.")
        server_running = False
    except Exception as e:
        print(f"❌ Error testing CORS: {str(e)}")
    
    # Print recommendations
    print("\n--- RECOMMENDATIONS ---")
    
    if not server_running:
        print("1. Start your Django server with: python manage.py runserver")
        print("2. Run this test script again to check CORS headers")
    else:
        print("1. Check that all your frontend domains are in CORS_ALLOWED_ORIGINS")
        print("2. Ensure 'corsheaders.middleware.CorsMiddleware' is before 'django.middleware.common.CommonMiddleware'")
        print("3. Consider adding CORS_ALLOW_CREDENTIALS = True if using cookies/auth")
    
    print("\nRemember: After changing CORS settings, you must restart your Django server!")
    print("\n========== TEST COMPLETE ==========")

if __name__ == "__main__":
    test_cors()
