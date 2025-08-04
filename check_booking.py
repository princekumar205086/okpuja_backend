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

def check_booking_structure():
    print("🔍 Checking Booking Structure")
    print("=" * 40)
    
    try:
        booking = Booking.objects.get(book_id='BK-2540A790')
        print(f"✅ Found booking: {booking.book_id}")
        
        # Check fields
        fields = [f.name for f in booking._meta.fields]
        print(f"📋 Booking fields: {fields}")
        
        # Check payment details
        print(f"💳 Has payment_details attr: {hasattr(booking, 'payment_details')}")
        
        if hasattr(booking, 'payment_details'):
            payment_details = booking.payment_details
            print(f"💰 Payment details: {payment_details}")
            print(f"💰 Payment details type: {type(payment_details)}")
        
        # Check related fields that might contain payment info
        for field in fields:
            value = getattr(booking, field, None)
            if 'payment' in field.lower() or 'transaction' in field.lower():
                print(f"💳 {field}: {value}")
                
    except Booking.DoesNotExist:
        print("❌ Booking not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_booking_structure()
