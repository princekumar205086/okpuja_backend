#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from booking.invoice_views import public_invoice_pdf
from django.test import RequestFactory
from django.urls import reverse

def test_public_invoice():
    print("🧪 Testing Public Invoice Access")
    print("=" * 50)
    
    try:
        # Get the booking
        booking = Booking.objects.get(book_id='BK-2540A790')
        print(f"✅ Found booking: {booking.book_id}")
        print(f"📧 User: {booking.user.email}")
        print(f"💰 Amount: ₹{booking.total_amount}")
        
        # Create a test request (no authentication)
        factory = RequestFactory()
        request = factory.get('/api/booking/public/invoice/BK-2540A790/')
        
        # Test the public invoice generation
        response = public_invoice_pdf(request, 'BK-2540A790')
        print(f"✅ Public invoice response status: {response.status_code}")
        print(f"📄 Content-Type: {response.get('Content-Type', 'Unknown')}")
        
        if response.status_code == 200:
            print(f"📊 Invoice size: {len(response.content)} bytes")
            print("✅ Public invoice access: WORKING")
        else:
            print(f"❌ Public invoice failed with status: {response.status_code}")
            
        # Test the URL pattern
        try:
            url = reverse('booking-public-invoice', kwargs={'book_id': 'BK-2540A790'})
            print(f"✅ Public URL pattern: {url}")
        except Exception as url_error:
            print(f"❌ URL pattern error: {url_error}")
            
    except Booking.DoesNotExist:
        print("❌ Booking not found: BK-2540A790")
    except Exception as e:
        print(f"❌ Error during public invoice test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_public_invoice()
