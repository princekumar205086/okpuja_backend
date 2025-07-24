#!/usr/bin/env python
"""
Quick test script to verify BlogComment model fields
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

# Test imports and field names
try:
    from blog.models import BlogComment
    print("✅ BlogComment model imported successfully")
    
    # Get field names
    field_names = [f.name for f in BlogComment._meta.fields]
    print(f"📋 BlogComment fields: {field_names}")
    
    # Check if 'parent' field exists
    if 'parent' in field_names:
        print("✅ 'parent' field found in BlogComment model")
    else:
        print("❌ 'parent' field NOT found in BlogComment model")
    
    # Check if 'parent_comment' field exists (it shouldn't)
    if 'parent_comment' in field_names:
        print("❌ 'parent_comment' field found (this is the problem!)")
    else:
        print("✅ 'parent_comment' field not found (good)")
        
    print("\n🎯 Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
