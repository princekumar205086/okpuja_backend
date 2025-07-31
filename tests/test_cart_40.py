#!/usr/bin/env python3
"""
Test script to reproduce the PhonePe API HTTP 400 error with cart ID 40
"""

import requests
import json
import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from cart.models import Cart
from puja.models import PujaService, Package
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_payment_with_cart_40():
    """Test payment processing with cart ID 40"""
    
    # API Configuration
    BASE_URL = "http://127.0.0.1:8000"
    
    # Test credentials from user
    EMAIL = "asliprinceraj@gmail.com"
    PASSWORD = "testpass123"
    CART_ID = 40
    
    print(f"🧪 Testing Payment with Cart ID: {CART_ID}")
    print(f"📧 User Email: {EMAIL}")
    print("=" * 60)
    
    try:
        # Step 1: Login and get token
        print("\n1️⃣ Attempting login...")
        login_url = f"{BASE_URL}/api/accounts/login/"
        login_data = {
            "email": EMAIL,
            "password": PASSWORD
        }
        
        login_response = requests.post(login_url, json=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
            
        login_result = login_response.json()
        token = login_result.get('access_token')
        user_id = login_result.get('user', {}).get('id')
        
        if not token:
            print("❌ No access token received")
            return False
            
        print(f"✅ Login successful - User ID: {user_id}")
        
        # Step 2: Check cart details
        print(f"\n2️⃣ Checking cart details for ID {CART_ID}...")
        
        # Check cart in database
        try:
            cart = Cart.objects.get(id=CART_ID)
            print(f"✅ Cart found: ID={cart.id}, User={cart.user.email}, Total=₹{cart.total_price}")
            
            # Display cart details
            print(f"📦 Cart details:")
            print(f"   - Service Type: {cart.service_type}")
            print(f"   - Status: {cart.status}")
            
            if cart.puja_service:
                print(f"   - Puja Service: {cart.puja_service.name}")
                if cart.package:
                    print(f"   - Package: {cart.package.name}, Price: ₹{cart.package.price}")
            
            if cart.astrology_service:
                print(f"   - Astrology Service: {cart.astrology_service.name}")
                print(f"   - Price: ₹{cart.astrology_service.service_price}")
            
            print(f"   - Selected Date: {cart.selected_date}")
            print(f"   - Selected Time: {cart.selected_time}")
            
            if cart.promo_code:
                print(f"   - Promo Code: {cart.promo_code.code}")
                
        except Cart.DoesNotExist:
            print(f"❌ Cart {CART_ID} not found in database")
            return False
        
        # Step 3: Test payment processing
        print(f"\n3️⃣ Testing payment processing...")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payment_url = f"{BASE_URL}/api/payments/process-cart/"
        payment_data = {
            "cart_id": CART_ID,
            "payment_method": "PHONEPE"
        }
        
        print(f"Request URL: {payment_url}")
        print(f"Request Data: {json.dumps(payment_data, indent=2)}")
        print(f"Headers: {headers}")
        
        payment_response = requests.post(payment_url, json=payment_data, headers=headers)
        print(f"\n📊 Payment Response Status: {payment_response.status_code}")
        print(f"Response Headers: {dict(payment_response.headers)}")
        
        try:
            response_data = payment_response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
            
            # Check for the specific error
            if payment_response.status_code == 400:
                print("\n🔍 Analyzing the 400 error...")
                
                if "debug_info" in response_data:
                    debug_info = response_data["debug_info"]
                    print(f"Error Type: {debug_info.get('error_type')}")
                    print(f"Error Details: {debug_info.get('error_details')}")
                    print(f"Admin Message: {debug_info.get('admin_message')}")
                
                # Test debug connectivity
                print("\n🔧 Testing debug connectivity...")
                debug_url = f"{BASE_URL}/api/payments/payments/debug-connectivity/"
                debug_response = requests.get(debug_url, headers=headers)
                print(f"Debug connectivity status: {debug_response.status_code}")
                
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    print(f"Debug data: {json.dumps(debug_data, indent=2)}")
                
            return response_data
            
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {payment_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def analyze_phonepe_error():
    """Analyze PhonePe configuration and potential issues"""
    
    print("\n🔍 Analyzing PhonePe Configuration...")
    print("=" * 50)
    
    # Check environment variables
    from django.conf import settings
    
    print("Environment Variables:")
    phonepe_vars = [
        'PHONEPE_CLIENT_ID',
        'PHONEPE_CLIENT_SECRET', 
        'PHONEPE_PAYMENT_BASE_URL',
        'PHONEPE_WEBHOOK_URL'
    ]
    
    for var in phonepe_vars:
        value = getattr(settings, var, 'NOT SET')
        if 'SECRET' in var and value != 'NOT SET':
            value = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
        print(f"  {var}: {value}")
    
    # Check PhonePe gateway
    try:
        from payment.gateways_v2 import PhonePeV2Gateway
        
        print("\n🔧 Testing PhonePe Gateway initialization...")
        gateway = PhonePeV2Gateway()
        print(f"✅ Gateway created successfully")
        print(f"Base URL: {gateway.base_url}")
        print(f"Client ID: {gateway.client_id[:10]}..." if gateway.client_id else "None")
        
    except Exception as e:
        print(f"❌ Gateway initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Payment Test with Cart ID 40")
    print("=" * 60)
    
    # First analyze PhonePe configuration
    analyze_phonepe_error()
    
    # Then test the payment
    result = test_payment_with_cart_40()
    
    if result:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
