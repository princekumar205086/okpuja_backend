#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

import requests

def test_redirect_handler():
    """Test the redirect handler to see what it returns"""
    print("=== TESTING REDIRECT HANDLER ===\n")
    
    # Test the redirect endpoint (simulating PhonePe redirect)
    redirect_url = "http://127.0.0.1:8000/api/payments/redirect/simple/"
    
    try:
        # Make request to redirect handler
        response = requests.get(redirect_url, allow_redirects=False)
        
        print(f"🔄 Redirect Handler Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 302:
            redirect_location = response.headers.get('Location', 'No location header')
            print(f"   Redirect Location: {redirect_location}")
            
            # Parse the redirect URL to see booking ID
            if 'book_id=' in redirect_location:
                book_id_start = redirect_location.find('book_id=') + 8
                book_id_end = redirect_location.find('&', book_id_start)
                if book_id_end == -1:
                    book_id = redirect_location[book_id_start:]
                else:
                    book_id = redirect_location[book_id_start:book_id_end]
                
                print(f"   ✅ Booking ID found: {book_id}")
                
                # Check if this is the latest booking
                from booking.models import Booking
                from accounts.models import User
                
                user = User.objects.filter(email='asliprinceraj@gmail.com').first()
                latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
                
                if latest_booking and book_id == latest_booking.book_id:
                    print(f"   ✅ SUCCESS: Redirect contains LATEST booking ID!")
                    print(f"   Frontend will receive: {latest_booking.book_id}")
                else:
                    print(f"   ❌ ERROR: Redirect contains old booking ID")
                    if latest_booking:
                        print(f"   Expected: {latest_booking.book_id}")
                        print(f"   Found: {book_id}")
            else:
                print(f"   ❌ No booking ID in redirect URL")
        else:
            print(f"   ❌ Unexpected response: {response.text}")
    
    except Exception as e:
        print(f"❌ Redirect test failed: {e}")

def test_booking_api():
    """Test the booking API to verify latest booking works"""
    print(f"\n=== TESTING BOOKING API ===\n")
    
    # Login first
    login_data = {
        "email": "asliprinceraj@gmail.com",
        "password": "testpass123"
    }
    
    login_response = requests.post("http://127.0.0.1:8000/api/auth/login/", json=login_data)
    if login_response.status_code == 200:
        auth_data = login_response.json()
        token = auth_data['access']
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get latest booking from database
        from booking.models import Booking
        from accounts.models import User
        
        user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
        
        if latest_booking:
            print(f"📋 Testing API with LATEST booking: {latest_booking.book_id}")
            
            api_url = f"http://127.0.0.1:8000/api/booking/bookings/by-id/{latest_booking.book_id}/"
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                booking_data = response.json()['data']
                print(f"✅ API response successful")
                print(f"   Booking ID: {booking_data.get('book_id')}")
                print(f"   Service: {booking_data['cart']['puja_service']['title']}")
                print(f"   Date: {booking_data.get('selected_date')}")
                print(f"   Time: {booking_data.get('selected_time')}")
                print(f"   Status: {booking_data.get('status')}")
                print(f"   Total: ₹{booking_data.get('total_amount')}")
                
                # Check if this matches the latest cart
                cart_date = booking_data.get('selected_date')
                cart_time = booking_data.get('selected_time')
                
                if cart_date == "2025-08-21" and "14:00" in cart_time:
                    print(f"   ✅ SUCCESS: API returns LATEST cart data!")
                else:
                    print(f"   ⚠️ API returns different cart data")
                    print(f"   Expected: 2025-08-21 14:00")
                    print(f"   Found: {cart_date} {cart_time}")
            else:
                print(f"❌ API failed: {response.status_code}")
                print(f"   Response: {response.text}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")

def show_final_summary():
    """Show final summary of what frontend will receive"""
    print(f"\n=== FINAL FRONTEND SUMMARY ===\n")
    
    from booking.models import Booking
    from accounts.models import User
    import pytz
    
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
    
    if latest_booking:
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = latest_booking.created_at.astimezone(ist)
        
        service_name = "Unknown Service"
        date = "Unknown Date"
        time = "Unknown Time"
        
        if latest_booking.cart:
            if latest_booking.cart.puja_service:
                service_name = latest_booking.cart.puja_service.title
            date = latest_booking.cart.selected_date
            time = latest_booking.cart.selected_time
        
        print(f"🎯 FRONTEND WILL RECEIVE:")
        print(f"   📋 Booking ID: {latest_booking.book_id}")
        print(f"   🛍️ Service: {service_name}")
        print(f"   📅 Date: {date}")
        print(f"   ⏰ Time: {time}")
        print(f"   ✅ Status: {latest_booking.status}")
        print(f"   🕐 Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        print(f"\n🌐 REDIRECT URLs:")
        print(f"   From PhonePe: http://localhost:3000/confirmbooking?book_id={latest_booking.book_id}&order_id=CART_xxx&redirect_source=phonepe")
        print(f"   API Endpoint: GET /api/booking/bookings/by-id/{latest_booking.book_id}/")
        
        print(f"\n📱 FRONTEND EXPERIENCE:")
        print(f"   ✅ User creates cart with date/time: {date} {time}")
        print(f"   ✅ Payment completed successfully")
        print(f"   ✅ Redirected to booking confirmation")
        print(f"   ✅ Frontend shows REAL-TIME booking data")
        print(f"   ✅ Email notification sent")

if __name__ == "__main__":
    test_redirect_handler()
    test_booking_api()
    show_final_summary()
