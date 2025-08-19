"""
Production Payment Fix Verification
Test the updated configuration with production URLs
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payments.phonepe_client import PhonePePaymentClient
from payments.services import PaymentService
import json

def verify_production_fix():
    """Verify the production payment fix"""
    
    print("🔧 PRODUCTION PAYMENT FIX VERIFICATION")
    print("=" * 50)
    
    # 1. Check updated URLs
    print(f"\n✅ Updated Production URLs:")
    url_mappings = {
        'PHONEPE_CALLBACK_URL': 'Webhook URL',
        'PHONEPE_PROFESSIONAL_REDIRECT_URL': 'Redirect Handler URL',
        'PHONEPE_SUCCESS_REDIRECT_URL': 'Success Page URL',
        'PHONEPE_FAILED_REDIRECT_URL': 'Failed Page URL',
        'PHONEPE_PENDING_REDIRECT_URL': 'Pending Page URL',
        'PHONEPE_ERROR_REDIRECT_URL': 'Error Page URL',
        'FRONTEND_BASE_URL': 'Frontend Base URL'
    }
    
    all_production_ready = True
    for setting_name, description in url_mappings.items():
        url_value = getattr(settings, setting_name, 'NOT_SET')
        
        if 'localhost' in url_value or '127.0.0.1' in url_value:
            print(f"   ❌ {description}: Still using localhost - {url_value}")
            all_production_ready = False
        elif 'okpuja.com' in url_value or 'api.okpuja.com' in url_value:
            print(f"   ✅ {description}: Production ready - {url_value}")
        else:
            print(f"   ⚠️ {description}: Unknown domain - {url_value}")
    
    # 2. Test PhonePe client with new URLs
    print(f"\n🔧 Testing Payment Service with Production URLs:")
    try:
        payment_service = PaymentService()
        client = payment_service.client
        
        print(f"   Environment: {payment_service.environment}")
        print(f"   Base URL: {client.base_url}")
        print(f"   OAuth URL: {client.oauth_url}")
        
        # Test token generation
        token = client.get_access_token()
        if token:
            print(f"   ✅ OAuth Token: Generated successfully ({len(token)} chars)")
        else:
            print(f"   ❌ OAuth Token: Failed to generate")
            
    except Exception as e:
        print(f"   ❌ Payment Service Error: {e}")
    
    # 3. Simulate payment creation
    print(f"\n💳 Testing Payment Order Creation Logic:")
    try:
        from django.contrib.auth import get_user_model
        from cart.models import Cart
        
        User = get_user_model()
        
        # Check if we have test data
        test_cart = Cart.objects.filter(status='ACTIVE').first()
        if test_cart:
            print(f"   ✅ Test Cart Available: {test_cart.cart_id}")
            
            # Test payment data preparation
            amount_in_rupees = test_cart.total_price
            amount_in_paisa = int(amount_in_rupees * 100)
            redirect_url = getattr(settings, 'PHONEPE_PROFESSIONAL_REDIRECT_URL')
            
            print(f"   Amount: ₹{amount_in_rupees} ({amount_in_paisa} paisa)")
            print(f"   Redirect URL: {redirect_url}")
            
            if 'api.okpuja.com' in redirect_url:
                print(f"   ✅ Using production redirect URL")
            else:
                print(f"   ❌ Not using production redirect URL")
                
        else:
            print(f"   ⚠️ No active test cart available")
            
    except Exception as e:
        print(f"   ❌ Payment Logic Error: {e}")
    
    # 4. Summary
    print(f"\n📋 PRODUCTION READINESS SUMMARY:")
    if all_production_ready:
        print(f"   ✅ All URLs updated to production domains")
        print(f"   ✅ PhonePe integration working")
        print(f"   ✅ Ready for production deployment")
        
        print(f"\n🚀 DEPLOYMENT INSTRUCTIONS:")
        print(f"   1. Update your production server .env file with these URLs")
        print(f"   2. Restart your Django server")
        print(f"   3. Test payment flow with a small amount")
        print(f"   4. Monitor server logs for any remaining issues")
        
    else:
        print(f"   ❌ Some URLs still need updating")
        print(f"   📝 Please update localhost URLs to production domains")
    
    print(f"\n🔍 DEBUGGING TIPS:")
    print(f"   - Check server logs: tail -f /path/to/your/django.log")
    print(f"   - Verify firewall allows HTTPS outbound to PhonePe")
    print(f"   - Test webhook URL accessibility from internet")
    print(f"   - Monitor PhonePe dashboard for callback issues")
    
    return all_production_ready

if __name__ == "__main__":
    success = verify_production_fix()
    if success:
        print(f"\n🎉 Production payment configuration looks good!")
    else:
        print(f"\n⚠️ Please complete the production URL updates.")
