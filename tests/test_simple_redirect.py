#!/usr/bin/env python
import os
import sys
import django
import requests

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from cart.models import Cart
from booking.models import Booking
from accounts.models import User

def test_simple_redirect_handler():
    """Test the simple redirect handler that finds latest payment"""
    print("=== TESTING SIMPLE REDIRECT HANDLER ===\n")
    
    # Find a user with recent payments
    user = User.objects.filter(
        payment_orders__cart_id__isnull=False
    ).first()
    
    if not user:
        print("❌ No users with cart payments found")
        return
    
    print(f"Testing with user: {user.email}")
    
    # Find user's latest payment
    latest_payment = PaymentOrder.objects.filter(
        user=user,
        cart_id__isnull=False
    ).order_by('-created_at').first()
    
    if not latest_payment:
        print("❌ No cart payments found for user")
        return
    
    print(f"Latest payment: {latest_payment.merchant_order_id}")
    print(f"Payment status: {latest_payment.status}")
    
    # Ensure payment is successful for testing
    if latest_payment.status != 'SUCCESS':
        latest_payment.mark_success(
            phonepe_transaction_id=f'TEST_TXN_{latest_payment.merchant_order_id}',
            phonepe_response={'test': True}
        )
        print(f"✅ Marked payment as successful")
    
    # Test simple redirect handler
    redirect_url = "http://127.0.0.1:8000/api/payments/redirect/simple/"
    
    try:
        # Test without any parameters (simulating PhonePe V2 behavior)
        response = requests.get(redirect_url, allow_redirects=False)
        
        if response.status_code in [302, 301]:
            redirect_location = response.headers.get('Location', '')
            print(f"\n✅ Simple redirect handler working")
            print(f"✅ Redirect location: {redirect_location}")
            
            # Check if book_id is in the redirect URL
            if 'book_id=' in redirect_location:
                print(f"✅ book_id parameter found in redirect URL")
                # Extract book_id for verification
                book_id = redirect_location.split('book_id=')[1].split('&')[0]
                print(f"✅ Book ID: {book_id}")
            else:
                print(f"❌ book_id parameter missing from redirect URL")
                print(f"   This means no booking was found/created")
                
        else:
            print(f"❌ Simple redirect handler failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to redirect handler. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Redirect handler error: {e}")

def force_create_booking_for_latest_payment():
    """Force create booking for latest successful payment"""
    print(f"\n=== ENSURING BOOKING EXISTS ===\n")
    
    # Find latest successful payment
    latest_payment = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    ).order_by('-created_at').first()
    
    if not latest_payment:
        print("❌ No successful payments found")
        return None
    
    print(f"Latest successful payment: {latest_payment.merchant_order_id}")
    
    try:
        cart = Cart.objects.get(cart_id=latest_payment.cart_id)
        booking = Booking.objects.filter(cart=cart).first()
        
        if not booking:
            print("Creating booking for latest payment...")
            from payments.services import WebhookService
            webhook_service = WebhookService()
            booking = webhook_service._create_booking_from_cart(latest_payment)
            
            if booking:
                print(f"✅ Booking created: {booking.book_id}")
                return booking
            else:
                print(f"❌ Failed to create booking")
        else:
            print(f"✅ Booking already exists: {booking.book_id}")
            return booking
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def show_frontend_implementation():
    """Show how to implement frontend handling"""
    print(f"\n=== FRONTEND IMPLEMENTATION GUIDE ===\n")
    
    print("1. UPDATE YOUR FRONTEND TO HANDLE BOTH SCENARIOS:")
    print("""
// In your confirmbooking page component
useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const bookId = urlParams.get('book_id');
    const orderId = urlParams.get('order_id');
    const redirectSource = urlParams.get('redirect_source');
    
    if (bookId) {
        // Scenario 1: We have booking ID - fetch booking details
        fetchBookingDetails(bookId);
    } else if (redirectSource === 'phonepe') {
        // Scenario 2: PhonePe redirect without booking ID - fetch latest booking
        fetchLatestBooking();
    }
}, []);

const fetchBookingDetails = async (bookId) => {
    try {
        const response = await fetch(`/api/booking/get/${bookId}/`, {
            headers: {
                'Authorization': `Bearer ${userToken}`,
            }
        });
        const booking = await response.json();
        if (booking.success) {
            setBookingData(booking.data);
            setLoading(false);
        }
    } catch (error) {
        console.error('Error fetching booking details:', error);
        // Fallback to latest booking
        fetchLatestBooking();
    }
};

const fetchLatestBooking = async () => {
    try {
        // Fetch user's latest booking
        const response = await fetch('/api/booking/latest/', {
            headers: {
                'Authorization': `Bearer ${userToken}`,
            }
        });
        const booking = await response.json();
        if (booking.success && booking.data) {
            setBookingData(booking.data);
        } else {
            setError('No recent booking found');
        }
        setLoading(false);
    } catch (error) {
        console.error('Error fetching latest booking:', error);
        setError('Failed to load booking details');
        setLoading(false);
    }
};
""")
    
    print("\n2. EXPECTED REDIRECT SCENARIOS:")
    print("   ✅ With booking ID: /confirmbooking?book_id=BK-XXX&order_id=CART_XXX")
    print("   ✅ Fallback: /confirmbooking?redirect_source=phonepe&status=no_booking")
    print("   ✅ Error: /confirmbooking?redirect_source=phonepe&error=redirect_error")
    
    print("\n3. API ENDPOINTS YOU NEED:")
    print("   - GET /api/booking/get/{book_id}/ - Get specific booking")
    print("   - GET /api/booking/latest/ - Get user's latest booking")

def show_current_status():
    """Show current successful payments and bookings"""
    print(f"\n=== CURRENT STATUS ===\n")
    
    successful_payments = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    ).order_by('-created_at')[:3]
    
    print("Recent successful payments:")
    for payment in successful_payments:
        try:
            cart = Cart.objects.get(cart_id=payment.cart_id)
            booking = Booking.objects.filter(cart=cart).first()
            
            print(f"\n  Payment: {payment.merchant_order_id}")
            print(f"  Status: {payment.status}")
            print(f"  User: {payment.user.email}")
            print(f"  Booking: {'YES - ' + booking.book_id if booking else 'NO'}")
            
            if booking:
                expected_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}"
                print(f"  Expected URL: {expected_url}")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    force_create_booking_for_latest_payment()
    test_simple_redirect_handler()
    show_frontend_implementation()
    show_current_status()
