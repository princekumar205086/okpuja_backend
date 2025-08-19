#!/usr/bin/env python
"""
Create test booking with real data matching the user's booking details
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from booking.models import Booking
from cart.models import Cart
from puja.models import PujaService
from accounts.models import Address

User = get_user_model()

def create_real_test_booking():
    """Create a test booking with real data from the user's example"""
    try:
        # Get or create user
        user, created = User.objects.get_or_create(
            email='princekumar205086@gmail.com',
            defaults={
                'username': 'princekumar205086',
                'phone': '+918210037589',
                'email_verified': True,
                'account_status': 'ACTIVE'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"Created new user: {user.email}")
        else:
            print(f"Using existing user: {user.email}")
        
        # Try to get an existing puja service first
        puja_service = PujaService.objects.first()
        if not puja_service:
            # If no services exist, we need to check the category first
            from puja.models import PujaCategory
            category = PujaCategory.objects.first()
            if not category:
                # Create a basic category
                category = PujaCategory.objects.create(
                    name='Testing Category',
                    description='Test category for bookings'
                )
            
            # Create puja service with correct fields
            puja_service = PujaService.objects.create(
                title='Navratri Testing Puja',
                description='Complete Navratri puja ceremony with all rituals',
                category=category,
                duration_minutes=90,
                is_active=True
            )
            print(f"Created new puja service: {puja_service.title}")
        else:
            print(f"Using existing puja service: {puja_service.title}")
        
        # Create or get address
        address, created = Address.objects.get_or_create(
            user=user,
            defaults={
                'address_line1': 'Rohini, Sector 5',
                'city': 'Purnia',
                'state': 'Bihar',
                'country': 'India',
                'postal_code': '854301'
            }
        )
        if created:
            print(f"Created new address for user")
        else:
            print(f"Using existing address")
        
        # Create cart with correct fields
        import uuid
        cart_id = f"CART-{str(uuid.uuid4())[:8].upper()}"
        
        cart = Cart.objects.create(
            user=user,
            puja_service=puja_service,
            selected_date=datetime(2025, 8, 26).date(),
            selected_time="23:30",
            cart_id=cart_id,
            status='CONVERTED'  # Mark as converted since we're creating a booking
        )
        print(f"Created cart with ID: {cart.cart_id}")
        
        # Create booking with only valid fields
        booking = Booking.objects.create(
            book_id='BK-7EDFC3B4',
            user=user,
            cart=cart,
            address=address,
            selected_date=datetime(2025, 8, 26).date(),
            selected_time=time(23, 30),
            status='CONFIRMED'
        )
        
        print(f"SUCCESS: Created test booking with ID: {booking.book_id}")
        print(f"User: {booking.user.email}")
        print(f"Service: {booking.cart.puja_service.title}")
        print(f"Amount: Rs.{booking.total_amount}")
        print(f"Date: {booking.selected_date}")
        print(f"Location: Bihar")
        
        return booking
        
    except Exception as e:
        print(f"ERROR: Failed to create booking: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Creating Real Test Booking with Authentic Data")
    print("=" * 50)
    
    booking = create_real_test_booking()
    
    if booking:
        print("\nSUCCESS: Test booking created successfully!")
        print(f"You can now test emails and invoices with booking ID: {booking.book_id}")
    else:
        print("\nERROR: Failed to create test booking.")