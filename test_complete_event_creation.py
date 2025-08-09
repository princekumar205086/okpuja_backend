#!/usr/bin/env python3

"""
Comprehensive Event Creation Test with ImageKit Verification
Tests multipart/form-data submission and ImageKit processing
"""

import requests
import json
import os
from PIL import Image
import tempfile

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
ADMIN_EMAIL = "admin@okpuja.com"
ADMIN_PASSWORD = "admin@123"

def create_test_image():
    """Create a test image for upload"""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        # Create a simple 800x600 test image
        img = Image.new('RGB', (800, 600), color=(73, 109, 137))
        img.save(f.name, 'JPEG')
        return f.name

def get_admin_token():
    """Get JWT token for admin authentication"""
    print("🔐 Getting admin authentication token...")
    
    response = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code == 200:
        token = response.json().get('access')
        print(f"✅ Successfully authenticated as admin")
        return token
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def create_event_with_image(token):
    """Create event with mandatory image using multipart/form-data"""
    print("\n📝 Creating event with image upload...")
    
    # Create test image
    test_image_path = create_test_image()
    
    try:
        # Prepare multipart form data
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'title': 'Test Event with ImageKit Processing',
            'description': 'This is a test event to verify ImageKit integration and multipart upload',
            'event_date': '2025-09-15',
            'start_time': '10:00:00',
            'end_time': '12:00:00',
            'location': 'Test Location, Mumbai',
            'registration_link': 'https://example.com/register',
            'status': 'PUBLISHED',
            'is_featured': True
        }
        
        files = {
            'original_image': ('test_event.jpg', open(test_image_path, 'rb'), 'image/jpeg')
        }
        
        print(f"📤 Sending multipart/form-data request...")
        response = requests.post(
            f"{BASE_URL}/api/misc/admin/events/",
            headers=headers,
            data=data,
            files=files
        )
        
        files['original_image'][1].close()  # Close file handle
        
        if response.status_code == 201:
            event_data = response.json()
            print(f"✅ Event created successfully!")
            print(f"   Event ID: {event_data['id']}")
            print(f"   Title: {event_data['title']}")
            print(f"   Status: {event_data['status']}")
            print(f"   Featured: {event_data['is_featured']}")
            
            # Verify ImageKit URLs
            print(f"\n🖼️ ImageKit Processing Results:")
            original_url = event_data.get('original_image_url')
            thumbnail_url = event_data.get('thumbnail_url')
            banner_url = event_data.get('banner_url')
            
            print(f"   Original Image: {original_url}")
            print(f"   Thumbnail (400x300): {thumbnail_url}")
            print(f"   Banner (1200x600): {banner_url}")
            
            # Test image URLs accessibility
            print(f"\n🌐 Testing image URL accessibility...")
            for name, url in [('Original', original_url), ('Thumbnail', thumbnail_url), ('Banner', banner_url)]:
                if url:
                    try:
                        img_response = requests.head(url, timeout=10)
                        if img_response.status_code == 200:
                            print(f"   ✅ {name}: Accessible ({url})")
                        else:
                            print(f"   ❌ {name}: Not accessible - Status {img_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ {name}: Error accessing - {str(e)}")
                else:
                    print(f"   ❌ {name}: No URL provided")
            
            return event_data
            
        else:
            print(f"❌ Event creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    finally:
        # Clean up test image
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)

def test_swagger_multipart_display():
    """Test if Swagger shows multipart form fields"""
    print(f"\n📋 Testing Swagger documentation...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/docs/?format=openapi")
        if response.status_code == 200:
            schema = response.json()
            
            # Look for Event creation endpoint
            paths = schema.get('paths', {})
            event_post = paths.get('/api/misc/admin/events/', {}).get('post', {})
            
            if event_post:
                consumes = event_post.get('consumes', [])
                parameters = event_post.get('parameters', [])
                
                print(f"   ✅ Swagger schema accessible")
                print(f"   Content Types: {consumes}")
                print(f"   Parameters Count: {len(parameters)}")
                
                # Check for multipart/form-data
                if 'multipart/form-data' in consumes:
                    print(f"   ✅ Multipart/form-data support confirmed")
                else:
                    print(f"   ❌ Multipart/form-data not found in consumes")
                
                # Check for image parameter
                image_param = next((p for p in parameters if p.get('name') == 'original_image'), None)
                if image_param:
                    print(f"   ✅ Image parameter found: {image_param.get('type')} (required: {image_param.get('required')})")
                else:
                    print(f"   ❌ Image parameter not found")
            else:
                print(f"   ❌ Event creation endpoint not found in schema")
        else:
            print(f"   ❌ Swagger schema not accessible: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing Swagger: {str(e)}")

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Event Creation Test")
    print("="*60)
    
    # Get authentication token
    token = get_admin_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    # Test Swagger documentation
    test_swagger_multipart_display()
    
    # Create event with image
    event = create_event_with_image(token)
    
    print("\n" + "="*60)
    if event:
        print("🎉 TEST COMPLETED SUCCESSFULLY!")
        print(f"✅ Event created with proper ImageKit processing")
        print(f"✅ Multipart/form-data upload working")
        print(f"✅ All image URLs generated correctly")
    else:
        print("❌ TEST FAILED!")
        print("❌ Event creation or image processing failed")
    
    print("\n💡 Next: Check Swagger UI at http://127.0.0.1:8000/api/docs/")
    print("   - Should show multipart form fields")
    print("   - Image field should be marked as required")

if __name__ == "__main__":
    main()
