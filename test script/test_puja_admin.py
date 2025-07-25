#!/usr/bin/env python
"""
Test script for puja service admin functionality
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from puja.models import PujaService, PujaCategory
from puja.admin import PujaServiceAdmin

def test_admin_functionality():
    print("Testing PujaService admin functionality...")
    
    # Test 1: Check if admin can handle services with images
    print("\n1. Testing image preview method:")
    admin_instance = PujaServiceAdmin(PujaService, None)
    
    # Test with a service that has an image
    services_with_images = PujaService.objects.exclude(image='').exclude(image__isnull=True)[:3]
    
    for service in services_with_images:
        try:
            preview = admin_instance.image_preview(service)
            print(f"   Service '{service.title}': Image preview generated ✓")
        except Exception as e:
            print(f"   Service '{service.title}': Error - {e}")
    
    # Test with a service without image
    service_without_image = PujaService.objects.filter(image='').first()
    if service_without_image:
        try:
            preview = admin_instance.image_preview(service_without_image)
            print(f"   Service without image: {preview} ✓")
        except Exception as e:
            print(f"   Service without image: Error - {e}")
    
    # Test 2: Check list_display fields
    print("\n2. Testing list_display fields:")
    try:
        for field in admin_instance.list_display:
            if hasattr(admin_instance, field):
                print(f"   Admin method '{field}': Available ✓")
            elif hasattr(PujaService, field):
                print(f"   Model field '{field}': Available ✓")
            else:
                print(f"   Field '{field}': NOT FOUND ❌")
    except Exception as e:
        print(f"   Error checking list_display: {e}")
    
    # Test 3: Check readonly_fields
    print("\n3. Testing readonly_fields:")
    try:
        for field in admin_instance.readonly_fields:
            if hasattr(admin_instance, field):
                print(f"   Admin method '{field}': Available ✓")
            elif hasattr(PujaService, field):
                print(f"   Model field '{field}': Available ✓")
            else:
                print(f"   Field '{field}': NOT FOUND ❌")
    except Exception as e:
        print(f"   Error checking readonly_fields: {e}")
    
    print("\nAdmin functionality test completed!")

if __name__ == "__main__":
    test_admin_functionality()
