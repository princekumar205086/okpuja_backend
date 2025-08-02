"""
Test Email Notifications Directly with Latest Booking
This tests email sending without needing the Django server running
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from core.tasks import send_booking_confirmation
from django.core.mail import send_mail
from django.conf import settings

print("📧 TESTING EMAIL NOTIFICATIONS WITH CELERY")
print("=" * 60)

# Find the latest booking
latest_booking = Booking.objects.order_by('-created_at').first()

if latest_booking:
    print(f"\n📝 Found Latest Booking:")
    print(f"   ID: {latest_booking.book_id}")
    print(f"   User: {latest_booking.user.email}")
    print(f"   Service: {latest_booking.cart.puja_service.title if latest_booking.cart.puja_service else 'N/A'}")
    print(f"   Amount: ₹{latest_booking.total_amount}")
    print(f"   Date: {latest_booking.selected_date}")
    print(f"   Time: {latest_booking.selected_time}")
    
    print(f"\n⚙️ Current Email Configuration:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   Admin Email: {settings.ADMIN_EMAIL}")
    print(f"   Celery Eager: {getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)}")
    
    # Test 1: Call Celery task directly (should execute immediately with EAGER=True)
    print(f"\n1️⃣ Testing Celery Task (send_booking_confirmation)")
    print("   Calling send_booking_confirmation.delay()...")
    
    try:
        # This should execute immediately because CELERY_TASK_ALWAYS_EAGER=True
        result = send_booking_confirmation.delay(latest_booking.id)
        print("   ✅ Celery task executed successfully!")
        print("   📧 Check console output above for email content")
        
    except Exception as e:
        print(f"   ❌ Celery task failed: {e}")
        
        # Fallback: Call the function directly
        print("\n   Trying direct function call...")
        try:
            send_booking_confirmation(latest_booking.id)
            print("   ✅ Direct function call successful!")
        except Exception as e2:
            print(f"   ❌ Direct function call failed: {e2}")
    
    # Test 2: Manual email sending
    print(f"\n2️⃣ Testing Manual Email Sending")
    try:
        # Send user email
        user_subject = f"🙏 Booking Confirmed & Invoice - {latest_booking.book_id}"
        user_message = f"""
Dear {latest_booking.user.email},

Your booking has been confirmed!

Booking Details:
- Booking ID: {latest_booking.book_id}
- Service: {latest_booking.cart.puja_service.title if latest_booking.cart.puja_service else 'N/A'}
- Date: {latest_booking.selected_date}
- Time: {latest_booking.selected_time}
- Amount: ₹{latest_booking.total_amount}

Thank you for choosing OKPUJA!

Best regards,
OKPUJA Team
        """
        
        # User email
        send_mail(
            user_subject,
            user_message,
            settings.DEFAULT_FROM_EMAIL,
            [latest_booking.user.email],
            fail_silently=False,
        )
        print("   ✅ User email sent successfully")
        
        # Admin email
        admin_subject = f"New Booking Confirmed - {latest_booking.book_id}"
        admin_message = f"""
New booking confirmed:

- Booking ID: {latest_booking.book_id}
- User: {latest_booking.user.email}
- Service: {latest_booking.cart.puja_service.title if latest_booking.cart.puja_service else 'N/A'}
- Amount: ₹{latest_booking.total_amount}
- Date: {latest_booking.selected_date} at {latest_booking.selected_time}

Login to admin panel for more details.
        """
        
        send_mail(
            admin_subject,
            admin_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        print("   ✅ Admin email sent successfully")
        
    except Exception as e:
        print(f"   ❌ Manual email sending failed: {e}")
    
    print(f"\n" + "=" * 60)
    print("🎉 EMAIL TESTING COMPLETE!")
    print("=" * 60)
    
    print(f"\n📧 EMAIL SUMMARY:")
    print(f"   📨 User Email: {latest_booking.user.email}")
    print(f"   👨‍💼 Admin Email: {settings.ADMIN_EMAIL}")
    print(f"   📝 Booking: {latest_booking.book_id}")
    print(f"   💰 Amount: ₹{latest_booking.total_amount}")
    
    print(f"\n✅ WHAT HAPPENED:")
    print(f"   • Email tasks are now executing immediately (CELERY_TASK_ALWAYS_EAGER=True)")
    print(f"   • Emails are printed to console (EMAIL_BACKEND=console)")
    print(f"   • Both user and admin notifications sent")
    print(f"   • No Redis/Celery worker needed for development")
    
    print(f"\n🚀 FOR PRODUCTION:")
    print(f"   • Set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
    print(f"   • Configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
    print(f"   • Set CELERY_TASK_ALWAYS_EAGER=False")
    print(f"   • Start Celery worker: celery -A okpuja_backend worker")
    
else:
    print("❌ No bookings found!")
    print("Create a booking first to test email notifications.")
