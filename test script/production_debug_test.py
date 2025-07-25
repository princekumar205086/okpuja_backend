#!/usr/bin/env python
"""
Production API Endpoint Test
Test the exact process-cart endpoint that's failing in production
"""

import requests
import json

def test_production_endpoint():
    """Test the production process-cart endpoint"""
    print("🧪 Testing Production Process-Cart Endpoint")
    print("=" * 60)
    
    endpoint = "https://api.okpuja.com/api/payments/payments/process-cart/"
    
    # Test payload
    payload = {
        "cart_id": 15,
        "method": "PHONEPE"
    }
    
    # We need a valid token - let's test without auth first to see the error
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"🌐 Endpoint: {endpoint}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        print("📡 Making request without authentication...")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Endpoint is responding (401 = authentication required)")
            print("💡 This confirms the server is working and updated")
        elif response.status_code == 400:
            # Parse the error to see if it's still V1 vs V2
            try:
                error_data = response.json()
                error_message = error_data.get('admin_message', '')
                
                if 'PhonePe API connection refused' in error_message:
                    print("❌ STILL USING V1 GATEWAY!")
                    print("💡 The production server hasn't fully reloaded the V2 code")
                else:
                    print("✅ Using V2 gateway (different error)")
                    
            except:
                print("⚠️ Could not parse error response")
                
    except Exception as e:
        print(f"❌ Request error: {e}")

def create_production_debug_script():
    """Create a script to debug the production issue"""
    debug_script = '''#!/usr/bin/env python
"""
Production Debug Script - Run this on the production server
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/opt/api.okpuja.com')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def check_imports():
    """Check what gateway is actually being imported"""
    print("🔍 Checking Gateway Imports")
    print("=" * 40)
    
    try:
        # Check if V2 gateway can be imported
        from payment.gateways_v2 import get_payment_gateway_v2
        print("✅ V2 Gateway: Can import get_payment_gateway_v2")
        
        # Check what views.py is actually importing
        import payment.views
        print(f"✅ Views module: {payment.views.__file__}")
        
        # Check if views has the V2 import
        if hasattr(payment.views, 'get_payment_gateway_v2'):
            print("✅ Views: Has get_payment_gateway_v2 import")
        else:
            print("❌ Views: Missing get_payment_gateway_v2 import")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        
def test_gateway_creation():
    """Test creating both V1 and V2 gateways"""
    print("\\n🧪 Testing Gateway Creation")
    print("=" * 40)
    
    try:
        # Test V1 gateway
        from payment.gateways import get_payment_gateway
        v1_gateway = get_payment_gateway('phonepe')
        print(f"✅ V1 Gateway: {type(v1_gateway).__name__}")
        
        # Test V2 gateway
        from payment.gateways_v2 import get_payment_gateway_v2
        v2_gateway = get_payment_gateway_v2('phonepe')
        print(f"✅ V2 Gateway: {type(v2_gateway).__name__}")
        
    except Exception as e:
        print(f"❌ Gateway creation error: {e}")

def main():
    """Main debug function"""
    print("🔍 Production Gateway Debug")
    print("=" * 50)
    
    check_imports()
    test_gateway_creation()
    
    print("\\n💡 If V2 gateway can be imported but views still use V1:")
    print("   1. Check if views.py was properly updated")
    print("   2. Restart gunicorn with: sudo systemctl restart gunicorn_api_okpuja")
    print("   3. Clear Python cache: find . -name '*.pyc' -delete")

if __name__ == "__main__":
    main()
'''
    
    return debug_script

def main():
    """Main test function"""
    print("🚨 PRODUCTION DEBUGGING REQUIRED")
    print("=" * 60)
    print("The V2 test script works, but the actual API endpoint still fails")
    print("This suggests a caching or import issue on production")
    print()
    
    # Test the actual endpoint
    test_production_endpoint()
    
    # Create debug script
    debug_script = create_production_debug_script()
    
    print("\n🔧 DEBUGGING STEPS:")
    print("=" * 60)
    print("1. SSH into your production server")
    print("2. Create and run this debug script:")
    print()
    print("```bash")
    print("cd /opt/api.okpuja.com")
    print("cat > production_debug.py << 'EOF'")
    print(debug_script)
    print("EOF")
    print("python production_debug.py")
    print("```")
    print()
    print("3. If the debug shows V1 still being used:")
    print("   - Clear Python cache: find . -name '*.pyc' -delete")
    print("   - Force restart: sudo systemctl restart gunicorn_api_okpuja")
    print("   - Check views.py was updated: grep -n 'get_payment_gateway_v2' payment/views.py")

if __name__ == "__main__":
    main()
