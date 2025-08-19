#!/usr/bin/env python
"""
Email Template Preview
Creates a standalone HTML file to preview the email template in browser
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.template.loader import render_to_string
from booking.models import Booking

def create_email_preview():
    """Create email preview HTML file"""
    try:
        # Get the real test booking
        booking = Booking.objects.filter(book_id='BK-7EDFC3B4').first()
        if not booking:
            booking = Booking.objects.filter(book_id='BK-08D291CD').first()
            
        if not booking:
            print("ERROR: No test booking found. Run create_real_test_booking.py first.")
            return False
        
        print(f"Creating email preview for booking: {booking.book_id}")
        
        # Render the email template
        html_content = render_to_string('emails/booking_confirmation_professional.html', {
            'booking': booking,
            'MEDIA_URL': '/media/'
        })
        
        # Save to preview file
        preview_file = 'email_preview_professional.html'
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"SUCCESS: Email preview created: {preview_file}")
        print(f"Open this file in your browser to see how the email looks!")
        print(f"\nFile path: {os.path.abspath(preview_file)}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create preview: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_email_preview()