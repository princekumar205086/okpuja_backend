#!/usr/bin/env python
"""
Create test user if needed
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def ensure_test_user():
    """Ensure test user exists"""
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Check if test user exists
        test_email = 'asliprinceraj@gmail.com'
        user = User.objects.filter(email=test_email).first()
        
        if user:
            print(f"✅ Test user exists: {user.email}")
            print(f"   User ID: {user.id}")
            print(f"   Is active: {user.is_active}")
            return True
        else:
            print(f"❌ Test user '{test_email}' not found")
            print("   You need to create this user manually or via Django admin")
            print("   Alternatively, run: python manage.py createsuperuser")
            return False
            
    except Exception as e:
        print(f"❌ Error checking user: {e}")
        return False

def check_admin_user():
    """Check if admin user exists"""
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        admin_email = 'prince@gmail.com'
        admin = User.objects.filter(email=admin_email).first()
        
        if admin:
            print(f"✅ Admin user exists: {admin.email}")
            print(f"   Is superuser: {admin.is_superuser}")
            print(f"   Is staff: {admin.is_staff}")
        else:
            print(f"ℹ️  Admin user '{admin_email}' not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking admin: {e}")
        return False

if __name__ == "__main__":
    print("👤 Checking Users\n")
    
    admin_check = check_admin_user()
    user_check = ensure_test_user()
    
    print("\n" + "="*40)
    
    if user_check:
        print("✅ Ready to run tests!")
    else:
        print("❌ Need to create test user first!")
        print("\nTo create the test user:")
        print("1. Run: python manage.py shell")
        print("2. Execute:")
        print("   from django.contrib.auth import get_user_model")
        print("   User = get_user_model()")
        print("   User.objects.create_user('asliprinceraj@gmail.com', 'testpass123')")
        print("   exit()")
