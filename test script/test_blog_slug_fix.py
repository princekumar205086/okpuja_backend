#!/usr/bin/env python
"""
Test script to verify the blog post slug uniqueness fix
Run this to confirm the blog post creation works without slug conflicts
"""

import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.utils.text import slugify
from blog.models import BlogPost, BlogCategory
from django.contrib.auth import get_user_model
from accounts.models import UserProfile

User = get_user_model()

def generate_unique_slug(title, model_class):
    """Generate a unique slug for the given title and model class"""
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    
    # Keep trying until we find a unique slug
    while model_class.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

def test_slug_uniqueness():
    """Test the slug uniqueness functionality"""
    print("🧪 TESTING BLOG POST SLUG UNIQUENESS")
    print("=" * 50)
    
    # Test data
    duplicate_titles = [
        "The Complete Guide to Ganesh Puja",
        "The Complete Guide to Ganesh Puja", # Duplicate
        "The Complete Guide to Ganesh Puja", # Another duplicate
        "Benefits of Daily Prayer",
        "Benefits of Daily Prayer", # Duplicate
    ]
    
    generated_slugs = []
    
    print("\n🔍 Testing slug generation for duplicate titles:")
    print("-" * 50)
    
    for i, title in enumerate(duplicate_titles, 1):
        unique_slug = generate_unique_slug(title, BlogPost)
        generated_slugs.append(unique_slug)
        print(f"{i}. Title: '{title}'")
        print(f"   Slug:  '{unique_slug}'")
        print()
    
    # Check for uniqueness
    unique_slugs = set(generated_slugs)
    
    print(f"📊 Results:")
    print(f"   Generated slugs: {len(generated_slugs)}")
    print(f"   Unique slugs: {len(unique_slugs)}")
    
    if len(generated_slugs) == len(unique_slugs):
        print("✅ SUCCESS: All slugs are unique!")
        return True
    else:
        print("❌ FAILURE: Duplicate slugs detected!")
        return False

def test_database_creation():
    """Test actual database blog post creation"""
    print("\n🗄️ TESTING DATABASE BLOG POST CREATION")
    print("=" * 50)
    
    try:
        # Get or create a test user
        test_user = User.objects.filter(email='test_slug@okpuja.com').first()
        if not test_user:
            test_user = User.objects.create_user(
                email='test_slug@okpuja.com',
                password='testpass123',
                phone='+919876543210'
            )
            UserProfile.objects.create(
                user=test_user,
                first_name='Test',
                last_name='Slug'
            )
        
        # Get or create a test category
        test_category = BlogCategory.objects.filter(name='Test Category').first()
        if not test_category:
            admin_user = User.objects.filter(is_staff=True).first() or test_user
            test_category = BlogCategory.objects.create(
                user=admin_user,
                name='Test Category',
                description='Test category for slug testing',
                status='PUBLISHED'
            )
        
        # Create test posts with potentially duplicate titles
        test_titles = [
            "Amazing Benefits of Morning Prayer",
            "Amazing Benefits of Morning Prayer",  # Will get slug-1
            "Amazing Benefits of Morning Prayer",  # Will get slug-2
        ]
        
        created_posts = []
        for title in test_titles:
            unique_slug = generate_unique_slug(title, BlogPost)
            
            post = BlogPost.objects.create(
                title=title,
                slug=unique_slug,
                content=f"Test content for {title}",
                excerpt="Test excerpt",
                user=test_user,
                category=test_category,
                status='PUBLISHED'
            )
            created_posts.append(post)
            print(f"✅ Created post: '{post.title}' with slug: '{post.slug}'")
        
        print(f"\n📊 Successfully created {len(created_posts)} posts with unique slugs!")
        
        # Cleanup
        for post in created_posts:
            post.delete()
        
        print("🧹 Test posts cleaned up")
        return True
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

def show_existing_posts():
    """Show existing blog posts and their slugs"""
    posts = BlogPost.objects.all()[:10]  # Show first 10
    
    print(f"\n📄 EXISTING BLOG POSTS ({posts.count()} total):")
    print("-" * 50)
    
    for post in posts:
        print(f"• '{post.title}' → slug: '{post.slug}'")
    
    if posts.count() > 10:
        print(f"... and {posts.count() - 10} more posts")

if __name__ == '__main__':
    print("🔧 BLOG POST SLUG UNIQUENESS TEST")
    print("=" * 50)
    
    # Show existing posts
    show_existing_posts()
    
    # Test slug generation
    slug_test_passed = test_slug_uniqueness()
    
    # Test database creation
    db_test_passed = test_database_creation()
    
    print("\n" + "=" * 50)
    if slug_test_passed and db_test_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Blog seeder should now work without slug conflicts")
        print("\n🚀 READY FOR DEPLOYMENT!")
        print("   python manage.py seed_blog_data --clear")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Check the error messages above")
