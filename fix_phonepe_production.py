#!/usr/bin/env python
"""
PhonePe Production Fix Script
This script fixes the PhonePe connection issues for production servers
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.gateways import PhonePeGateway
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhonePeProductionFix:
    def __init__(self):
        self.gateway = PhonePeGateway()
        
    def check_and_fix_settings(self):
        """Check and suggest fixes for settings"""
        
        print("🔧 PHONEPE PRODUCTION FIX")
        print("=" * 50)
        
        # Check current settings
        print("\n1. Current Configuration:")
        print(f"   PHONEPE_MERCHANT_ID: {'SET' if settings.PHONEPE_MERCHANT_ID else 'NOT SET'}")
        print(f"   PHONEPE_MERCHANT_KEY: {'SET' if settings.PHONEPE_MERCHANT_KEY else 'NOT SET'}")
        print(f"   PHONEPE_ENV: {getattr(settings, 'PHONEPE_ENV', 'NOT SET')}")
        print(f"   PHONEPE_BASE_URL: {settings.PHONEPE_BASE_URL}")
        print(f"   PRODUCTION_SERVER: {getattr(settings, 'PRODUCTION_SERVER', False)}")
        
        # Test connectivity
        print("\n2. Testing Connectivity:")
        connectivity = self.gateway.test_connectivity()
        
        working_endpoints = [r for r in connectivity if r['status'] == 'connected']
        failed_endpoints = [r for r in connectivity if r['status'] != 'connected']
        
        print(f"   Working endpoints: {len(working_endpoints)}")
        print(f"   Failed endpoints: {len(failed_endpoints)}")
        
        if not working_endpoints:
            print("\n❌ NO WORKING ENDPOINTS FOUND!")
            print("This indicates a network connectivity issue on your server.")
            return False
        
        # Create environment fixes
        print("\n3. Creating Environment File Fix:")
        
        env_content = """
# PhonePe Production Configuration
PHONEPE_ENV=PRODUCTION
PHONEPE_MERCHANT_ID=your_merchant_id_here
PHONEPE_MERCHANT_KEY=your_merchant_key_here
PHONEPE_SALT_INDEX=1

# Production URLs (Update these to your actual URLs)
PHONEPE_CALLBACK_URL=https://backend.okpuja.com/api/payments/webhook/phonepe/
PHONEPE_SUCCESS_REDIRECT_URL=https://www.okpuja.com/confirmbooking/
PHONEPE_FAILED_REDIRECT_URL=https://www.okpuja.com/failedbooking

# Production Server Flag
PRODUCTION_SERVER=True

# Enhanced PhonePe Settings for Production
PHONEPE_TIMEOUT=120
PHONEPE_MAX_RETRIES=5
PHONEPE_SSL_VERIFY=True
"""
        
        with open('.env.phonepe.example', 'w') as f:
            f.write(env_content.strip())
            
        print("   ✅ Created '.env.phonepe.example' with production settings")
        
        return len(working_endpoints) > 0
    
    def create_test_payment(self):
        """Create a test payment to verify the fix"""
        
        from django.contrib.auth import get_user_model
        from payment.models import Payment, PaymentStatus
        from cart.models import Cart
        
        User = get_user_model()
        
        # Create or get test user
        test_user, created = User.objects.get_or_create(
            email='test@okpuja.com',
            defaults={
                'phone_number': '9000000000',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # Create test cart (minimal)
        test_cart = Cart.objects.create(
            user=test_user,
            total_amount=100.00  # 100 rupees
        )
        
        # Create test payment
        test_payment = Payment.objects.create(
            user=test_user,
            cart=test_cart,
            amount=100.00,
            status=PaymentStatus.PENDING,
            gateway='phonepe'
        )
        
        print(f"\n4. Testing Payment Creation:")
        print(f"   Created test payment: {test_payment.id}")
        print(f"   Transaction ID: {test_payment.transaction_id}")
        
        try:
            # Try to initiate payment
            result = self.gateway.initiate_payment(test_payment)
            
            print("   ✅ Payment initiation SUCCESSFUL!")
            print(f"   Payment URL: {result.get('payment_url', 'N/A')}")
            
            # Clean up test payment
            test_payment.delete()
            test_cart.delete()
            if created:
                test_user.delete()
                
            return True
            
        except Exception as e:
            print(f"   ❌ Payment initiation FAILED: {str(e)}")
            
            # Clean up test payment
            test_payment.delete()
            test_cart.delete()
            if created:
                test_user.delete()
                
            return False
    
    def run_fix(self):
        """Run the complete fix process"""
        
        connectivity_ok = self.check_and_fix_settings()
        
        if connectivity_ok:
            payment_ok = self.create_test_payment()
            
            print("\n" + "=" * 50)
            if payment_ok:
                print("🎉 PHONEPE FIX SUCCESSFUL!")
                print("Your PhonePe integration is now working.")
            else:
                print("⚠️  PARTIAL FIX COMPLETED")
                print("Connectivity is OK, but payment initiation failed.")
                print("Check your PhonePe merchant credentials.")
        else:
            print("\n" + "=" * 50)
            print("❌ NETWORK CONNECTIVITY ISSUE")
            print("Your server cannot connect to PhonePe APIs.")
            print("Contact your hosting provider about:")
            print("- Outbound HTTPS connections (port 443)")
            print("- DNS resolution for api.phonepe.com")
            print("- Firewall rules blocking external API calls")
        
        print("\nNext Steps:")
        print("1. Update your .env file with the values from .env.phonepe.example")
        print("2. Set your actual PhonePe merchant credentials")
        print("3. Ensure your hosting provider allows outbound HTTPS connections")
        print("4. Restart your Django server after updating settings")
        
        print("=" * 50)

if __name__ == "__main__":
    fix = PhonePeProductionFix()
    fix.run_fix()
