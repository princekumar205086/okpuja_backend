#!/usr/bin/env python
"""
Test basic Django setup
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✅ Django setup successful")
    
    # Test basic imports
    from django.conf import settings
    print("✅ Settings imported")
    
    from django.contrib.auth import get_user_model
    print("✅ User model imported")
    
    # Test our models
    from cart.models import Cart
    print("✅ Cart model imported")
    
    from payments.models import PaymentOrder
    print("✅ PaymentOrder model imported")
    
    from puja.models import PujaService, Package
    print("✅ Puja models imported")
    
    from booking.models import Booking
    print("✅ Booking model imported")
    
    print("\n🎉 All basic imports successful!")
    print("Django environment is properly configured.")
    
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    import traceback
    traceback.print_exc()
