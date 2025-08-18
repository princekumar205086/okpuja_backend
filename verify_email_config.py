#!/usr/bin/env python
"""
Quick Settings Verification for Professional Email Notifications
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def verify_settings():
    """Verify all email settings are properly configured"""
    print("🔧 OKPUJA EMAIL SETTINGS VERIFICATION")
    print("=" * 50)
    
    # Check basic email settings
    print("📧 Basic Email Configuration:")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    
    # Check admin email
    print("\n👨‍💼 Admin Email Configuration:")
    if hasattr(settings, 'ADMIN_PERSONAL_EMAIL'):
        print(f"   ADMIN_PERSONAL_EMAIL: {settings.ADMIN_PERSONAL_EMAIL}")
        print("   ✅ Admin email properly configured")
    else:
        print("   ❌ ADMIN_PERSONAL_EMAIL not found in settings")
        print("   Please add ADMIN_PERSONAL_EMAIL=okpuja108@gmail.com to .env file")
    
    # Check if sender and admin are the same
    admin_email = getattr(settings, 'ADMIN_PERSONAL_EMAIL', '')
    if admin_email == settings.DEFAULT_FROM_EMAIL:
        print("   ✅ Admin and sender email match (recommended)")
    else:
        print("   ⚠️  Admin and sender email are different")
    
    # Check template paths
    print("\n📄 Template Configuration:")
    template_dirs = settings.TEMPLATES[0]['DIRS']
    print(f"   Template directories: {template_dirs}")
    
    # Check if our professional templates exist
    import os
    base_dir = settings.BASE_DIR
    templates_path = os.path.join(base_dir, 'templates', 'emails')
    
    professional_templates = [
        'otp_verification.html',
        'admin_booking_notification.html',
        'admin_astrology_notification.html'
    ]
    
    print("\n🎨 Professional Template Status:")
    for template in professional_templates:
        template_path = os.path.join(templates_path, template)
        if os.path.exists(template_path):
            print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template} - Missing!")
    
    # Check cache configuration
    print("\n🔄 Cache Configuration:")
    cache_backend = settings.CACHES['default']['BACKEND']
    print(f"   Cache backend: {cache_backend}")
    if 'dummy' in cache_backend.lower():
        print("   ⚠️  Dummy cache - duplicate prevention may not work")
    else:
        print("   ✅ Cache configured for duplicate prevention")
    
    print("\n" + "=" * 50)
    print("🎯 VERIFICATION COMPLETE")
    
    # Overall status
    has_admin_email = hasattr(settings, 'ADMIN_PERSONAL_EMAIL')
    templates_exist = all(
        os.path.exists(os.path.join(templates_path, t)) 
        for t in professional_templates
    )
    
    if has_admin_email and templates_exist:
        print("✅ ALL SYSTEMS READY - Professional emails configured!")
    else:
        print("⚠️  CONFIGURATION INCOMPLETE - Please fix issues above")

if __name__ == "__main__":
    verify_settings()
