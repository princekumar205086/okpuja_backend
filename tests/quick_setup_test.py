"""
Quick Test Script for PhonePe V2 Setup
Validates basic setup and configuration
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.phonepe_v2_client import PhonePeV2Client, PhonePeException

def test_configuration():
    """Test PhonePe configuration"""
    print("🔧 Testing PhonePe V2 Configuration...")
    
    required_settings = [
        'PHONEPE_CLIENT_ID',
        'PHONEPE_CLIENT_SECRET', 
        'PHONEPE_CLIENT_VERSION',
        'PHONEPE_MERCHANT_ID',
        'PHONEPE_CALLBACK_URL',
        'PHONEPE_SUCCESS_REDIRECT_URL'
    ]
    
    missing_settings = []
    
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if not value:
            missing_settings.append(setting)
        else:
            # Hide sensitive data
            display_value = value[:10] + "..." if len(str(value)) > 10 else value
            print(f"   ✅ {setting}: {display_value}")
    
    if missing_settings:
        print(f"   ❌ Missing settings: {', '.join(missing_settings)}")
        return False
    
    print("   ✅ All required settings present")
    return True

def test_client_initialization():
    """Test PhonePe client initialization"""
    print("\n🔌 Testing PhonePe Client Initialization...")
    
    try:
        from payment.phonepe_v2_simple import PhonePeV2ClientSimplified
        client = PhonePeV2ClientSimplified(env="sandbox")
        print("   ✅ PhonePe V2 simplified client initialized successfully")
        print(f"   📍 Environment: sandbox")
        print(f"   🔗 Base URL: {client.base_url}")
        return client
    except Exception as e:
        print(f"   ❌ Client initialization failed: {str(e)}")
        return None

def test_connectivity(client):
    """Test basic connectivity"""
    print("\n🔗 Testing Connectivity...")
    
    if not client:
        print("   ❌ No client available")
        return False
    
    try:
        results = client.test_connectivity()
        
        for result in results:
            status_icon = "✅" if result['status'] == 'OK' else "❌"
            print(f"   {status_icon} {result['url']}: {result.get('status_code', result.get('error'))}")
        
        return any(r['status'] == 'OK' for r in results)
        
    except Exception as e:
        print(f"   ❌ Connectivity test failed: {str(e)}")
        return False

def test_oauth_token(client):
    """Test OAuth token generation (simplified version doesn't need OAuth)"""
    print("\n🔐 Testing OAuth Token Generation...")
    
    if not client:
        print("   ❌ No client available")
        return False
    
    try:
        # For simplified client, just test the dummy method
        token = client.get_access_token()
        
        if token:
            print(f"   ✅ Token method works (simplified): {token}")
            return True
        else:
            print("   ❌ No token received")
            return False
            
    except Exception as e:
        print(f"   ❌ Token method failed: {str(e)}")
        return False

def test_imports():
    """Test if all imports work correctly"""
    print("\n📦 Testing Imports...")
    
    try:
        from payment.services import PaymentService
        print("   ✅ PaymentService imported")
        
        from payment.phonepe_v2_simple import PhonePeV2ClientSimplified
        print("   ✅ PhonePeV2ClientSimplified imported")
        
        from payment.serializers_v2 import PaymentCreateSerializer
        print("   ✅ PaymentCreateSerializer imported")
        
        from payment.views import PaymentViewSet
        print("   ✅ PaymentViewSet imported")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        return False

def main():
    """Run all basic tests"""
    print("🧪 PhonePe V2 Quick Setup Test")
    print("=" * 40)
    
    # Test 1: Configuration
    config_ok = test_configuration()
    
    # Test 2: Imports
    imports_ok = test_imports()
    
    # Test 3: Client initialization
    client = test_client_initialization()
    
    # Test 4: Connectivity (if client works)
    connectivity_ok = test_connectivity(client) if client else False
    
    # Test 5: OAuth (if connectivity works)
    oauth_ok = test_oauth_token(client) if connectivity_ok else False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Quick Test Results:")
    print(f"   Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Client Init: {'✅ PASS' if client else '❌ FAIL'}")
    print(f"   Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
    print(f"   OAuth Token: {'✅ PASS' if oauth_ok else '❌ FAIL'}")
    
    overall_status = all([config_ok, imports_ok, client, connectivity_ok, oauth_ok])
    
    print(f"\n🎯 Overall Status: {'✅ READY FOR TESTING' if overall_status else '❌ NEEDS FIXING'}")
    
    if overall_status:
        print("\n🚀 Next Steps:")
        print("   1. Run the full test suite: python tests/test_phonepe_v2_integration.py")
        print("   2. Test the API endpoints: python tests/test_payment_api.py")
        print("   3. Or run PowerShell script: tests/run_payment_tests.ps1")
    else:
        print("\n🔧 Fix the failing tests above before proceeding")

if __name__ == "__main__":
    main()
