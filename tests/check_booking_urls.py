#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.urls import reverse
from booking.views import BookingViewSet

def check_booking_urls():
    """Check available booking URLs"""
    print("=== CHECKING BOOKING URLS ===\n")
    
    try:
        # Check if the custom actions are available
        actions = BookingViewSet.get_extra_actions()
        print("Available actions:")
        for action in actions:
            print(f"  - {action['name']}: {action.get('url_path', 'N/A')}")
    except Exception as e:
        print(f"Error getting actions: {e}")
    
    # Try to reverse some common URLs
    try:
        booking_list = reverse('booking-list')
        print(f"\nBooking list URL: {booking_list}")
    except Exception as e:
        print(f"Error reversing booking-list: {e}")

if __name__ == "__main__":
    check_booking_urls()
