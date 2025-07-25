#!/usr/bin/env python3
"""
Runtime diagnostic to check what gateway is actually being used
"""

import django
import os
import sys

# Add the project directory to Python path
sys.path.append('/opt/api.okpuja.com')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def check_runtime_imports():
    print("🔍 Runtime Import Check")
    print("=" * 25)
    
    try:
        # Try to import the views module
        from payment import views
        print("✅ payment.views imported successfully")
        
        # Check what gateway function is available
        if hasattr(views, 'get_payment_gateway_v2'):
            print("✅ get_payment_gateway_v2 function is available")
        else:
            print("❌ get_payment_gateway_v2 function NOT available")
            
        # Check the actual file path being used
        print(f"📁 Views.py path: {views.__file__}")
        
        # Try to import the gateway directly
        try:
            from payment.gateways_v2 import get_payment_gateway_v2
            print("✅ gateways_v2.get_payment_gateway_v2 imported successfully")
            
            # Test the gateway
            gateway = get_payment_gateway_v2('phonepe')
            print(f"✅ V2 Gateway created: {type(gateway)}")
            
        except ImportError as e:
            print(f"❌ Failed to import gateways_v2: {e}")
            
    except ImportError as e:
        print(f"❌ Failed to import payment.views: {e}")

def check_view_source():
    print("\n📖 Checking Views.py Source")
    print("=" * 28)
    
    views_path = "/opt/api.okpuja.com/payment/views.py"
    
    try:
        with open(views_path, 'r') as f:
            lines = f.readlines()
            
        print("🔍 Import statements in views.py:")
        for i, line in enumerate(lines[:50], 1):  # Check first 50 lines
            if 'import' in line and ('gateway' in line.lower() or 'phonepe' in line.lower()):
                print(f"Line {i}: {line.strip()}")
                
        print("\n🔍 Gateway usage in views.py:")
        for i, line in enumerate(lines, 1):
            if 'get_payment_gateway' in line:
                print(f"Line {i}: {line.strip()}")
                
    except Exception as e:
        print(f"❌ Failed to read views.py: {e}")

def test_process_cart_view():
    print("\n🧪 Testing Process Cart View Function")
    print("=" * 35)
    
    try:
        from payment.views import PaymentViewSet
        print("✅ PaymentViewSet imported successfully")
        
        # Check if the view has the process_cart method
        if hasattr(PaymentViewSet, 'process_cart'):
            print("✅ process_cart method exists")
            
            # Get the method
            method = getattr(PaymentViewSet, 'process_cart')
            print(f"📋 Method: {method}")
            
        else:
            print("❌ process_cart method NOT found")
            
    except Exception as e:
        print(f"❌ Failed to test view: {e}")

if __name__ == "__main__":
    print("🔍 DJANGO RUNTIME DIAGNOSTIC")
    print("=" * 40)
    print(f"📅 Time: {os.popen('date').read().strip()}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[:3]}...")
    
    check_runtime_imports()
    check_view_source()
    test_process_cart_view()
    
    print("\n" + "="*50)
    print("🎯 DIAGNOSTIC COMPLETE")
    print("="*50)
    print("If V2 gateway imports are working but payments still fail,")
    print("the issue is likely in the actual request handling or")
    print("the gunicorn process is still using cached/old code.")
    print()
    print("🚨 Next step: Run force_fix_gunicorn.sh")
