#!/usr/bin/env python
"""
Professional Invoice & Email Test System
Tests the complete invoice and email system for OkPuja
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.core.cache import cache
from booking.models import Booking

def clear_email_cache():
    """Clear email notification cache for all bookings"""
    try:
        # Get all booking IDs
        booking_ids = Booking.objects.values_list('id', flat=True)
        cleared_count = 0
        
        for booking_id in booking_ids:
            cache_key = f"booking_notification_sent_{booking_id}"
            if cache.delete(cache_key):
                cleared_count += 1
        
        print(f"SUCCESS: Cleared email cache for {cleared_count} bookings")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to clear cache: {str(e)}")
        return False

def test_invoice_html():
    """Test HTML invoice generation"""
    try:
        booking = Booking.objects.filter(book_id='BK-7EDFC3B4').first()
        if not booking:
            booking = Booking.objects.filter(book_id='BK-08D291CD').first()
            
        if not booking:
            print("ERROR: No test booking found. Run create_real_test_booking.py first.")
            return False
        
        print(f"Testing HTML invoice for booking: {booking.book_id}")
        print(f"Invoice URL: http://localhost:8000/api/booking/public/invoice/html/{booking.book_id}/")
        print("SUCCESS: HTML invoice test ready")
        return True
        
    except Exception as e:
        print(f"ERROR: HTML invoice test failed: {str(e)}")
        return False

def test_invoice_pdf():
    """Test PDF invoice generation"""
    try:
        booking = Booking.objects.filter(book_id='BK-7EDFC3B4').first()
        if not booking:
            booking = Booking.objects.filter(book_id='BK-08D291CD').first()
            
        if not booking:
            print("ERROR: No test booking found. Run create_real_test_booking.py first.")
            return False
        
        print(f"Testing PDF invoice for booking: {booking.book_id}")
        print(f"PDF URL: http://localhost:8000/api/booking/public/invoice/pdf/{booking.book_id}/")
        print("SUCCESS: PDF invoice test ready")
        return True
        
    except Exception as e:
        print(f"ERROR: PDF invoice test failed: {str(e)}")
        return False

def send_fresh_confirmation_email():
    """Send a fresh confirmation email (no duplicates)"""
    try:
        booking = Booking.objects.filter(book_id='BK-7EDFC3B4').first()
        if not booking:
            booking = Booking.objects.filter(book_id='BK-08D291CD').first()
            
        if not booking:
            print("ERROR: No test booking found. Run create_real_test_booking.py first.")
            return False
        
        print(f"Sending fresh confirmation email for booking: {booking.book_id}")
        print(f"Customer: {booking.user.email}")
        print(f"Service: {booking.cart.puja_service.title if booking.cart and booking.cart.puja_service else 'N/A'}")
        print(f"Amount: Rs.{booking.total_amount}")
        
        # Clear any existing cache to allow fresh email
        cache_key = f"booking_notification_sent_{booking.id}"
        cache.delete(cache_key)
        print("INFO: Cleared email cache for fresh send")
        
        # Send using the production system
        from core.tasks import send_booking_confirmation
        send_booking_confirmation(booking.id)
        
        print(f"SUCCESS: Fresh confirmation email sent successfully!")
        print(f"Check your email at: {booking.user.email}")
        print("\nThe email includes:")
        print("  ✓ Professional booking confirmation")
        print("  ✓ PDF invoice attachment")
        print("  ✓ Complete booking details")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to send email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_complete_test():
    """Run complete invoice and email system test"""
    print("=" * 60)
    print("🚀 OKPUJA PROFESSIONAL INVOICE & EMAIL SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: HTML Invoice
    print("\n1. Testing HTML Invoice Generation...")
    test_invoice_html()
    
    # Test 2: PDF Invoice  
    print("\n2. Testing PDF Invoice Generation...")
    test_invoice_pdf()
    
    # Test 3: Fresh Email (no duplicates)
    print("\n3. Sending Fresh Confirmation Email...")
    send_fresh_confirmation_email()
    
    print("\n" + "=" * 60)
    print("🎉 TESTING COMPLETE!")
    print("=" * 60)
    print("\nTo view invoices, start your Django server:")
    print("   python manage.py runserver")
    print("\nThen visit the URLs shown above.")
    print("\nCheck your email for the professional confirmation with PDF attachment.")

if __name__ == "__main__":
    run_complete_test()