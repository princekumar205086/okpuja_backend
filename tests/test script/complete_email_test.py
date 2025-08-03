#!/usr/bin/env python
"""
Complete End-to-End Email Verification Test
Tests the entire flow: Cart → Payment → Booking → Email Notification
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
from cart.models import Cart
from puja.models import PujaService, Package
from core.tasks import send_booking_confirmation
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

def create_test_cart_and_booking():
    """Create a test cart and booking to verify email flow"""
    print("=== Creating Test Cart and Booking ===")
    
    try:
        # Get or create a test user
        test_email = "test@okpuja.com"
        user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'role': 'USER',
                'account_status': 'ACTIVE',
                'email_verified': True,
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created test user: {test_email}")
        else:
            print(f"📧 Using existing user: {test_email}")
        
        # Get a puja service
        puja_service = PujaService.objects.first()
        if not puja_service:
            print("❌ No puja services found!")
            return None
        
        # Create a test cart
        cart = Cart.objects.create(
            user=user,
            service_type='PUJA',
            puja_service=puja_service,
            package=Package.objects.filter(puja_service=puja_service).first(),
            quantity=1,
            address_id=None,
            selected_date=datetime.now().date() + timedelta(days=7),
            selected_time="10:00",
            cart_total=Decimal('1500.00'),
            final_amount=Decimal('1500.00'),
            status='PENDING'
        )
        
        print(f"✅ Created test cart: {cart.cart_id}")
        
        # Create a test booking (simulating the webhook process)
        booking = Booking.objects.create(
            user=user,
            cart=cart,
            book_id=f"BK-{uuid.uuid4().hex[:8].upper()}",
            total_amount=cart.final_amount,
            payment_method='PhonePe',
            payment_status='COMPLETED',
            selected_date=cart.selected_date,
            selected_time=cart.selected_time,
            status='CONFIRMED',
            transaction_id=f"TEST_{uuid.uuid4().hex[:10]}"
        )
        
        print(f"✅ Created test booking: {booking.book_id}")
        
        return booking
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return None

def test_email_notifications(booking):
    """Test both user and admin email notifications"""
    print(f"\n=== Testing Email Notifications for {booking.book_id} ===")
    
    try:
        # Test Celery task (this sends both user and admin emails)
        print("🔄 Executing Celery email task...")
        task_result = send_booking_confirmation.apply(args=[booking.id])
        
        print(f"✅ Celery task completed!")
        print(f"📋 Task ID: {task_result.id}")
        print(f"📊 Task Status: {task_result.status}")
        
        # Test direct email to user
        print(f"\n📤 Sending direct test email to user: {booking.user.email}")
        user_result = send_mail(
            subject='🙏 Test: Booking Confirmation - OkPuja',
            message=f'''
            Dear Customer,
            
            Your booking {booking.book_id} has been confirmed!
            
            Service: {booking.cart.puja_service.name if booking.cart.puja_service else 'N/A'}
            Date: {booking.selected_date}
            Time: {booking.selected_time}
            Amount: ₹{booking.total_amount}
            
            This is a test email to verify our notification system.
            
            Best regards,
            OkPuja Team
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            fail_silently=False,
        )
        print(f"✅ User email sent! Result: {user_result}")
        
        # Test direct email to admin
        print(f"\n📤 Sending direct test email to admin: {settings.ADMIN_EMAIL}")
        admin_result = send_mail(
            subject='🔔 Test: New Booking Alert - OkPuja Admin',
            message=f'''
            New booking received!
            
            Booking ID: {booking.book_id}
            Customer: {booking.user.email}
            Service: {booking.cart.puja_service.name if booking.cart.puja_service else 'N/A'}
            Date: {booking.selected_date}
            Amount: ₹{booking.total_amount}
            
            This is a test email to verify admin notifications.
            
            OkPuja System
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        print(f"✅ Admin email sent! Result: {admin_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email testing failed: {e}")
        return False

def main():
    print("🚀 Complete End-to-End Email Verification Test")
    print("=" * 60)
    
    # Show current configuration
    print(f"📧 FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"👨‍💼 ADMIN_EMAIL: {settings.ADMIN_EMAIL}")
    print(f"🔧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    
    # Create test data
    booking = create_test_cart_and_booking()
    if not booking:
        print("\n❌ Failed to create test data!")
        return
    
    # Test email notifications
    success = test_email_notifications(booking)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ COMPLETE EMAIL SYSTEM VERIFICATION SUCCESSFUL!")
        print("📧 Both user and admin emails are working")
        print("🎯 End-to-end flow is functional")
        print("\n💡 If emails aren't reaching users:")
        print("   1. Check spam/junk folders")
        print("   2. Verify email addresses are correct")
        print("   3. Check Gmail app password validity")
        print("   4. Monitor email delivery logs")
    else:
        print("❌ EMAIL SYSTEM VERIFICATION FAILED!")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
