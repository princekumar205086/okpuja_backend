#!/usr/bin/env python
"""
Test script for both puja and astrology admin functionality
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from puja.models import PujaService
from puja.admin import PujaServiceAdmin
from astrology.models import AstrologyService
from astrology.admin import AstrologyServiceAdmin

def test_all_admin_functionality():
    print("Testing all admin functionality...")
    
    # Test Puja Admin
    print("\n=== PUJA SERVICE ADMIN ===")
    puja_admin = PujaServiceAdmin(PujaService, None)
    
    print("1. Testing image preview method:")
    puja_services = PujaService.objects.all()[:3]
    
    for service in puja_services:
        try:
            preview = puja_admin.image_preview(service)
            print(f"   Puja Service '{service.title}': Image preview generated ✓")
        except Exception as e:
            print(f"   Puja Service '{service.title}': Error - {e}")
    
    print("2. Testing list_display fields:")
    try:
        for field in puja_admin.list_display:
            if hasattr(puja_admin, field):
                print(f"   Admin method '{field}': Available ✓")
            elif hasattr(PujaService, field):
                print(f"   Model field '{field}': Available ✓")
            else:
                print(f"   Field '{field}': NOT FOUND ❌")
    except Exception as e:
        print(f"   Error checking list_display: {e}")
    
    # Test Astrology Admin
    print("\n=== ASTROLOGY SERVICE ADMIN ===")
    astrology_admin = AstrologyServiceAdmin(AstrologyService, None)
    
    print("1. Testing image preview method:")
    astrology_services = AstrologyService.objects.all()[:3]
    
    for service in astrology_services:
        try:
            preview = astrology_admin.image_preview(service)
            print(f"   Astrology Service '{service.title}': Image preview generated ✓")
        except Exception as e:
            print(f"   Astrology Service '{service.title}': Error - {e}")
    
    print("2. Testing list_display fields:")
    try:
        for field in astrology_admin.list_display:
            if hasattr(astrology_admin, field):
                print(f"   Admin method '{field}': Available ✓")
            elif hasattr(AstrologyService, field):
                print(f"   Model field '{field}': Available ✓")
            else:
                print(f"   Field '{field}': NOT FOUND ❌")
    except Exception as e:
        print(f"   Error checking list_display: {e}")
    
    print("\n=== COMPARISON ===")
    print(f"Puja Services: {PujaService.objects.count()}")
    print(f"Astrology Services: {AstrologyService.objects.count()}")
    
    # Test with services that have images
    puja_with_images = PujaService.objects.exclude(image='').exclude(image__isnull=True).count()
    astrology_with_images = AstrologyService.objects.exclude(image_url='').exclude(image_url__isnull=True).count()
    
    print(f"Puja Services with images: {puja_with_images}")
    print(f"Astrology Services with images: {astrology_with_images}")
    
    print("\nAll admin functionality tests completed!")

if __name__ == "__main__":
    test_all_admin_functionality()
