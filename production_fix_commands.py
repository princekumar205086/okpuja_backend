#!/usr/bin/env python
"""
Quick Production Fix - Force V2 Gateway Usage
This script will help ensure production is using V2 gateway
"""

def show_production_commands():
    """Show commands to run on production server"""
    print("🚨 PRODUCTION QUICK FIX")
    print("=" * 50)
    print("Run these commands on your production server:")
    print()
    
    commands = [
        "# 1. Navigate to project directory",
        "cd /opt/api.okpuja.com",
        "",
        "# 2. Check if views.py has V2 gateway imports", 
        "grep -n 'get_payment_gateway_v2' payment/views.py",
        "",
        "# 3. If the above shows no results, the views.py wasn't updated. Force pull:",
        "git status",
        "git reset --hard origin/main",
        "git pull origin main",
        "",
        "# 4. Verify V2 files exist",
        "ls -la payment/gateways_v2.py",
        "ls -la simple_v2_check.py",
        "",
        "# 5. Clear Python cache",
        "find . -name '*.pyc' -delete",
        "find . -name '__pycache__' -type d -exec rm -rf {} +",
        "",
        "# 6. Restart services",
        "sudo systemctl restart gunicorn_api_okpuja",
        "sudo systemctl status gunicorn_api_okpuja",
        "",
        "# 7. Test V2 integration",
        "python simple_v2_check.py",
        "",
        "# 8. Test the actual endpoint (should show different error now)",
        "curl -X POST https://backend.okpuja.com/api/payments/payments/process-cart/ \\",
        "     -H 'Content-Type: application/json' \\",
        "     -d '{\"cart_id\": 15, \"method\": \"PHONEPE\"}'"
    ]
    
    for cmd in commands:
        print(cmd)
    
    print("\n💡 EXPECTED RESULTS:")
    print("=" * 50)
    print("✅ grep command should show V2 gateway imports")
    print("✅ V2 integration test should show 'WORKING!'")
    print("✅ curl command should show 401 auth error (not CONNECTION_REFUSED)")
    print()
    print("If you still get CONNECTION_REFUSED after these steps,")
    print("there might be an import issue in the production environment.")

def show_manual_fix():
    """Show manual fix if automated doesn't work"""
    print("\n🔧 MANUAL FIX (if above doesn't work):")
    print("=" * 50)
    print("1. Check the views.py file on production:")
    print("   cat payment/views.py | grep -A5 -B5 'get_payment_gateway'")
    print()
    print("2. If it still shows 'get_payment_gateway' instead of 'get_payment_gateway_v2':")
    print("   - The git pull didn't update the file properly")
    print("   - Manually edit the file or re-upload it")
    print()
    print("3. Look for these specific lines in payment/views.py:")
    print("   Line ~82: gateway = get_payment_gateway_v2('phonepe')")
    print("   Line ~185: gateway = get_payment_gateway_v2('phonepe')")
    print("   Line ~254: gateway = get_payment_gateway_v2(payment.method.lower())")
    print("   Line ~354: gateway = get_payment_gateway_v2('phonepe')")
    print("   Line ~932: gateway = get_payment_gateway_v2(gateway_name)")

def main():
    """Main function"""
    print("🎯 PRODUCTION V2 DEPLOYMENT TROUBLESHOOTING")
    print("=" * 60)
    print("The V2 test script works, but the API endpoint still uses V1 gateway")
    print("This means the views.py file wasn't properly updated on production")
    print()
    
    show_production_commands()
    show_manual_fix()
    
    print("\n🎉 AFTER THE FIX:")
    print("=" * 60)
    print("✅ Frontend payment should work without CONNECTION_REFUSED error")
    print("✅ Payment URLs will be generated successfully")
    print("✅ PhonePe V2 integration will be fully functional")

if __name__ == "__main__":
    main()
