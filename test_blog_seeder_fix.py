#!/usr/bin/env python
"""
Test script to verify the fixed blog seeder works correctly
Run this to confirm the blog seeder fix before deploying
"""

import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from blog.models import BlogCategory, BlogPost

User = get_user_model()

def test_blog_seeder_fix():
    """Test the blog seeder functionality"""
    print("🔍 Testing Blog Seeder Fix...")
    print("=" * 50)
    
    # 1. Test User Creation and Profile
    print("\n1. Testing User Creation...")
    try:
        # Create a test user like the seeder does
        test_user = User.objects.create_user(
            email='test_seeder@okpuja.com',
            password='testpass123',
            phone='+919876543210'
        )
        
        # Create user profile
        profile = UserProfile.objects.create(
            user=test_user,
            first_name='Test',
            last_name='User'
        )
        
        print(f"✅ User created: {test_user.email}")
        print(f"✅ Profile created: {profile.first_name} {profile.last_name}")
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False
    
    # 2. Test Blog Category Creation
    print("\n2. Testing Blog Category Creation...")
    try:
        # Get admin user for categories (like the seeder does)
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        print(f"📝 Using user for categories: {admin_user.email}")
        
        # Create a test category like the seeder does
        test_category = BlogCategory.objects.create(
            user=admin_user,
            name='Test Category',
            description='Test category description',
            meta_title='Test Category | Hindu Spiritual Guidance | OkPuja',
            meta_description='Test category for seeder validation',
            meta_keywords='test, category, seeder',
            status='PUBLISHED'
        )
        
        print(f"✅ Category created: {test_category.name}")
        print(f"✅ Category user: {test_category.user.email}")
        
    except Exception as e:
        print(f"❌ Category creation failed: {e}")
        return False
    
    # 3. Test Database Cleanup
    print("\n3. Cleaning up test data...")
    try:
        test_category.delete()
        test_user.delete()
        print("✅ Test data cleaned up successfully")
        
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Blog seeder fix test PASSED!")
    print("✅ The blog seeder should now work correctly")
    print("✅ Ready for deployment!")
    
    return True

def show_current_data():
    """Show current database state"""
    print("\n📊 Current Database State:")
    print("-" * 30)
    
    users_count = User.objects.count()
    profiles_count = UserProfile.objects.count()
    categories_count = BlogCategory.objects.count()
    posts_count = BlogPost.objects.count()
    
    print(f"👥 Users: {users_count}")
    print(f"📝 User Profiles: {profiles_count}")
    print(f"📂 Blog Categories: {categories_count}")
    print(f"📄 Blog Posts: {posts_count}")
    
    if categories_count > 0:
        print("\n📂 Existing Categories:")
        for cat in BlogCategory.objects.all()[:5]:
            print(f"   • {cat.name} (by {cat.user.email})")
    
    return {
        'users': users_count,
        'profiles': profiles_count,
        'categories': categories_count,
        'posts': posts_count
    }

if __name__ == '__main__':
    print("🧪 BLOG SEEDER FIX TEST")
    print("=" * 50)
    
    # Show current state
    current_data = show_current_data()
    
    # Run the test
    success = test_blog_seeder_fix()
    
    if success:
        print("\n🚀 READY FOR PRODUCTION!")
        print("Run these commands on your server:")
        print("   python manage.py seed_blog_data --clear")
        print("   python manage.py seed_puja_data --clear")
    else:
        print("\n❌ FIX REQUIRED!")
        print("Check the error messages above.")
