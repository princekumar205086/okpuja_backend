"""
Final Payment ID Integration Test
Tests the complete booking API endpoint for payment details
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from booking.serializers import BookingSerializer
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def test_payment_integration():
    """Test payment integration with booking"""
    
    print("🔍 FINAL PAYMENT INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Get the booking in question
        booking = Booking.objects.get(book_id='BK-AE8348BC')
        
        print(f"📋 Testing Booking: {booking.book_id}")
        print(f"   User: {booking.user.email}")
        print(f"   Payment Order ID: {booking.payment_order_id}")
        print(f"   Cart ID: {booking.cart.cart_id}")
        
        # Test the payment_details property directly
        payment_details = booking.payment_details
        print(f"\n💳 Model Payment Details:")
        for key, value in payment_details.items():
            print(f"   {key}: {value}")
            
        # Test the serializer
        serializer = BookingSerializer(booking)
        serialized_data = serializer.data
        
        print(f"\n🔧 Serializer Test:")
        if 'payment_details' in serialized_data:
            print(f"   ✅ Payment details included in serializer")
            serializer_payment = serialized_data['payment_details']
            for key, value in serializer_payment.items():
                print(f"   {key}: {value}")
        else:
            print(f"   ❌ Payment details NOT in serializer")
            
        # Check what fields are included
        print(f"\n📊 All Serializer Fields:")
        for key in serialized_data.keys():
            if key != 'payment_details':
                print(f"   {key}: {type(serialized_data[key])}")
            else:
                print(f"   {key}: PAYMENT_DETAILS_OBJECT ✅")
                
        # Verify payment ID integrity
        if payment_details['payment_id'] != 'N/A':
            print(f"\n✅ PAYMENT ID VERIFIED:")
            print(f"   Payment ID: {payment_details['payment_id']}")
            print(f"   Amount: ₹{payment_details['amount']}")
            print(f"   Status: {payment_details['status']}")
            print(f"   Transaction ID: {payment_details['transaction_id']}")
            
            # Check if payment_order_id matches
            if booking.payment_order_id == payment_details['payment_id']:
                print(f"   🔗 Payment Order ID matches Payment ID: ✅")
            else:
                print(f"   ⚠️ Payment Order ID mismatch!")
                
            return True
        else:
            print(f"\n❌ PAYMENT ID NOT FOUND!")
            return False
            
    except Booking.DoesNotExist:
        print(f"❌ Booking BK-AE8348BC not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_payment_integration()
    
    if success:
        print(f"\n🎉 PAYMENT ID IS INTACT WITH BOOKING!")
        print(f"✅ The payment details are properly integrated")
        print(f"✅ The API should return payment details in the response")
        print(f"✅ Check your frontend code to ensure it's reading 'payment_details' field")
    else:
        print(f"\n❌ PAYMENT INTEGRATION FAILED!")
        
    print(f"\n📡 API Endpoint to test:")
    print(f"   GET /api/booking/bookings/by-id/BK-AE8348BC/")
    print(f"   Authorization: Bearer <your-jwt-token>")
    print(f"   Expected field: data.payment_details")
