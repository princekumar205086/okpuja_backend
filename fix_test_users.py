#!/usr/bin/env python3
"""
Fix Employee Test Users Script
"""
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
import django
django.setup()

from accounts.models import User, UserProfile

def fix_test_users():
    """Fix test users for proper testing"""
    print("🔧 Fixing test users...")
    
    # Get existing users
    try:
        admin_user = User.objects.get(email='admin@test.com')
        print(f"   Found admin user: {admin_user.email}")
        
        # Make sure admin is verified and active
        admin_user.email_verified = True
        admin_user.otp_verified = True
        admin_user.is_active = True
        admin_user.account_status = User.AccountStatus.ACTIVE
        admin_user.save()
        print("   ✅ Admin user fixed")
        
    except User.DoesNotExist:
        print("   ❌ Admin user not found")
    
    try:
        employee_user = User.objects.get(email='employee@test.com')
        print(f"   Found employee user: {employee_user.email}")
        
        # Make sure employee is verified and active
        employee_user.email_verified = True
        employee_user.otp_verified = True
        employee_user.is_active = True
        employee_user.account_status = User.AccountStatus.ACTIVE
        employee_user.save()
        print("   ✅ Employee user fixed")
        
    except User.DoesNotExist:
        print("   ❌ Employee user not found")
    
    try:
        regular_user = User.objects.get(email='user@test.com')
        print(f"   Found regular user: {regular_user.email}")
        
        # Make sure user is verified and active
        regular_user.email_verified = True
        regular_user.otp_verified = True
        regular_user.is_active = True
        regular_user.account_status = User.AccountStatus.ACTIVE
        regular_user.save()
        print("   ✅ Regular user fixed")
        
    except User.DoesNotExist:
        print("   ❌ Regular user not found")
    
    print("\n📊 User Status Summary:")
    for user in User.objects.filter(email__endswith='test.com'):
        print(f"   {user.email}: {user.role} - Active: {user.is_active} - Verified: {user.otp_verified}")

def create_missing_users():
    """Create missing test users"""
    print("\n👤 Creating missing test users...")
    
    # Create admin if not exists
    admin_user, created = User.objects.get_or_create(
        email='admin@test.com',
        defaults={
            'username': 'admin',
            'role': User.Role.ADMIN,
            'account_status': User.AccountStatus.ACTIVE,
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
            'email_verified': True,
            'otp_verified': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("   ✅ Admin user created")
    
    # Create employee if not exists
    employee_user, created = User.objects.get_or_create(
        email='employee@test.com',
        defaults={
            'username': 'employee',
            'phone': '9876543210',
            'role': User.Role.EMPLOYEE,
            'account_status': User.AccountStatus.ACTIVE,
            'is_active': True,
            'email_verified': True,
            'otp_verified': True
        }
    )
    if created:
        employee_user.set_password('emp123')
        employee_user.save()
        print("   ✅ Employee user created")
    
    # Create regular user if not exists
    regular_user, created = User.objects.get_or_create(
        email='user@test.com',
        defaults={
            'username': 'user',
            'phone': '8765432109',
            'role': User.Role.USER,
            'account_status': User.AccountStatus.ACTIVE,
            'is_active': True,
            'email_verified': True,
            'otp_verified': True
        }
    )
    if created:
        regular_user.set_password('user123')
        regular_user.save()
        print("   ✅ Regular user created")
    
    # Create profiles
    for user in [admin_user, employee_user, regular_user]:
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': f'Test {user.role.title()}',
                'last_name': 'User'
            }
        )
        if created:
            print(f"   ✅ Profile created for {user.email}")

if __name__ == "__main__":
    create_missing_users()
    fix_test_users()
    print("\n🎉 Test users setup complete!")