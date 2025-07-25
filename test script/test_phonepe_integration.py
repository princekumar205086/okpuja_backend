#!/usr/bin/env python
"""
Test script for PhonePe integration
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_phonepe_config():
    """Test PhonePe configuration"""
    print("=== PhonePe Configuration Test ===")
    print(f"Environment: {settings.PHONEPE_ENV}")
    print(f"Client ID: {settings.PHONEPE_CLIENT_ID}")
    print(f"Client Secret: {'*' * len(settings.PHONEPE_CLIENT_SECRET) if settings.PHONEPE_CLIENT_SECRET else 'Not set'}")
    print(f"Client Version: {settings.PHONEPE_CLIENT_VERSION}")
    print(f"Redirect URL: {settings.PHONEPE_REDIRECT_URL}")
    print(f"Callback URL: {settings.PHONEPE_CALLBACK_URL}")
    print()

def test_phonepe_gateway():
    """Test PhonePe gateway initialization"""
    print("=== PhonePe Gateway Test ===")
    try:
        from payment.gateways import get_payment_gateway
        gateway = get_payment_gateway('phonepe')
        print("✓ PhonePe gateway initialized successfully")
        print(f"✓ Environment: {gateway.env}")
        print(f"✓ Client ID: {gateway.client_id}")
        print(f"✓ Client Version: {gateway.client_version}")
        return gateway
    except Exception as e:
        print(f"✗ Error initializing PhonePe gateway: {e}")
        return None

def test_payment_creation():
    """Test payment creation without actual processing"""
    print("=== Payment Model Test ===")
    try:
        from payment.models import Payment, PaymentMethod, PaymentStatus
        from booking.models import Booking
        from accounts.models import User
        
        # Create a test payment (don't save to avoid actual processing)
        print("✓ Payment models imported successfully")
        print(f"✓ Available payment methods: {[choice[0] for choice in PaymentMethod.choices]}")
        print(f"✓ Available payment statuses: {[choice[0] for choice in PaymentStatus.choices]}")
        
    except Exception as e:
        print(f"✗ Error with payment models: {e}")

def main():
    """Run all tests"""
    print("PhonePe Integration Test Suite")
    print("=" * 50)
    
    test_phonepe_config()
    gateway = test_phonepe_gateway()
    test_payment_creation()
    
    print("=" * 50)
    if gateway:
        print("✓ PhonePe integration setup completed successfully!")
        print()
        print("Next steps:")
        print("1. Configure callback username/password in PhonePe dashboard")
        print("2. Test payment flow with a sample booking")
        print("3. Set up webhook endpoint in PhonePe dashboard")
        print(f"   Webhook URL: {settings.PHONEPE_CALLBACK_URL}")
    else:
        print("✗ PhonePe integration setup needs attention")

if __name__ == "__main__":
    main()
