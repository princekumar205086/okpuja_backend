#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from core.tasks import send_booking_confirmation
from django.conf import settings

def test_email_functionality():
    """Test email functionality and configuration"""
    print("=== TESTING EMAIL FUNCTIONALITY ===\n")
    
    # Check email settings
    print("1. Email Configuration:")
    print(f"   DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
    print(f"   EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'NOT SET')}")
    print(f"   EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'NOT SET')}")
    print(f"   EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'NOT SET')}")
    print(f"   EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')}")
    print(f"   ADMIN_EMAIL: {getattr(settings, 'ADMIN_EMAIL', 'NOT SET')}")
    
    # Find a booking to test with
    booking = Booking.objects.first()
    if not booking:
        print("\n❌ No bookings found to test email with")
        return
    
    print(f"\n2. Testing with booking: {booking.book_id}")
    print(f"   Booking ID (PK): {booking.id}")
    print(f"   User email: {booking.user.email}")
    print(f"   Booking status: {booking.status}")
    
    # Test email task directly (synchronously for testing)
    print(f"\n3. Testing email task...")
    try:
        # Call the task directly (not async) for testing
        result = send_booking_confirmation(booking.id)
        print(f"✅ Email task completed successfully")
    except Exception as e:
        print(f"❌ Email task failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    # Test async task (if Celery is running)
    print(f"\n4. Testing async email task...")
    try:
        task_result = send_booking_confirmation.delay(booking.id)
        print(f"✅ Async email task queued: {task_result.id}")
        print(f"   Note: Check Celery worker logs for actual execution")
    except Exception as e:
        print(f"❌ Async email task failed: {e}")
        print(f"   This might be because Celery is not running")

def test_manual_email():
    """Test manual email sending"""
    print(f"\n=== MANUAL EMAIL TEST ===")
    
    from django.core.mail import send_mail
    
    try:
        send_mail(
            'Test Email from OKPuja',
            'This is a test email to verify email configuration.',
            settings.DEFAULT_FROM_EMAIL,
            ['test@example.com'],  # Replace with your email for testing
            fail_silently=False,
        )
        print("✅ Manual email sent successfully")
    except Exception as e:
        print(f"❌ Manual email failed: {e}")

if __name__ == "__main__":
    test_email_functionality()
    test_manual_email()
