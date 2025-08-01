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
from django.core.mail import send_mail
from django.conf import settings

def test_email_directly():
    """Test email functionality directly"""
    print("=== TESTING EMAIL FUNCTIONALITY ===\n")
    
    # Get the latest booking
    latest_booking = Booking.objects.order_by('-created_at').first()
    
    if not latest_booking:
        print("❌ No bookings found")
        return
    
    print(f"📧 Testing email for booking: {latest_booking.book_id}")
    print(f"   User: {latest_booking.user.email}")
    print(f"   Status: {latest_booking.status}")
    
    try:
        # Test simple email first
        subject = f"🙏 Booking Confirmed - {latest_booking.book_id}"
        message = f"""
        Dear {getattr(latest_booking.user, 'first_name', '') or latest_booking.user.email},
        
        Your booking has been confirmed!
        
        Booking Details:
        - Booking ID: {latest_booking.book_id}
        - Service: {latest_booking.cart.puja_service.title if latest_booking.cart and latest_booking.cart.puja_service else 'N/A'}
        - Date: {latest_booking.selected_date}
        - Time: {latest_booking.selected_time}
        - Status: {latest_booking.status}
        
        Thank you for choosing OkPuja!
        
        Best regards,
        Team OkPuja
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [latest_booking.user.email],
            fail_silently=False
        )
        
        print(f"✅ Email sent successfully to {latest_booking.user.email}")
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        print(f"   Check your email settings in .env file")

def show_email_configuration():
    """Show current email configuration"""
    print(f"\n=== EMAIL CONFIGURATION ===\n")
    
    print(f"📧 CURRENT SETTINGS:")
    print(f"   EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'NOT SET')}")
    print(f"   EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'NOT SET')}")
    print(f"   EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'NOT SET')}")
    print(f"   EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')}")
    print(f"   EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')}")
    print(f"   DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")

def setup_simple_celery():
    """Show how to set up simple Celery for email"""
    print(f"\n=== CELERY SETUP GUIDE ===\n")
    
    print(f"🔧 TO ENABLE EMAIL NOTIFICATIONS:")
    print(f"   1. Install Redis: pip install redis")
    print(f"   2. Start Redis server: redis-server")
    print(f"   3. Add to settings.py:")
    print(f"      CELERY_BROKER_URL = 'redis://localhost:6379/0'")
    print(f"      CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'")
    print(f"   4. Create celery.py in okpuja_backend/")
    print(f"   5. Run Celery worker: celery -A okpuja_backend worker -l info")
    
    print(f"\n📋 ALTERNATIVE - SYNC EMAIL:")
    print(f"   For testing, you can call send_booking_confirmation() directly")
    print(f"   without .delay() to send emails synchronously")

if __name__ == "__main__":
    show_email_configuration()
    test_email_directly()
    setup_simple_celery()
