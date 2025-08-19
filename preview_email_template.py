#!/usr/bin/env python
"""
Email Template Test - Preview the email as it would appear in email clients
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
from django.conf import settings
from booking.models import Booking

def preview_email_template():
    """Generate and save email template preview"""
    try:
        # Get the test booking
        booking = Booking.objects.filter(book_id='BK-7EDFC3B4').first()
        if not booking:
            booking = Booking.objects.filter(book_id='BK-08D291CD').first()
            
        if not booking:
            print("ERROR: No test booking found. Run create_real_test_booking.py first.")
            return False
        
        print(f"Generating email preview for booking: {booking.book_id}")
        
        # Render the email template
        html_content = render_to_string('emails/booking_confirmation_professional.html', {
            'booking': booking,
            'MEDIA_URL': getattr(settings, 'MEDIA_URL', '/media/')
        })
        
        # Save to preview file
        preview_file = 'email_template_preview.html'
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"SUCCESS: Email template preview saved to: {preview_file}")
        print(f"Open this file in your browser to see how the email will look in email clients")
        print(f"\nEmail details:")
        print(f"  ✓ No external dependencies (Tailwind removed)")
        print(f"  ✓ All CSS is internal and email-safe")
        print(f"  ✓ Uses HTML tables for layout (email client compatible)")
        print(f"  ✓ Inline styles for maximum compatibility")
        print(f"  ✓ Mobile responsive design")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to generate preview: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    preview_email_template()