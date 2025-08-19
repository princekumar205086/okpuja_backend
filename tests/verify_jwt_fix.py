#!/usr/bin/env python
"""
Quick verification of JWT settings fix
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def verify_jwt_fix():
    """Verify that JWT settings have been fixed"""
    print("🔍 VERIFYING JWT CONFIGURATION FIX")
    print("=" * 50)
    
    jwt_settings = settings.SIMPLE_JWT
    
    print("Current JWT Settings:")
    for key, value in jwt_settings.items():
        print(f"  {key}: {value}")
    
    print(f"\n🎯 VERIFICATION RESULTS:")
    
    # Check access token lifetime
    access_lifetime = jwt_settings.get('ACCESS_TOKEN_LIFETIME')
    if access_lifetime and access_lifetime.total_seconds() >= 7200:  # 2 hours
        print("✅ ACCESS_TOKEN_LIFETIME: Fixed (≥2 hours)")
    else:
        print("❌ ACCESS_TOKEN_LIFETIME: Not fixed (should be ≥2 hours)")
    
    # Check blacklist setting
    blacklist_after = jwt_settings.get('BLACKLIST_AFTER_ROTATION', True)
    if blacklist_after == False:
        print("✅ BLACKLIST_AFTER_ROTATION: Fixed (disabled)")
    else:
        print("❌ BLACKLIST_AFTER_ROTATION: Not fixed (should be False)")
    
    # Check update last login
    update_login = jwt_settings.get('UPDATE_LAST_LOGIN', False)
    if update_login == True:
        print("✅ UPDATE_LAST_LOGIN: Fixed (enabled)")
    else:
        print("⚠️  UPDATE_LAST_LOGIN: Not set (should be True)")
    
    # Overall status
    fixes_applied = (
        access_lifetime and access_lifetime.total_seconds() >= 7200 and
        blacklist_after == False
    )
    
    if fixes_applied:
        print(f"\n🎉 JWT CONFIGURATION FIX: APPLIED ✅")
        print("The logout issue should be resolved!")
    else:
        print(f"\n❌ JWT CONFIGURATION FIX: NOT FULLY APPLIED")
        print("The logout issue may still exist!")
    
    return fixes_applied

if __name__ == "__main__":
    verify_jwt_fix()
