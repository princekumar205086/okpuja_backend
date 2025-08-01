#!/usr/bin/env python
import os
import sys
import django
import requests
import json
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from accounts.models import User
from cart.models import Cart
from puja.models import PujaService, Package
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
from datetime import date

def test_cart_payment_with_server():
    """Test cart payment flow with detailed error handling"""
    
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            email="asliprinceraj@gmail.com",
            defaults={
                'username': 'asliprinceraj@gmail.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            
        print(f"✅ User found/created: {user.email}")
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        print(f"✅ JWT token generated")
        
        # Get or create a service and package
        service = PujaService.objects.filter(title__icontains='test').first()
        if not service:
            service = PujaService.objects.create(
                title="Test Service",
                description="Test service for payment",
                category="Test",
                is_active=True
            )
        
        package = Package.objects.filter(puja_service=service).first()
        if not package:
            package = Package.objects.create(
                puja_service=service,
                title="Basic Package",
                description="Basic test package",
                price=1000,
                duration_minutes=60,
                is_active=True
            )
        
        # Create or get cart
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            cart = Cart.objects.create(
                user=user,
                puja_service=service,
                package=package,
                selected_date=date.today(),
                selected_time="10:00 AM",
                cart_id=str(uuid.uuid4())
            )
        print(f"✅ Cart found/created: {cart.id}")
        print(f"✅ Cart total: ₹{cart.total_price}")
        
        # Test API call
        base_url = "http://127.0.0.1:8000"
        endpoint = f"{base_url}/api/payments/cart/"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'cart_id': cart.cart_id  # Use cart_id field, not database ID
        }
        
        print(f"\n🔍 Testing API call...")
        print(f"URL: {endpoint}")
        print(f"Headers: {headers}")
        print(f"Payload: {payload}")
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            
            print(f"\n📤 Response Status: {response.status_code}")
            print(f"📤 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ Error {response.status_code}")
                print(f"📤 Response Content: {response.text}")
                
                # Try to parse as JSON
                try:
                    error_data = response.json()
                    print(f"📤 Error JSON: {json.dumps(error_data, indent=2)}")
                except:
                    print("📤 Response is not JSON")
                
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Cart Payment API...")
    success = test_cart_payment_with_server()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
