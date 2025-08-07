#!/usr/bin/env python
import os
import sys
import django

# Add Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
django.setup()

from accounts.models import User, UserProfile

def create_admin_user():
    """Create or update admin user with correct credentials"""
    print("🔧 Creating/updating admin user...")
    
    # Try to get existing admin
    admin_user = User.objects.filter(email='admin@okpuja.com').first()
    
    if admin_user:
        print(f"✅ Admin user found - Role: {admin_user.role}, Status: {admin_user.account_status}")
        # Update password
        admin_user.set_password('admin@123')
        admin_user.role = 'ADMIN'
        admin_user.account_status = 'ACTIVE'
        admin_user.save()
        print("🔧 Admin password and details updated")
    else:
        # Create new admin user
        admin_user = User.objects.create(
            email='admin@okpuja.com',
            role='ADMIN',
            account_status='ACTIVE',
            phone='+919999999999'
        )
        admin_user.set_password('admin@123')
        admin_user.save()
        
        # Create profile
        UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'first_name': 'Admin',
                'last_name': 'User'
            }
        )
        print("✅ New admin user created")
    
    # Test login
    from django.contrib.auth import authenticate
    user = authenticate(email='admin@okpuja.com', password='admin@123')
    if user:
        print("✅ Admin authentication test successful")
    else:
        print("❌ Admin authentication test failed")
    
    return admin_user

if __name__ == '__main__':
    create_admin_user()
