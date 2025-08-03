#!/usr/bin/env python
"""
Test actual email functionality with current configuration
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.core.mail import send_mail, get_connection
from django.conf import settings
from booking.models import Booking
from accounts.models import User
from cart.models import Cart

def test_email_configuration():
    """Test current email configuration"""
    print("=== Email Configuration Test ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    
    if hasattr(settings, 'EMAIL_HOST'):
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    if hasattr(settings, 'EMAIL_PORT'):
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    if hasattr(settings, 'EMAIL_USE_TLS'):
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    if hasattr(settings, 'EMAIL_HOST_USER'):
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    if hasattr(settings, 'EMAIL_HOST_PASSWORD'):
        print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'Not set'}")
    
    print("\n=== Testing Email Connection ===")
    try:
        connection = get_connection()
        connection.open()
        print("✅ Email connection successful")
        connection.close()
    except Exception as e:
        print(f"❌ Email connection failed: {e}")
    
    return True

def test_simple_email():
    """Test sending a simple email"""
    print("\n=== Testing Simple Email ===")
    try:
        result = send_mail(
            subject='OkPuja Test Email',
            message='This is a test email from OkPuja backend.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],  # Test email
            fail_silently=False,
        )
        print(f"✅ Email sent successfully! Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

def test_booking_email():
    """Test booking confirmation email with actual data"""
    print("\n=== Testing Booking Confirmation Email ===")
    try:
        # Get the latest booking
        latest_booking = Booking.objects.first()
        if not latest_booking:
            print("❌ No bookings found to test with")
            return False
        
        print(f"Testing with booking: {latest_booking.book_id}")
        print(f"User: {latest_booking.user.email}")
        
        # Import and test the Celery task directly
        from core.tasks import send_booking_confirmation
        
        # Execute the task
        result = send_booking_confirmation.apply(args=[latest_booking.id])
        print(f"✅ Booking email task executed! Result: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Booking email failed: {e}")
        return False

def main():
    print("🚀 Starting Email System Test...")
    
    # Test configuration
    test_email_configuration()
    
    # Test simple email
    test_simple_email()
    
    # Test booking email
    test_booking_email()
    
    print("\n=== Email System Test Complete ===")

if __name__ == "__main__":
    main()
