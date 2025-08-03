#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

# Setup Django
django.setup()

from payments.models import PaymentOrder
from payments.services import PaymentService
from django.utils import timezone
from datetime import timedelta

def test_payment_verification():
    print("🔍 Testing Payment Verification...")
    
    # Get INITIATED payments older than 2 minutes
    cutoff = timezone.now() - timedelta(minutes=2)
    payments = PaymentOrder.objects.filter(status='INITIATED', created_at__lt=cutoff)[:3]
    
    print(f"📋 Found {payments.count()} INITIATED payments to test")
    
    if not payments:
        print("❌ No INITIATED payments found")
        return
    
    service = PaymentService()
    
    for payment in payments:
        print(f"\n🔍 Testing payment: {payment.merchant_order_id}")
        print(f"   Created: {payment.created_at}")
        print(f"   Amount: ₹{payment.amount_in_rupees}")
        
        try:
            result = service.check_payment_status(payment.merchant_order_id)
            print(f"   Result: {result}")
            
            if result and result.get('success'):
                print("   ✅ API call successful")
                if result.get('payment_order'):
                    updated_payment = result['payment_order']
                    print(f"   Status: {updated_payment.status}")
                else:
                    print("   ⚠️ No payment_order in result")
            else:
                print("   ❌ API call failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_payment_verification()
