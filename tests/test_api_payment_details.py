import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.test import Client
from booking.models import Booking

try:
    # Test the booking model directly
    booking = Booking.objects.get(book_id='BK-AE8348BC')
    payment_details = booking.payment_details
    
    print(f"📋 Direct Model Test:")
    print(f"   Booking ID: {booking.book_id}")
    print(f"   Payment Order ID: {booking.payment_order_id}")
    
    print(f"\n💳 Updated Payment Details:")
    print(f"   Payment ID: {payment_details['payment_id']}")
    print(f"   Amount: ₹{payment_details['amount']}")
    print(f"   Status: {payment_details['status']}")
    print(f"   Transaction ID: {payment_details['transaction_id']}")
    print(f"   Payment Method: {payment_details['payment_method']}")
    
    # Test API endpoint
    client = Client()
    response = client.get('/api/booking/bookings/by-id/BK-AE8348BC/')
    print(f"\n🌐 API Test:")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = response.json()
        if 'data' in data:
            if 'payment_details' in data['data']:
                api_payment_details = data['data']['payment_details']
                print(f"   ✅ Payment details found in API response:")
                print(f"      Payment ID: {api_payment_details['payment_id']}")
                print(f"      Transaction ID: {api_payment_details['transaction_id']}")
            else:
                print(f"   ❌ Payment details NOT in API response")
                print(f"   Available fields: {list(data['data'].keys())}")
        else:
            print(f"   ❌ No data in response")
    else:
        print(f"   ❌ API request failed")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
