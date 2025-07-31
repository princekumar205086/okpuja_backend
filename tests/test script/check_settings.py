#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def check_phonepe_settings():
    """Check PhonePe settings loaded by Django"""
    print("🔍 Checking PhonePe Settings in Django...")
    
    attrs = [
        'PHONEPE_ENV',
        'PHONEPE_MERCHANT_ID', 
        'PHONEPE_MERCHANT_KEY',
        'PHONEPE_SALT_INDEX',
        'PHONEPE_BASE_URL'
    ]
    
    for attr in attrs:
        value = getattr(settings, attr, 'NOT SET')
        if 'KEY' in attr and value != 'NOT SET':
            value = '*' * len(value)  # Hide sensitive data
        print(f"{attr}: {value}")

if __name__ == "__main__":
    check_phonepe_settings()
