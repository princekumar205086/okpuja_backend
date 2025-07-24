#!/usr/bin/env python
"""
Test specific to the seeder fix - validates BlogComment parent field
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

try:
    import django
    django.setup()
    
    # Import the models
    from blog.models import BlogComment
    
    print("🔍 Checking BlogComment model fields...")
    
    # Get all field names
    field_names = [field.name for field in BlogComment._meta.get_fields()]
    print(f"📋 All BlogComment fields: {field_names}")
    
    # Check specific fields
    if 'parent' in field_names:
        print("✅ GOOD: 'parent' field exists")
        
        # Get the parent field
        parent_field = BlogComment._meta.get_field('parent')
        print(f"📝 Parent field type: {type(parent_field).__name__}")
        print(f"📝 Parent field related model: {parent_field.related_model}")
        print(f"📝 Parent field related name: {parent_field.related_query_name()}")
        
    else:
        print("❌ ERROR: 'parent' field not found!")
    
    if 'parent_comment' in field_names:
        print("❌ ERROR: 'parent_comment' field found (this should not exist)")
    else:
        print("✅ GOOD: 'parent_comment' field does not exist")
    
    print("\n🧪 Testing field lookup syntax...")
    
    # Test the field lookup that was causing the error
    try:
        # This should work
        test_query = BlogComment.objects.filter(parent__isnull=True)
        print("✅ GOOD: BlogComment.objects.filter(parent__isnull=True) works")
    except Exception as e:
        print(f"❌ ERROR with parent field: {e}")
    
    try:
        # This should fail
        test_query = BlogComment.objects.filter(parent_comment__isnull=True)
        print("❌ ERROR: parent_comment field should not work!")
    except Exception as e:
        print(f"✅ GOOD: parent_comment field correctly fails: {e}")
    
    print("\n🎯 Fix validation completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
