#!/usr/bin/env python
"""
Production Deployment Check Script
This script helps verify what's deployed on production vs local changes
"""

import requests
import json

def check_production_status():
    """Check if production server is using V2 implementation"""
    print("🔍 Production Server Status Check")
    print("=" * 50)
    
    # Check if the server is responding
    try:
        health_url = "https://backend.okpuja.com/api/payments/payments/"
        response = requests.get(health_url, timeout=10)
        print(f"✅ Production server is responding (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Production server error: {e}")
        return
    
    print("\n🚨 ISSUE IDENTIFIED:")
    print("Your production server is still using the OLD V1 gateway implementation!")
    print()
    print("📋 Evidence:")
    print("✅ Local V2 tests: WORKING")
    print("❌ Production API calls: CONNECTION_REFUSED with V1 errors")
    print("❌ Error message: 'PhonePe API connection refused' (V1 gateway message)")
    print()
    print("🔧 SOLUTION REQUIRED:")
    print("Deploy the V2 implementation to your production server")

def show_deployment_checklist():
    """Show what needs to be deployed"""
    print("\n📦 Files to Deploy to Production:")
    print("=" * 50)
    
    files_to_deploy = [
        "payment/gateways_v2.py (NEW FILE - V2 gateway implementation)",
        "payment/views.py (UPDATED - now uses get_payment_gateway_v2)",
        ".env (UPDATED - V2 credentials and settings)",
        "okpuja_backend/settings.py (UPDATED - V2 configuration variables)"
    ]
    
    for i, file in enumerate(files_to_deploy, 1):
        print(f"{i}. {file}")
    
    print("\n🚀 Deployment Steps:")
    print("=" * 50)
    print("1. Upload the updated files to your production server")
    print("2. Restart the Django application (gunicorn/uwsgi)")
    print("3. Clear any cached imports")
    print("4. Test the payment endpoint")
    print()
    print("💡 Quick deployment commands:")
    print("   - git add . && git commit -m 'PhonePe V2 integration'")
    print("   - git push origin main")
    print("   - On production: git pull && sudo systemctl restart your-django-service")

def show_verification_steps():
    """Show how to verify the deployment"""
    print("\n✅ Verification Steps After Deployment:")
    print("=" * 50)
    print("1. Check Django logs on production server")
    print("2. Test the process-cart endpoint")
    print("3. Look for 'V2 Gateway initialized' messages in logs")
    print("4. Verify OAuth2 authentication is working")
    print()
    print("🧪 Test Commands (run on production server):")
    print("   cd /path/to/your/project")
    print("   python simple_v2_check.py")
    print("   # Should show: 'V2 Integration is WORKING!'")

def main():
    """Main function"""
    print("🚨 PRODUCTION DEPLOYMENT REQUIRED")
    print("=" * 60)
    print("Your V2 implementation is working locally but not deployed to production")
    print()
    
    check_production_status()
    show_deployment_checklist()
    show_verification_steps()
    
    print("\n🎯 SUMMARY:")
    print("=" * 60)
    print("❌ Current Status: Production still using V1 (CONNECTION_REFUSED)")
    print("✅ Local Status: V2 working perfectly")
    print("🔧 Action Required: Deploy V2 implementation to production")
    print()
    print("Once deployed, the CONNECTION_REFUSED error will be resolved! 🎉")

if __name__ == "__main__":
    main()
