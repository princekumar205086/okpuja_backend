#!/usr/bin/env python
"""
Test script to send booking confirmation email with the new professional invoice template
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

# Now import Django models and utilities
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

from booking.models import Booking
from cart.models import Cart
from puja.models import PujaService, Package
from accounts.models import Address
from booking.invoice_views import generate_invoice_html, generate_invoice_pdf_data

User = get_user_model()

def create_test_booking():
    """Create a test booking for email testing"""
    
    # Get or create test user with your email
    user, created = User.objects.get_or_create(
        email='asliprinceraj@gmail.com',
        defaults={
            'username': 'asliprinceraj',
            'first_name': 'Prince',
            'last_name': 'Raj',
            'phone': '+91-9876543210'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing user: {user.email}")
    
    # Get or create a test puja service
    puja_service, created = PujaService.objects.get_or_create(
        title="Ganesh Puja",
        defaults={
            'description': "Complete Ganesh Puja with all rituals and prasadam",
            'price': Decimal('5000.00'),
            'duration': 120,
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created test puja service: {puja_service.title}")
    else:
        print(f"✅ Using existing puja service: {puja_service.title}")
    
    # Get or create a test package
    package, created = Package.objects.get_or_create(
        package_type="Premium",
        defaults={
            'location': 'Home Visit',
            'price': Decimal('2500.00'),
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created test package: {package.package_type}")
    else:
        print(f"✅ Using existing package: {package.package_type}")
    
    # Get or create a test address
    address, created = Address.objects.get_or_create(
        user=user,
        defaults={
            'address_line1': '123 Test Street',
            'address_line2': 'Near Temple',
            'city': 'New Delhi',
            'state': 'Delhi',
            'postal_code': '110001',
            'country': 'India'
        }
    )
    
    if created:
        print(f"✅ Created test address")
    else:
        print(f"✅ Using existing address")
    
    # Create or get cart
    cart, created = Cart.objects.get_or_create(
        user=user,
        puja_service=puja_service,
        package=package,
        defaults={
            'cart_id': f'CART-TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'quantity': 1
        }
    )
    
    if created:
        print(f"✅ Created test cart: {cart.cart_id}")
    else:
        print(f"✅ Using existing cart: {cart.cart_id}")
    
    # Create booking
    booking, created = Booking.objects.get_or_create(
        user=user,
        cart=cart,
        defaults={
            'selected_date': (timezone.now() + timedelta(days=7)).date(),
            'selected_time': timezone.now().time(),
            'address': address,
            'status': 'CONFIRMED'
        }
    )
    
    if created:
        print(f"✅ Created test booking: {booking.book_id}")
    else:
        print(f"✅ Using existing booking: {booking.book_id}")
    
    return booking

def test_html_invoice(booking):
    """Test HTML invoice generation"""
    try:
        html_content = generate_invoice_html(booking)
        
        # Save to file for preview
        with open('test_invoice.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML invoice generated successfully")
        print(f"📄 Saved to: test_invoice.html")
        return True
    except Exception as e:
        print(f"❌ Failed to generate HTML invoice: {str(e)}")
        return False

def test_pdf_invoice(booking):
    """Test PDF invoice generation"""
    try:
        pdf_data = generate_invoice_pdf_data(booking)
        
        # Save to file for preview
        with open(f'test_invoice_{booking.book_id}.pdf', 'wb') as f:
            f.write(pdf_data)
        
        print(f"✅ PDF invoice generated successfully")
        print(f"📄 Saved to: test_invoice_{booking.book_id}.pdf")
        return True
    except Exception as e:
        print(f"❌ Failed to generate PDF invoice: {str(e)}")
        return False

def send_test_confirmation_email(booking):
    """Send test confirmation email"""
    try:
        # Use the same template as the actual confirmation email
        subject = f"🙏 Booking Confirmed & Invoice - {booking.book_id}"
        html_message = render_to_string('emails/booking_confirmation_professional.html', {
            'booking': booking,
            'MEDIA_URL': getattr(settings, 'MEDIA_URL', '/media/')
        })
        
        # Create EmailMessage to support attachments
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email]
        )
        email.content_subtype = "html"
        
        # Generate and attach invoice PDF
        try:
            pdf_data = generate_invoice_pdf_data(booking)
            email.attach(f'OkPuja-Invoice-{booking.book_id}.pdf', pdf_data, 'application/pdf')
            print(f"✅ PDF invoice attached to email")
        except Exception as e:
            print(f"⚠️ Warning: Failed to attach PDF invoice: {str(e)}")
        
        # Send email
        email.send()
        print(f"✅ Test confirmation email sent to: {booking.user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting OkPuja Invoice Test...")
    print("=" * 60)
    
    # Check email settings
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    # Create test booking
    print("\n📝 Creating test booking...")
    booking = create_test_booking()
    
    # Test HTML invoice
    print(f"\n🎨 Testing HTML invoice for booking {booking.book_id}...")
    html_success = test_html_invoice(booking)
    
    # Test PDF invoice
    print(f"\n📄 Testing PDF invoice for booking {booking.book_id}...")
    pdf_success = test_pdf_invoice(booking)
    
    # Send test email
    print(f"\n📧 Sending test confirmation email...")
    email_success = send_test_confirmation_email(booking)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"  • HTML Invoice: {'✅ Success' if html_success else '❌ Failed'}")
    print(f"  • PDF Invoice: {'✅ Success' if pdf_success else '❌ Failed'}")
    print(f"  • Email Sent: {'✅ Success' if email_success else '❌ Failed'}")
    print(f"  • Booking ID: {booking.book_id}")
    print(f"  • Customer: {booking.user.email}")
    print(f"  • Amount: ₹{booking.total_amount}")
    
    if email_success:
        print(f"\n✅ Check your email at {booking.user.email} for the confirmation with invoice!")
        print(f"🌐 You can also view the HTML invoice at:")
        print(f"   http://localhost:8000/api/booking/invoice/html/{booking.book_id}/")
        print(f"🌐 Or the public HTML invoice at:")
        print(f"   http://localhost:8000/api/booking/public/invoice/html/{booking.book_id}/")

if __name__ == "__main__":
    main()