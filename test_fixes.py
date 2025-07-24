"""
Test script to verify the fixes for User model issues
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile

User = get_user_model()

def test_user_creation():
    """Test creating users with profiles"""
    print("🧪 Testing User Creation...")
    
    try:
        # Create user
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone='+919876543210'
        )
        print(f"✅ Created user: {user.email}")
        
        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            first_name='Test',
            last_name='User'
        )
        print(f"✅ Created profile: {profile.first_name} {profile.last_name}")
        
        # Test accessing profile
        print(f"✅ User profile access: {user.profile.first_name} {user.profile.last_name}")
        
        # Clean up
        user.delete()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_puja_models():
    """Test puja models import"""
    print("\n🕉️ Testing Puja Models...")
    
    try:
        from puja.models import PujaCategory, PujaService, Package, PujaBooking
        print("✅ Puja models imported successfully")
        
        # Test basic queries
        categories = PujaCategory.objects.all()
        services = PujaService.objects.all()
        packages = Package.objects.all()
        bookings = PujaBooking.objects.all()
        
        print(f"✅ Database queries work:")
        print(f"   • Categories: {categories.count()}")
        print(f"   • Services: {services.count()}")
        print(f"   • Packages: {packages.count()}")
        print(f"   • Bookings: {bookings.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Puja models test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running Fix Verification Tests")
    print("=" * 40)
    
    success = True
    
    if not test_user_creation():
        success = False
    
    if not test_puja_models():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! Fixes are working correctly!")
        print("✅ You can now run the data seeders successfully")
    else:
        print("❌ Some tests failed. Please check the issues above.")
    
    return success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
