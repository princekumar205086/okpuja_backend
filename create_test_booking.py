#!/usr/bin/env python
"""
Simple test to create a test user and booking for invoice testing
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
from booking.models import Booking
from cart.models import Cart
from puja.models import PujaService, PujaCategory, Package
from accounts.models import Address

User = get_user_model()

def create_simple_test_data():
    """Create minimal test data"""
    
    # Create test user
    user, created = User.objects.get_or_create(
        email='asliprinceraj@gmail.com',
        defaults={
            'username': 'testuser',
            'phone': '+919876543210'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create test category
    category, _ = PujaCategory.objects.get_or_create(name='Test Category')
    
    # Create test puja service
    puja_service = PujaService.objects.create(
        title='Ganesh Puja',
        description='Complete Ganesh Puja with all rituals',
        category=category,
        duration_minutes=120,
        is_active=True,
        image='https://example.com/test-image.jpg'
    )
    
    # Create test package
    package = Package.objects.create(
        puja_service=puja_service,
        location='Home Visit',
        package_type='PREMIUM',
        price=Decimal('5000.00'),
        description='Premium Ganesh Puja package',
        is_active=True
    )
    
    # Create test cart
    cart = Cart.objects.create(
        user=user,
        puja_service=puja_service,
        package=package,
        cart_id=f'CART-TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        selected_date=(timezone.now() + timedelta(days=7)).date(),
        selected_time='10:00 AM'
    )
    
    # Create test address
    address = Address.objects.create(
        user=user,
        address_line1='123 Test Street',
        city='New Delhi',
        state='Delhi',
        postal_code='110001',
        country='India'
    )
    
    # Create test booking
    booking = Booking.objects.create(
        user=user,
        cart=cart,
        selected_date=(timezone.now() + timedelta(days=7)).date(),
        selected_time=timezone.now().time(),
        address=address,
        status='CONFIRMED'
    )
    
    print(f"✅ Created test booking: {booking.book_id}")
    print(f"✅ User: {user.email}")
    print(f"✅ Service: {puja_service.title}")
    print(f"✅ Amount: ₹{booking.total_amount}")
    
    return booking

if __name__ == "__main__":
    try:
        booking = create_simple_test_data()
        print(f"\n🌐 Test your HTML invoice at:")
        print(f"   http://localhost:8000/api/booking/invoice/html/{booking.book_id}/")
        print(f"   http://localhost:8000/api/booking/public/invoice/html/{booking.book_id}/")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()