#!/usr/bin/env python
"""
Test the booking API endpoint for frontend integration
"""
import requests
import json

def test_booking_api():
    """Test the booking API endpoint"""
    print("🔧 Testing Booking API Endpoint")
    print("=" * 50)
    
    # Test data
    base_url = "http://127.0.0.1:8000"
    book_id = "BK-072D32E4"
    
    # API endpoint
    api_url = f"{base_url}/api/booking/bookings/by-id/{book_id}/"
    
    print(f"Testing URL: {api_url}")
    
    try:
        # Make API request (you'll need authentication headers in real frontend)
        headers = {
            'Content-Type': 'application/json',
            # In real frontend, you'll need:
            # 'Authorization': 'Bearer YOUR_JWT_TOKEN'
        }
        
        response = requests.get(api_url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(json.dumps(data, indent=2))
            
            # Show key booking details
            if data.get('success') and data.get('data'):
                booking = data['data']
                print(f"\n📋 Booking Details:")
                print(f"- Book ID: {booking.get('book_id')}")
                print(f"- Status: {booking.get('status')}")
                print(f"- Date: {booking.get('selected_date')}")
                print(f"- Time: {booking.get('selected_time')}")
                print(f"- Total Amount: {booking.get('total_amount')}")
                print(f"- User: {booking.get('user', {}).get('email')}")
                
        elif response.status_code == 401:
            print("❌ Authentication required")
            print("You need to include authentication headers")
            
        elif response.status_code == 404:
            print("❌ Booking not found or permission denied")
            
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Django server")
        print("Make sure Django server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def show_frontend_integration():
    """Show how to integrate with frontend"""
    print(f"\n🌐 FRONTEND INTEGRATION GUIDE")
    print("=" * 50)
    
    print(f"1. API Endpoint:")
    print(f"   GET /api/booking/bookings/by-id/{{book_id}}/")
    print(f"   Example: /api/booking/bookings/by-id/BK-072D32E4/")
    
    print(f"\n2. JavaScript/TypeScript Example:")
    print(f"""
const fetchBookingDetails = async (bookId) => {{
  try {{
    const response = await fetch(
      `http://localhost:8000/api/booking/bookings/by-id/${{bookId}}/`,
      {{
        method: 'GET',
        headers: {{
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${{localStorage.getItem('access_token')}}`, // Your JWT token
        }},
      }}
    );
    
    if (!response.ok) {{
      throw new Error(`HTTP error! status: ${{response.status}}`);
    }}
    
    const data = await response.json();
    
    if (data.success) {{
      return data.data; // Booking details
    }} else {{
      throw new Error(data.message);
    }}
  }} catch (error) {{
    console.error('Error fetching booking:', error);
    throw error;
  }}
}};

// Usage in your confirm booking page
const bookId = new URLSearchParams(window.location.search).get('book_id') || 'BK-072D32E4';
fetchBookingDetails(bookId)
  .then(booking => {{
    // Update UI with booking details
    console.log('Booking details:', booking);
  }})
  .catch(error => {{
    // Handle error (show error message)
    console.error('Failed to load booking:', error);
  }});
""")
    
    print(f"\n3. Next.js Example (pages or app router):")
    print(f"""
// pages/confirmbooking.js or app/confirmbooking/page.js
import {{ useRouter }} from 'next/router';
import {{ useState, useEffect }} from 'react';

export default function ConfirmBooking() {{
  const router = useRouter();
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Get book_id from URL query
  const bookId = router.query.book_id || 'BK-072D32E4';
  
  useEffect(() => {{
    const fetchBooking = async () => {{
      try {{
        const response = await fetch(
          `http://localhost:8000/api/booking/bookings/by-id/${{bookId}}/`,
          {{
            headers: {{
              'Authorization': `Bearer ${{localStorage.getItem('access_token')}}`,
            }},
          }}
        );
        
        const data = await response.json();
        
        if (data.success) {{
          setBooking(data.data);
        }} else {{
          setError(data.message);
        }}
      }} catch (err) {{
        setError('Failed to load booking details');
      }} finally {{
        setLoading(false);
      }}
    }};
    
    if (bookId) {{
      fetchBooking();
    }}
  }}, [bookId]);
  
  if (loading) return <div>Loading booking details...</div>;
  if (error) return <div>Error: {{error}}</div>;
  if (!booking) return <div>Booking not found</div>;
  
  return (
    <div>
      <h1>Booking Confirmation</h1>
      <div>
        <h2>Booking ID: {{booking.book_id}}</h2>
        <p>Status: {{booking.status}}</p>
        <p>Date: {{booking.selected_date}}</p>
        <p>Time: {{booking.selected_time}}</p>
        <p>Total Amount: ₹{{booking.total_amount}}</p>
        <p>Service: {{booking.service_name}}</p>
      </div>
    </div>
  );
}}
""")

if __name__ == "__main__":
    print("🔍 BOOKING API ENDPOINT TEST")
    print("Testing the booking details API for frontend integration")
    print("=" * 70)
    
    # Test the API
    test_booking_api()
    
    # Show integration guide
    show_frontend_integration()
    
    print(f"\n" + "=" * 70)
    print("✅ Integration guide complete!")
    print("Use the provided code examples in your frontend application.")
