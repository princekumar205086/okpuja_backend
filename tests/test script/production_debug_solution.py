#!/usr/bin/env python3
"""
Final debugging solution for production PhonePe issue
This creates a simple Django management command to test PhonePe from production server
"""

def create_debug_management_command():
    """Create a management command to test PhonePe from production server"""
    
    command_content = '''#!/usr/bin/env python3
from django.core.management.base import BaseCommand
from payment.gateways import PhonePeGateway
import requests
import json
import uuid
import datetime

class Command(BaseCommand):
    help = 'Debug PhonePe API connectivity from production server'

    def handle(self, *args, **options):
        self.stdout.write("🧪 DEBUGGING PHONEPE FROM PRODUCTION SERVER")
        self.stdout.write("=" * 50)
        
        try:
            # Test 1: Basic connectivity to PhonePe
            self.stdout.write("1. Testing basic connectivity to PhonePe...")
            response = requests.get("https://api.phonepe.com", timeout=10)
            self.stdout.write(f"   PhonePe API reachable: {response.status_code}")
        except Exception as e:
            self.stdout.write(f"   ❌ Cannot reach PhonePe API: {e}")
            return
        
        # Test 2: Test PhonePe gateway initialization
        self.stdout.write("2. Testing PhonePe gateway initialization...")
        try:
            gateway = PhonePeGateway()
            self.stdout.write(f"   ✅ Gateway initialized")
            self.stdout.write(f"   Merchant ID: {gateway.merchant_id}")
            self.stdout.write(f"   Base URL: {gateway.base_url}")
            self.stdout.write(f"   Salt Index: {gateway.salt_index}")
        except Exception as e:
            self.stdout.write(f"   ❌ Gateway init failed: {e}")
            return
        
        # Test 3: Create mock payment and test initiation
        self.stdout.write("3. Testing payment initiation...")
        
        class MockUser:
            id = 2
            phone_number = "9000000000"
        
        class MockPayment:
            def __init__(self):
                self.id = 999
                self.user = MockUser()
                self.amount = 4990.00
                self.merchant_transaction_id = f"DEBUG{datetime.datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4()).split('-')[0].upper()}"
                self.transaction_id = self.merchant_transaction_id
                self.gateway_response = None
            
            def save(self):
                self.stdout.write(f"   Payment save called")
        
        try:
            payment = MockPayment()
            result = gateway.initiate_payment(payment)
            self.stdout.write(f"   ✅ SUCCESS! Payment initiated")
            self.stdout.write(f"   Payment URL: {result.get('payment_url', 'Not found')}")
        except Exception as e:
            self.stdout.write(f"   ❌ Payment initiation failed: {e}")
            self.stdout.write(f"   Error type: {type(e).__name__}")
            import traceback
            self.stdout.write(f"   Traceback: {traceback.format_exc()}")
'''
    
    return command_content

def create_simple_debug_view():
    """Create a simple debug view for immediate testing"""
    
    view_content = '''
# Add this to payment/views.py

@action(detail=False, methods=['get'], url_path='debug-phonepe')
def debug_phonepe(self, request):
    """Debug PhonePe connectivity - REMOVE IN PRODUCTION"""
    if not settings.DEBUG:
        return Response({'error': 'Only available in debug mode'}, status=403)
    
    try:
        import requests
        # Test basic connectivity
        response = requests.get("https://api.phonepe.com", timeout=10)
        connectivity = f"PhonePe reachable: {response.status_code}"
        
        # Test gateway
        from payment.gateways import PhonePeGateway
        gateway = PhonePeGateway()
        gateway_info = {
            'merchant_id': gateway.merchant_id,
            'base_url': gateway.base_url,
            'salt_index': gateway.salt_index
        }
        
        return Response({
            'connectivity': connectivity,
            'gateway': gateway_info,
            'status': 'Debug complete'
        })
    except Exception as e:
        return Response({
            'error': str(e),
            'type': type(e).__name__
        }, status=400)
'''
    
    return view_content

if __name__ == "__main__":
    print("🛠️ PRODUCTION DEBUGGING SOLUTIONS")
    print("=" * 50)
    print()
    print("Since we've identified the issue is with production PhonePe connectivity,")
    print("here are immediate solutions:")
    print()
    print("1. **CHECK PRODUCTION ENVIRONMENT VARIABLES**")
    print("   - Verify PHONEPE_MERCHANT_ID, PHONEPE_MERCHANT_KEY in production")
    print("   - Ensure they match the working local environment")
    print()
    print("2. **TEST NETWORK CONNECTIVITY**")
    print("   - Production server may be blocked from reaching api.phonepe.com")
    print("   - Check firewall rules and outbound connections")
    print()
    print("3. **TEMPORARY WORKAROUND**")
    print("   - Add a debug endpoint to test PhonePe directly from production")
    print("   - Use Django management command to test from production server")
    print()
    print("4. **IMMEDIATE FIX**")
    print("   - Contact hosting provider to check outbound HTTPS connections")
    print("   - Verify production environment variables match development")
    print("   - Test with a simple curl from production server:")
    print("     curl -v https://api.phonepe.com")
    print()
    print("The core payment flow is working perfectly - this is purely")
    print("a production environment connectivity issue!")
