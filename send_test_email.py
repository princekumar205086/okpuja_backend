#!/usr/bin/env python
"""
Send test confirmation email with professional invoice
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from booking.models import Booking
from booking.invoice_views import generate_invoice_pdf_data

def send_test_email():
    """Send test confirmation email"""
    try:
        # Get the real test booking we created
        booking = Booking.objects.filter(book_id='BK-7EDFC3B4').first()
        if not booking:
            # Fallback to the old test booking
            booking = Booking.objects.filter(book_id='BK-08D291CD').first()
            
        if not booking:
            print("ERROR: No test booking found. Run create_real_test_booking.py first.")
            return False
        
        print(f"Sending test email for booking: {booking.book_id}")
        print(f"Customer: {booking.user.email}")
        print(f"Service: {booking.cart.puja_service.title if booking.cart and booking.cart.puja_service else 'N/A'}")
        print(f"Amount: Rs.{booking.total_amount}")
        
        # Check if email was already sent automatically by the booking signal
        from django.core.cache import cache
        cache_key = f"booking_notification_sent_{booking.id}"
        if cache.get(cache_key):
            print("INFO: Confirmation email was already sent automatically when booking was created.")
            print("INFO: This prevents duplicate emails. If you want to test email sending,")
            print("INFO: you can create a new booking or clear the cache.")
            return True
        
        # Use the core task system to send professional email (same as production)
        from core.tasks import send_booking_confirmation
        send_booking_confirmation(booking.id)  # Call directly for testing
        
        print(f"SUCCESS: Test confirmation email sent successfully!")
        print(f"Check your email at: {booking.user.email}")
        print(f"\nYou can also view the invoice online at:")
        print(f"   http://localhost:8000/api/booking/public/invoice/html/{booking.book_id}/")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to send email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("OkPuja - Test Professional Email Confirmation")
    print("=" * 50)
    
    # Check email configuration
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Email Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
    print()
    
    success = send_test_email()
    
    if success:
        print("\nSUCCESS: Test completed successfully!")
        print("Check your email inbox for the professional booking confirmation with invoice.")
    else:
        print("\nERROR: Test failed. Please check the error messages above.")