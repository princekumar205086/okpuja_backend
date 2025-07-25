#!/usr/bin/env python3
"""
Test the actual payment flow that's failing in production
This will simulate the exact same request that the frontend is making
"""

import requests
import json
import os
from datetime import datetime

def test_payment_flow():
    print("🔍 Testing Actual Payment Flow")
    print("=" * 50)
    
    # Your production API endpoint
    base_url = "https://api.okpuja.com"
    
    # Test the exact endpoint that's failing
    payment_url = f"{base_url}/api/payments/payments/process-cart/"
    
    # Sample payload (adjust based on your actual cart structure)
    payload = {
        "cart_id": 16,  # Using the cart_id from your error
        "payment_method": "phonepe",
        "delivery_address_id": 1,
        "billing_address_id": 1
    }
    
    headers = {
        'Content-Type': 'application/json',
        # Add your JWT token here if you have one
        # 'Authorization': 'Bearer YOUR_JWT_TOKEN_HERE'
    }
    
    print(f"📡 Testing endpoint: {payment_url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        print("🚀 Making request...")
        response = requests.post(
            payment_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📄 Response: {json.dumps(result, indent=2)}")
        else:
            print("❌ ERROR!")
            try:
                error_data = response.json()
                print(f"📄 Error Response: {json.dumps(error_data, indent=2)}")
                
                # Check if it's still the CONNECTION_REFUSED error
                if error_data.get('error_category') == 'CONNECTION_REFUSED':
                    print()
                    print("🔥 STILL GETTING CONNECTION_REFUSED!")
                    print("This means the views.py is still using the old gateway")
                    print()
                    print("🛠️  IMMEDIATE ACTIONS NEEDED:")
                    print("1. Check if views.py was actually updated")
                    print("2. Check if gunicorn actually restarted")
                    print("3. Check if there are multiple Python processes")
                    print("4. Check if there's a cache/import issue")
                    
            except:
                print(f"📄 Raw Response: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        
    print()
    print("🔧 Next Steps:")
    print("1. Run this script on your production server")
    print("2. If still CONNECTION_REFUSED, the views.py update didn't take effect")
    print("3. Check gunicorn processes and restart properly")

def check_gunicorn_processes():
    print("\n🔍 Checking Gunicorn Processes")
    print("=" * 30)
    print("Run these commands on your server:")
    print()
    print("# Check all gunicorn processes")
    print("ps aux | grep gunicorn")
    print()
    print("# Kill all gunicorn processes")
    print("sudo pkill -f gunicorn")
    print()
    print("# Start gunicorn again")
    print("sudo systemctl start gunicorn_api_okpuja")
    print()
    print("# Check status")
    print("sudo systemctl status gunicorn_api_okpuja")

def verify_views_update():
    print("\n🔍 Verify Views.py Update")
    print("=" * 25)
    print("Run these commands on your server:")
    print()
    print("# Check the actual file content")
    print("head -30 payment/views.py | grep -E 'import|from'")
    print()
    print("# Check if V2 gateway is imported")
    print("grep -n 'gateways_v2' payment/views.py")
    print()
    print("# Check git status")
    print("git log -1 --oneline")
    print("git status")

if __name__ == "__main__":
    test_payment_flow()
    check_gunicorn_processes()
    verify_views_update()
    
    print("\n" + "="*60)
    print("🎯 SUMMARY")
    print("="*60)
    print("If you're still getting CONNECTION_REFUSED after:")
    print("✅ V2 gateway test passes")
    print("✅ Code is updated")
    print("✅ Service is restarted")
    print()
    print("Then the issue is likely:")
    print("1. Gunicorn didn't actually restart")
    print("2. Multiple gunicorn processes running")
    print("3. Python import cache issue")
    print("4. Views.py still has old code")
    print()
    print("🚨 FORCE FIX: Kill all gunicorn, clear cache, restart")
