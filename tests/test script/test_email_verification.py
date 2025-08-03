#!/usr/bin/env python
"""
Complete Email Verification Test - Check if emails are actually being sent to users
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

from django.core.mail import send_mail
from django.conf import settings
from booking.models import Booking
from accounts.models import User
from core.tasks import send_booking_confirmation
import logging

def test_real_user_email():
    """Test sending email to actual user from latest booking"""
    print("=== Testing Real User Email ===")
    
    # Get the latest booking
    latest_booking = Booking.objects.select_related('user', 'cart').first()
    if not latest_booking:
        print("❌ No bookings found!")
        return False
    
    print(f"📧 Testing with booking: {latest_booking.book_id}")
    print(f"👤 User: {latest_booking.user.email}")
    print(f"📅 Booking Date: {latest_booking.selected_date}")
    print(f"💰 Amount: ₹{latest_booking.total_amount}")
    
    # Test direct email sending
    try:
        print(f"\n📤 Sending test email to: {latest_booking.user.email}")
        # Get user name safely
        user_name = latest_booking.user.email
        if hasattr(latest_booking.user, 'profile') and latest_booking.user.profile:
            user_name = f"{latest_booking.user.profile.first_name} {latest_booking.user.profile.last_name}"
        
        result = send_mail(
            subject='✅ OkPuja Email Test - Your Booking Confirmation',
            message=f'''
            Dear {user_name},
            
            This is a test email to confirm that our email system is working.
            
            Your booking details:
            - Booking ID: {latest_booking.book_id}
            - Date: {latest_booking.selected_date}
            - Amount: ₹{latest_booking.total_amount}
            - Status: {latest_booking.get_status_display()}
            
            If you receive this email, our notification system is working perfectly!
            
            Best regards,
            OkPuja Team
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[latest_booking.user.email],
            fail_silently=False,
        )
        print(f"✅ Email sent successfully! Result: {result}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False
    
    # Test Celery task
    try:
        print(f"\n🔄 Testing Celery booking confirmation task...")
        task_result = send_booking_confirmation.apply(args=[latest_booking.id])
        print(f"✅ Celery task executed! Task ID: {task_result.id}")
        print(f"📊 Task Status: {task_result.status}")
        print(f"📋 Task Result: {task_result.result}")
    except Exception as e:
        print(f"❌ Celery task failed: {e}")
        return False
    
    return True

def check_email_logs():
    """Check if there are any email-related logs"""
    print("\n=== Email Configuration Summary ===")
    print(f"🔧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"🌐 EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"📧 FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"👨‍💼 ADMIN_EMAIL: {settings.ADMIN_EMAIL}")
    print(f"🔒 TLS Enabled: {settings.EMAIL_USE_TLS}")
    print(f"🚪 Port: {settings.EMAIL_PORT}")
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("ℹ️  Console backend - emails will appear in terminal output")
    elif settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
        print("📤 SMTP backend - emails will be sent via Gmail")
    
def main():
    print("🚀 Complete Email Verification Test Starting...")
    print("=" * 60)
    
    # Check configuration
    check_email_logs()
    
    # Test real email
    success = test_real_user_email()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ EMAIL SYSTEM IS WORKING!")
        print("📧 Emails are being sent successfully")
        print("💡 If users aren't receiving emails, check:")
        print("   - Spam/Junk folders")
        print("   - Email delivery delays")
        print("   - Gmail app passwords are working")
        print("   - Recipients' email addresses are correct")
    else:
        print("❌ EMAIL SYSTEM HAS ISSUES!")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
