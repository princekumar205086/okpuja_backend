#!/usr/bin/env python
"""
Minimal test for BlogComment creation
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from blog.models import BlogPost, BlogComment, BlogCategory
from django.utils import timezone

User = get_user_model()

try:
    print("🔍 Testing BlogComment creation with parent field...")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'password': 'test123',
            'phone': '+919876543210'
        }
    )
    print(f"✅ User: {user.email}")
    
    # Get or create a test category
    category, created = BlogCategory.objects.get_or_create(
        name='Test Category',
        defaults={
            'user': user,
            'description': 'Test category for blog comment test',
            'status': 'PUBLISHED'
        }
    )
    print(f"✅ Category: {category.name}")
    
    # Get or create a test post
    post, created = BlogPost.objects.get_or_create(
        title='Test Post for Comments',
        defaults={
            'user': user,
            'category': category,
            'content': 'Test content for blog post',
            'excerpt': 'Test excerpt',
            'status': 'PUBLISHED',
            'published_at': timezone.now()
        }
    )
    print(f"✅ Post: {post.title}")
    
    # Create a parent comment
    parent_comment = BlogComment.objects.create(
        post=post,
        user=user,
        content="This is a parent comment for testing",
        is_approved=True
    )
    print(f"✅ Parent comment created: {parent_comment.id}")
    
    # Create a reply comment with parent field
    reply_comment = BlogComment.objects.create(
        post=post,
        user=user,
        parent=parent_comment,  # This should work now
        content="This is a reply comment for testing",
        is_approved=True,
        created_at=parent_comment.created_at + timedelta(hours=1)
    )
    print(f"✅ Reply comment created: {reply_comment.id}")
    print(f"✅ Reply parent: {reply_comment.parent.id}")
    
    print("\n🎉 All tests passed! The fix is working correctly.")
    
    # Cleanup (optional)
    reply_comment.delete()
    parent_comment.delete()
    print("🧹 Test data cleaned up")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
