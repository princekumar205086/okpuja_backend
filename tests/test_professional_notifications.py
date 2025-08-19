#!/usr/bin/env python
"""
Professional Email Notification Testing Script

This script tests all the professional email notifications to ensure:
1. No duplicate notifications are sent
2. Professional templates are used
3. Admin gets proper notifications with invoices
4. OTP emails are professional
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from django.test import TestCase
from django.core import mail
from django.core.cache import cache
from django.contrib.auth import get_user_model
from accounts.models import User
from booking.models import Booking
from astrology.models import AstrologyBooking, AstrologyService
from cart.models import Cart
from puja.models import PujaService, PujaCategory
import random
from datetime import datetime, timedelta
from decimal import Decimal

User = get_user_model()

def clear_cache():
    """Clear cache to test duplicate prevention"""
    cache.clear()
    print("✅ Cache cleared")

def create_test_user():
    """Create a test user for notifications"""
    email = f"testuser{random.randint(1000, 9999)}@gmail.com"
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+919876543210',
            'otp': '123456',
            'otp_verified': True
        }
    )
    print(f"✅ Test user created: {user.email}")
    return user

def test_otp_notification():
    """Test professional OTP email notification"""
    print("\n" + "="*60)
    print("🔐 TESTING OTP NOTIFICATION")
    print("="*60)
    
    # Clear previous emails
    mail.outbox.clear()
    
    user = create_test_user()
    user.otp = '789123'
    user.otp_verified = False
    user.save()
    
    # Import the registration view
    from accounts.views import RegisterView
    register_view = RegisterView()
    
    try:
        register_view._send_verification(user)
        
        if len(mail.outbox) > 0:
            email = mail.outbox[0]
            print(f"✅ OTP Email sent successfully")
            print(f"📧 Subject: {email.subject}")
            print(f"👤 To: {email.to}")
            print(f"📝 Content Type: {'HTML' if 'html' in email.content_subtype else 'Plain'}")
            
            # Check if professional template is used
            if '🔐' in email.subject and 'OkPuja' in email.subject:
                print("✅ Professional OTP template used")
            else:
                print("❌ Basic OTP template detected")
                
        else:
            print("❌ No OTP email sent")
            
    except Exception as e:
        print(f"❌ OTP notification failed: {str(e)}")

def test_booking_notification():
    """Test professional booking notification with admin alert"""
    print("\n" + "="*60)
    print("🙏 TESTING BOOKING NOTIFICATION")
    print("="*60)
    
    # Clear cache and emails
    clear_cache()
    mail.outbox.clear()
    
    user = create_test_user()
    
    # Create a puja service
    category, _ = PujaCategory.objects.get_or_create(
        name="Test Category",
        defaults={"description": "Test category for notifications"}
    )
    
    puja_service, _ = PujaService.objects.get_or_create(
        title="Test Puja Service",
        defaults={
            "category": category,
            "description": "Test puja for notification testing",
            "price": Decimal('1500.00'),
            "duration": 60,
            "is_active": True
        }
    )
    
    # Create cart and booking
    cart, _ = Cart.objects.get_or_create(
        user=user,
        defaults={
            "puja_service": puja_service,
            "total_amount": puja_service.price
        }
    )
    
    booking = Booking.objects.create(
        user=user,
        cart=cart,
        book_id=f"BK-TEST{random.randint(1000, 9999)}",
        total_amount=cart.total_amount,
        selected_date=datetime.now().date() + timedelta(days=7),
        selected_time=datetime.now().time(),
        status='CONFIRMED',
        payment_status='SUCCESS'
    )
    
    print(f"✅ Test booking created: {booking.book_id}")
    
    # Test booking confirmation
    from core.tasks import send_booking_confirmation
    
    try:
        result = send_booking_confirmation(booking.id)
        
        # Check emails sent
        if len(mail.outbox) >= 2:
            customer_email = None
            admin_email = None
            
            for email in mail.outbox:
                if user.email in email.to:
                    customer_email = email
                elif getattr(settings, 'ADMIN_PERSONAL_EMAIL', 'okpuja108@gmail.com') in email.to:
                    admin_email = email
            
            if customer_email:
                print(f"✅ Customer email sent")
                print(f"📧 Subject: {customer_email.subject}")
                print(f"📎 Attachments: {len(customer_email.attachments)}")
                
            if admin_email:
                print(f"✅ Admin email sent")
                print(f"📧 Subject: {admin_email.subject}")
                print(f"📎 Attachments: {len(admin_email.attachments)}")
                
                # Check if professional template is used
                if '🚨' in admin_email.subject and 'Alert' in admin_email.subject:
                    print("✅ Professional admin template used")
                else:
                    print("❌ Basic admin template detected")
            
            # Test duplicate prevention
            print("\n🔄 Testing duplicate prevention...")
            mail.outbox.clear()
            send_booking_confirmation(booking.id)
            
            if len(mail.outbox) == 0:
                print("✅ Duplicate notifications prevented successfully")
            else:
                print(f"❌ Duplicate notifications sent: {len(mail.outbox)}")
                
        else:
            print(f"❌ Expected 2+ emails, got {len(mail.outbox)}")
            
    except Exception as e:
        print(f"❌ Booking notification failed: {str(e)}")

def test_astrology_notification():
    """Test professional astrology notification"""
    print("\n" + "="*60)
    print("🔮 TESTING ASTROLOGY NOTIFICATION")
    print("="*60)
    
    # Clear cache and emails
    clear_cache()
    mail.outbox.clear()
    
    # Create astrology service
    service, _ = AstrologyService.objects.get_or_create(
        title="Test Astrology Consultation",
        defaults={
            "description": "Test astrology service",
            "price": Decimal('2500.00'),
            "duration_minutes": 60,
            "is_active": True
        }
    )
    
    # Create astrology booking
    booking = AstrologyBooking.objects.create(
        service=service,
        astro_book_id=f"ASTRO-TEST{random.randint(1000, 9999)}",
        contact_email=f"astrologytest{random.randint(100, 999)}@gmail.com",
        contact_phone="+919876543210",
        preferred_date=datetime.now().date() + timedelta(days=5),
        preferred_time=datetime.now().time(),
        birth_date=datetime(1990, 1, 1).date(),
        birth_time=datetime(1990, 1, 1, 10, 30).time(),
        birth_place="Test City",
        language="English",
        gender="M",
        questions="Test astrology question",
        status="CONFIRMED"
    )
    
    print(f"✅ Test astrology booking created: {booking.astro_book_id}")
    
    try:
        # Test customer confirmation
        booking.send_booking_confirmation()
        
        # Test admin notification
        booking.send_admin_notification()
        
        # Check emails
        if len(mail.outbox) >= 2:
            customer_email = None
            admin_email = None
            
            for email in mail.outbox:
                if booking.contact_email in email.to:
                    customer_email = email
                elif getattr(settings, 'ADMIN_PERSONAL_EMAIL', 'okpuja108@gmail.com') in email.to:
                    admin_email = email
            
            if customer_email:
                print(f"✅ Customer astrology email sent")
                print(f"📧 Subject: {customer_email.subject}")
                
            if admin_email:
                print(f"✅ Admin astrology email sent")
                print(f"📧 Subject: {admin_email.subject}")
                
                # Check professional template
                if '🔮' in admin_email.subject and 'Astrology' in admin_email.subject:
                    print("✅ Professional astrology admin template used")
                else:
                    print("❌ Basic astrology admin template detected")
            
            # Test duplicate prevention
            print("\n🔄 Testing astrology duplicate prevention...")
            mail.outbox.clear()
            booking.send_admin_notification()
            
            if len(mail.outbox) == 0:
                print("✅ Astrology duplicate notifications prevented")
            else:
                print(f"❌ Astrology duplicate notifications sent: {len(mail.outbox)}")
                
        else:
            print(f"❌ Expected 2 astrology emails, got {len(mail.outbox)}")
            
    except Exception as e:
        print(f"❌ Astrology notification failed: {str(e)}")

def test_email_configuration():
    """Test email configuration"""
    print("\n" + "="*60)
    print("📧 TESTING EMAIL CONFIGURATION")
    print("="*60)
    
    print(f"📤 DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"👨‍💼 ADMIN_PERSONAL_EMAIL: {getattr(settings, 'ADMIN_PERSONAL_EMAIL', 'Not set')}")
    print(f"🏠 EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"🔐 EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    
    if settings.DEFAULT_FROM_EMAIL == getattr(settings, 'ADMIN_PERSONAL_EMAIL', ''):
        print("✅ Admin email properly configured")
    else:
        print("⚠️  Admin email different from default sender")

def main():
    """Run all notification tests"""
    print("\n" + "🎯"*20)
    print("OKPUJA PROFESSIONAL EMAIL NOTIFICATION TESTING")
    print("🎯"*20)
    
    try:
        test_email_configuration()
        test_otp_notification()
        test_booking_notification() 
        test_astrology_notification()
        
        print("\n" + "✅"*20)
        print("ALL NOTIFICATION TESTS COMPLETED")
        print("✅"*20)
        
    except Exception as e:
        print(f"\n❌ Testing failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
