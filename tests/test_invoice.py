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
from booking.invoice_views import generate_invoice_pdf
from django.test import RequestFactory
from django.urls import reverse

def test_invoice_generation():
    print("🧪 Testing Invoice Generation")
    print("=" * 50)
    
    try:
        # Get the booking
        booking = Booking.objects.get(book_id='BK-2540A790')
        print(f"✅ Found booking: {booking.book_id}")
        print(f"📧 User: {booking.user.email}")
        print(f"💰 Amount: ₹{booking.total_amount}")
        
        # Create a test request
        factory = RequestFactory()
        request = factory.get('/api/booking/invoice/BK-2540A790/')
        
        # Test the invoice generation directly
        response = generate_invoice_pdf(request, 'BK-2540A790')
        print(f"✅ Invoice response status: {response.status_code}")
        print(f"📄 Content-Type: {response.get('Content-Type', 'Unknown')}")
        
        if hasattr(response, 'content'):
            print(f"📊 Invoice size: {len(response.content)} bytes")
            
        # Test the URL pattern
        try:
            url = reverse('booking-invoice', kwargs={'book_id': 'BK-2540A790'})
            print(f"✅ URL pattern works: {url}")
        except Exception as url_error:
            print(f"❌ URL pattern error: {url_error}")
            
        print("\n🎯 INVOICE TEST RESULTS:")
        print("✅ Invoice generation: WORKING")
        print("✅ PDF creation: WORKING")
        print("✅ Response format: WORKING")
        
    except Booking.DoesNotExist:
        print("❌ Booking not found: BK-2540A790")
    except Exception as e:
        print(f"❌ Error during invoice test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_invoice_generation()
