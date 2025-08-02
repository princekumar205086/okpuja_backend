"""
Test and Fix Email Notification System
This will test email sending and provide solutions for issues
"""

import os
import django
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from core.tasks import send_booking_confirmation

print("📧 EMAIL NOTIFICATION DIAGNOSIS")
print("=" * 50)

# 1. Check email configuration
print("\n1️⃣ EMAIL CONFIGURATION CHECK")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"   EMAIL_HOST_USER: {'***SET***' if settings.EMAIL_HOST_USER else '❌ NOT SET'}")
print(f"   EMAIL_HOST_PASSWORD: {'***SET***' if settings.EMAIL_HOST_PASSWORD else '❌ NOT SET'}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"   ADMIN_EMAIL: {settings.ADMIN_EMAIL}")

# 2. Check if email credentials are missing
email_issues = []
if not settings.EMAIL_HOST_USER:
    email_issues.append("EMAIL_HOST_USER not configured")
if not settings.EMAIL_HOST_PASSWORD:
    email_issues.append("EMAIL_HOST_PASSWORD not configured")

if email_issues:
    print(f"\n❌ EMAIL ISSUES FOUND:")
    for issue in email_issues:
        print(f"   • {issue}")
    
    print(f"\n💡 SOLUTION 1: Configure email credentials in .env file:")
    print(f"   EMAIL_HOST_USER=your-email@gmail.com")
    print(f"   EMAIL_HOST_PASSWORD=your-app-password")
    print(f"   # For Gmail, use App Password, not regular password")
    
    print(f"\n💡 SOLUTION 2: Use console backend for testing:")
    print(f"   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend")

# 3. Test email sending with console backend
print(f"\n2️⃣ TESTING EMAIL WITH CONSOLE BACKEND")

# Temporarily switch to console backend for testing
original_backend = settings.EMAIL_BACKEND
settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

try:
    # Test basic email
    print("   Testing basic email...")
    send_mail(
        'Test Email from OKPUJA',
        'This is a test email to verify email configuration.',
        settings.DEFAULT_FROM_EMAIL,
        ['asliprinceraj@gmail.com'],
        fail_silently=False,
    )
    print("   ✅ Basic email test successful (check console output)")
    
    # Test with HTML template
    print("   Testing HTML email...")
    try:
        html_content = """
        <html>
        <body>
            <h2>🙏 Test Booking Confirmation</h2>
            <p>This is a test HTML email from OKPUJA system.</p>
            <p><strong>Booking ID:</strong> BK-TEST123</p>
            <p><strong>Amount:</strong> ₹5000.00</p>
            <p>Thank you for using OKPUJA!</p>
        </body>
        </html>
        """
        
        send_mail(
            '🙏 Test Booking Confirmation - BK-TEST123',
            'Test booking confirmation email',
            settings.DEFAULT_FROM_EMAIL,
            ['asliprinceraj@gmail.com'],
            html_message=html_content,
            fail_silently=False,
        )
        print("   ✅ HTML email test successful")
        
        # Also send to admin
        send_mail(
            'New Test Booking - BK-TEST123',
            'Test booking for asliprinceraj@gmail.com has been confirmed.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        print("   ✅ Admin notification test successful")
        
    except Exception as e:
        print(f"   ❌ HTML email test failed: {e}")

except Exception as e:
    print(f"   ❌ Email test failed: {e}")

# Restore original backend
settings.EMAIL_BACKEND = original_backend

# 4. Test with actual booking
print(f"\n3️⃣ TESTING WITH ACTUAL BOOKING")

# Find the latest booking
try:
    latest_booking = Booking.objects.order_by('-created_at').first()
    if latest_booking:
        print(f"   Found booking: {latest_booking.book_id}")
        print(f"   User: {latest_booking.user.email}")
        print(f"   Amount: ₹{latest_booking.total_amount}")
        
        # Test direct email sending (not via Celery)
        print("   Testing direct email notification...")
        settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        
        try:
            subject = f"🙏 Booking Confirmed & Invoice - {latest_booking.book_id}"
            html_message = f"""
            <html>
            <body>
                <h2>🙏 Booking Confirmation</h2>
                <p>Dear {latest_booking.user.email},</p>
                <p>Your booking has been confirmed!</p>
                <p><strong>Booking ID:</strong> {latest_booking.book_id}</p>
                <p><strong>Service:</strong> {latest_booking.cart.puja_service.title if latest_booking.cart.puja_service else 'N/A'}</p>
                <p><strong>Date:</strong> {latest_booking.selected_date}</p>
                <p><strong>Time:</strong> {latest_booking.selected_time}</p>
                <p><strong>Amount:</strong> ₹{latest_booking.total_amount}</p>
                <p>Thank you for choosing OKPUJA!</p>
            </body>
            </html>
            """
            
            # Send to user
            send_mail(
                subject,
                f"Your booking {latest_booking.book_id} has been confirmed. Amount: ₹{latest_booking.total_amount}",
                settings.DEFAULT_FROM_EMAIL,
                [latest_booking.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            print("   ✅ User notification sent")
            
            # Send to admin
            send_mail(
                f"New Booking Confirmed - {latest_booking.book_id}",
                f"Booking {latest_booking.book_id} for {latest_booking.user.email} has been confirmed. Amount: ₹{latest_booking.total_amount}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            print("   ✅ Admin notification sent")
            
        except Exception as e:
            print(f"   ❌ Direct email failed: {e}")
            
        settings.EMAIL_BACKEND = original_backend
        
    else:
        print("   ❌ No bookings found")
        
except Exception as e:
    print(f"   ❌ Booking test failed: {e}")

print(f"\n4️⃣ CELERY TASK TESTING")

# Check if we can import Celery
try:
    from celery import current_app
    print("   ✅ Celery imported successfully")
    
    # Check if we can call the task directly (synchronous)
    if latest_booking:
        print("   Testing Celery task (direct call)...")
        try:
            # Call the task function directly (not via Celery)
            send_booking_confirmation(latest_booking.id)
            print("   ✅ Task function executed directly")
        except Exception as e:
            print(f"   ❌ Task function failed: {e}")
            
except ImportError:
    print("   ❌ Celery not installed or configured")

print(f"\n" + "=" * 50)
print("🏁 EMAIL DIAGNOSIS COMPLETE")
print("=" * 50)

print(f"\n📋 SUMMARY & SOLUTIONS:")

if email_issues:
    print(f"\n❌ ISSUES FOUND:")
    for issue in email_issues:
        print(f"   • {issue}")
    
    print(f"\n🔧 TO FIX EMAIL NOTIFICATIONS:")
    print(f"\n   Option 1: Gmail Setup (Recommended)")
    print(f"   1. Create Gmail App Password:")
    print(f"      - Go to Google Account settings")
    print(f"      - Enable 2-factor authentication")
    print(f"      - Generate App Password for 'Mail'")
    print(f"   ")
    print(f"   2. Add to .env file:")
    print(f"      EMAIL_HOST_USER=okpuja108@gmail.com")
    print(f"      EMAIL_HOST_PASSWORD=your-16-digit-app-password")
    print(f"   ")
    print(f"   Option 2: Console Backend (Testing)")
    print(f"   Add to .env file:")
    print(f"      EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend")
    print(f"   (Emails will print to console instead of sending)")

print(f"\n🔄 TO START CELERY WORKER:")
print(f"   Open new terminal and run:")
print(f"   celery -A okpuja_backend worker --loglevel=info")
print(f"   (This processes email tasks in background)")

print(f"\n✅ EMAIL SYSTEM READY WHEN:")
print(f"   • Email credentials configured")
print(f"   • Celery worker running")
print(f"   • Both user and admin will receive emails")

print(f"\n📧 CHECK CONSOLE OUTPUT ABOVE for test emails!")
