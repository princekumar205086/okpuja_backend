#!/usr/bin/env python
"""
Test the booking API endpoint with authentication
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from booking.models import Booking
import json

User = get_user_model()

def test_booking_api_with_auth():
    """Test the booking API with proper authentication"""
    print("🔧 Testing Booking API with Authentication")
    print("=" * 60)
    
    # Create a test client
    client = Client()
    
    # Get the test user
    try:
        user = User.objects.get(email="asliprinceraj@gmail.com")
        print(f"Using user: {user.email}")
    except User.DoesNotExist:
        print("❌ Test user not found")
        return
    
    # Login the user
    client.force_login(user)
    
    # Test the booking endpoint
    book_id = "BK-072D32E4"
    url = f"/api/booking/bookings/by-id/{book_id}/"
    
    print(f"Testing URL: {url}")
    
    response = client.get(url)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API Response:")
        print(json.dumps(data, indent=2, default=str))
        
        # Show key booking details
        if data.get('success') and data.get('data'):
            booking = data['data']
            print(f"\n📋 Key Booking Details for Frontend:")
            print(f"- Book ID: {booking.get('book_id')}")
            print(f"- Status: {booking.get('status')}")
            print(f"- Selected Date: {booking.get('selected_date')}")
            print(f"- Selected Time: {booking.get('selected_time')}")
            print(f"- Total Amount: {booking.get('total_amount')}")
            
            # User details
            user_data = booking.get('user', {})
            print(f"- User Email: {user_data.get('email')}")
            
            # Address details
            address_data = booking.get('address', {})
            if address_data:
                print(f"- Address: {address_data}")
            
            # Cart details
            cart_data = booking.get('cart', {})
            if cart_data:
                print(f"- Service Type: {cart_data.get('service_type')}")
                print(f"- Service Name: {cart_data.get('puja_service', {}).get('title') if cart_data.get('puja_service') else 'N/A'}")
            
            return data
    else:
        print(f"❌ Error: {response.content.decode()}")
        return None

def show_api_details():
    """Show complete API details for frontend"""
    print(f"\n🌐 COMPLETE API REFERENCE")
    print("=" * 60)
    
    print(f"📍 ENDPOINT DETAILS:")
    print(f"   URL: GET /api/booking/bookings/by-id/{{book_id}}/")
    print(f"   Example: GET /api/booking/bookings/by-id/BK-072D32E4/")
    print(f"   Authentication: Required (JWT Bearer token)")
    print(f"   Permission: User must own the booking")
    
    print(f"\n📥 REQUEST EXAMPLE:")
    print(f"""
GET /api/booking/bookings/by-id/BK-072D32E4/
Host: localhost:8000
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
""")
    
    print(f"\n📤 SUCCESS RESPONSE (200):")
    print(f"""
{{
  "success": true,
  "data": {{
    "id": 19,
    "book_id": "BK-072D32E4",
    "status": "CONFIRMED",
    "selected_date": "2025-07-31",
    "selected_time": "18:50:00",
    "total_amount": "800.00",
    "created_at": "2025-07-31T18:50:01.865879Z",
    "updated_at": "2025-07-31T18:50:01.865879Z",
    "user": {{
      "id": 2,
      "email": "asliprinceraj@gmail.com",
      "username": "asliprinceraj"
    }},
    "cart": {{
      "id": 18,
      "cart_id": "d89edec9-20b1-4b49-9295-0211d29d6f4f",
      "service_type": "PUJA",
      "total_price": "800.00",
      "puja_service": {{
        "id": 1,
        "title": "Complete Durga Puja Ceremony 1",
        "description": "Complete Durga Puja ceremony at your home..."
      }}
    }},
    "address": {{
      "id": 1,
      "address_line_1": "H-01",
      "city": "Purnia",
      "state": "Bihar",
      "postal_code": "854301"
    }},
    "attachments": []
  }}
}}
""")
    
    print(f"\n❌ ERROR RESPONSES:")
    print(f"""
401 Unauthorized:
{{
  "detail": "Authentication credentials were not provided."
}}

404 Not Found:
{{
  "success": false,
  "message": "Booking not found or you do not have permission to view it"
}}

500 Server Error:
{{
  "success": false,
  "message": "Error retrieving booking: [error details]"
}}
""")

def fix_frontend_url():
    """Show how to fix the frontend URL"""
    print(f"\n🔧 FRONTEND URL FIX:")
    print("=" * 60)
    
    print(f"❌ CURRENT URL (incorrect):")
    print(f"   http://localhost:3000/confirmbooking?=BK-072D32E4")
    
    print(f"\n✅ CORRECT URL OPTIONS:")
    print(f"   Option 1: http://localhost:3000/confirmbooking?book_id=BK-072D32E4")
    print(f"   Option 2: http://localhost:3000/confirmbooking/BK-072D32E4")
    
    print(f"\n📝 JAVASCRIPT TO GET BOOK_ID:")
    print(f"""
// Option 1: From query parameter
const urlParams = new URLSearchParams(window.location.search);
const bookId = urlParams.get('book_id'); // Gets "BK-072D32E4"

// Option 2: From URL path (if using dynamic routes)
const bookId = window.location.pathname.split('/').pop(); // Gets "BK-072D32E4"

// Option 3: Next.js router (recommended)
import {{ useRouter }} from 'next/router';
const router = useRouter();
const bookId = router.query.book_id; // Option 1
// OR
const bookId = router.query.id; // Option 2 (dynamic route [id].js)
""")

if __name__ == "__main__":
    print("🔍 BOOKING API COMPLETE TEST")
    print("Testing booking API endpoint for frontend integration")
    print("=" * 80)
    
    # Test the API with authentication
    response_data = test_booking_api_with_auth()
    
    # Show complete API details
    show_api_details()
    
    # Show frontend URL fix
    fix_frontend_url()
    
    print(f"\n" + "=" * 80)
    print("✅ Complete API reference provided!")
    print("Use this information to integrate with your frontend.")
