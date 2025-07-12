#!/usr/bin/env python
"""
Test script to verify image upload functionality in astrology app
"""
import os
import sys
import django
from io import BytesIO
from PIL import Image

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from astrology.models import AstrologyService

def create_test_image():
    """Create a simple test image"""
    # Create a simple RGB image
    img = Image.new('RGB', (400, 300), color='red')
    
    # Save to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes

def test_image_upload():
    """Test image upload functionality"""
    try:
        # Create a test service
        service = AstrologyService.objects.create(
            title="Test Service",
            service_type="HOROSCOPE",
            description="Test service for image upload",
            price=100.00,
            duration_minutes=30
        )
        
        print(f"Created test service: {service}")
        
        # Create test image
        test_image = create_test_image()
        
        # Mock file object
        class MockFile:
            def __init__(self, data, name):
                self.data = data
                self.name = name
                
            def read(self):
                return self.data.getvalue()
        
        mock_file = MockFile(test_image, 'test_image.jpg')
        
        # Test image upload
        result = service.save_service_image(mock_file)
        
        if result:
            print(f"✅ Image upload successful!")
            print(f"Image URL: {service.image_url}")
            print(f"Thumbnail URL: {service.image_thumbnail_url}")
            print(f"Card URL: {service.image_card_url}")
        else:
            print("❌ Image upload failed!")
            
        # Clean up
        service.delete()
        print("Test service deleted")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing image upload functionality...")
    test_image_upload()
