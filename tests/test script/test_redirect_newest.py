#!/usr/bin/env python
import os
import django

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_redirect_newest():
    print("🔗 TESTING REDIRECT FOR NEWEST CART")
    print("="*50)
    
    from django.test import Client
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken
    
    try:
        # Get user and create token
        User = get_user_model()
        user = User.objects.get(phone="+919876543210")
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Create client and make request
        client = Client()
        
        # Test redirect endpoint
        response = client.get('/api/payments/redirect/simple/', 
                            HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        print(f"📍 Redirect Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Location: {response.get('Location', 'No redirect')}")
        
        if response.status_code == 302:
            redirect_url = response.get('Location', '')
            if 'd7a594ac-9333-4213-985f-67942a3b638b' in redirect_url:
                print(f"   ✅ SUCCESS: Redirecting to NEWEST cart!")
            elif '33dd806a-6989-47f5-a840-e588a73e11eb' in redirect_url:
                print(f"   ❌ ISSUE: Still redirecting to OLD cart")
            else:
                print(f"   ⚠️ Redirecting to unknown cart")
                
        # Test booking API for newest cart
        print(f"\n📋 Testing Booking API for newest cart:")
        newest_cart_id = 'd7a594ac-9333-4213-985f-67942a3b638b'
        
        booking_response = client.get(f'/api/booking/bookings/by-cart/{newest_cart_id}/',
                                    HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        print(f"   Status: {booking_response.status_code}")
        if booking_response.status_code == 200:
            booking_data = booking_response.json()
            print(f"   Booking ID: {booking_data.get('book_id')}")
            print(f"   Status: {booking_data.get('status')}")
            print(f"   Amount: ₹{booking_data.get('total_amount')}")
            print(f"   ✅ Booking API working for newest cart!")
        else:
            print(f"   ❌ Booking API failed: {booking_response.content}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_redirect_newest()
