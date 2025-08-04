#!/usr/bin/env python
"""
Manual test for astrology booking email notifications
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from astrology.models import AstrologyService, AstrologyBooking
from payments.models import PaymentOrder
from payments.services import WebhookService

User = get_user_model()

def manual_test_emails():
    """Manually test email notifications"""
    print("📧 Manual Email Notification Test")
    print("=" * 50)
    
    try:
        # Get the latest booking
        booking = AstrologyBooking.objects.order_by('-id').first()
        
        if not booking:
            print("❌ No astrology bookings found")
            return
            
        print(f"✅ Found booking: #{booking.id}")
        print(f"📧 Customer email: {booking.contact_email}")
        print(f"📅 Date: {booking.preferred_date}")
        print(f"🔮 Service: {booking.service.title}")
        
        # Test 1: User confirmation email
        print(f"\n📧 Testing user confirmation email...")
        try:
            booking.send_booking_confirmation()
            print("✅ User confirmation email sent successfully")
        except Exception as e:
            print(f"❌ User email error: {e}")
        
        # Test 2: Admin notification email
        print(f"\n📧 Testing admin notification email...")
        try:
            webhook_service = WebhookService()
            webhook_service._send_admin_notification_astrology(booking)
            print("✅ Admin notification email sent successfully")
        except Exception as e:
            print(f"❌ Admin email error: {e}")
            
        # Test 3: Manual booking confirmation
        print(f"\n🔄 Manually confirming booking...")
        try:
            booking.status = 'CONFIRMED'
            booking.save()
            print("✅ Booking status updated to CONFIRMED")
            
            # Send confirmation email
            booking.send_booking_confirmation()
            print("✅ Confirmation email sent for CONFIRMED booking")
            
        except Exception as e:
            print(f"❌ Manual confirmation error: {e}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

def test_email_templates():
    """Test email template rendering"""
    print("\n🎨 Testing Email Template Rendering")
    print("=" * 50)
    
    try:
        booking = AstrologyBooking.objects.order_by('-id').first()
        if not booking:
            print("❌ No bookings found")
            return
            
        from django.template.loader import render_to_string
        
        # Test template rendering
        html_content = render_to_string('astrology/booking_email.html', {
            'booking': booking,
            'service': booking.service
        })
        
        print("✅ Email template rendered successfully")
        print(f"📊 HTML length: {len(html_content)} characters")
        
        # Save rendered template for inspection
        with open('test_email_output.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("✅ Saved rendered email to test_email_output.html")
        
    except Exception as e:
        print(f"❌ Template rendering error: {e}")

def check_email_settings():
    """Check email configuration"""
    print("\n⚙️ Email Configuration Check")
    print("=" * 50)
    
    print(f"📮 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📮 Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    if hasattr(settings, 'EMAIL_HOST'):
        print(f"📮 Email Host: {settings.EMAIL_HOST}")
    if hasattr(settings, 'EMAIL_PORT'):
        print(f"📮 Email Port: {settings.EMAIL_PORT}")
    if hasattr(settings, 'EMAIL_USE_TLS'):
        print(f"📮 Use TLS: {settings.EMAIL_USE_TLS}")
    if hasattr(settings, 'EMAIL_FILE_PATH'):
        print(f"📮 File Path: {settings.EMAIL_FILE_PATH}")

def list_recent_bookings():
    """List recent astrology bookings"""
    print("\n📋 Recent Astrology Bookings")
    print("=" * 50)
    
    bookings = AstrologyBooking.objects.order_by('-id')[:5]
    
    for booking in bookings:
        print(f"#{booking.id} - {booking.service.title} - {booking.status} - {booking.contact_email}")

if __name__ == "__main__":
    print("🧪 Manual Astrology Email Testing")
    print("=" * 80)
    
    # Check settings
    check_email_settings()
    
    # List bookings
    list_recent_bookings()
    
    # Test email templates
    test_email_templates()
    
    # Test emails
    manual_test_emails()
    
    print("\n" + "=" * 80)
    print("✅ Manual testing complete! Check your email output.")
    print("=" * 80)
