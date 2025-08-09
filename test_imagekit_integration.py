#!/usr/bin/env python3

"""
Complete Event Creation Test with ImageKit.io Integration
Tests multipart form data and ImageKit.io server upload
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
        # Create a colorful test image
        img = Image.new('RGB', (800, 600), color=(50, 150, 200))
        
        # Add some visual elements
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        # Draw some shapes
        draw.rectangle([50, 50, 750, 550], outline=(255, 255, 255), width=3)
        draw.ellipse([200, 200, 600, 400], fill=(255, 215, 0), outline=(255, 255, 255), width=2)
        
        # Add text
        try:
            draw.text((250, 280), "ImageKit Test Event", fill=(0, 0, 0))
        except:
            pass
        
        img.save(f.name, 'JPEG', quality=95)
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

def create_event_with_imagekit(token):
    """Create event that will upload to ImageKit.io"""
    print("\n📝 Creating event with ImageKit.io integration...")
    
    # Create test image
    test_image_path = create_test_image()
    
    try:
        # Prepare multipart form data
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        data = {
            'title': 'ImageKit Integration Test Event',
            'description': 'Testing ImageKit.io server upload with multipart form data. This event should have images uploaded to ImageKit.io server instead of local storage.',
            'event_date': '2025-10-01',
            'start_time': '14:00:00',
            'end_time': '16:00:00',
            'location': 'ImageKit Testing Center, Delhi',
            'registration_link': 'https://imagekit.io/register',
            'status': 'PUBLISHED',
            'is_featured': True
        }
        
        files = {
            'original_image': ('imagekit_test.jpg', open(test_image_path, 'rb'), 'image/jpeg')
        }
        
        print(f"📤 Sending multipart/form-data request to ImageKit integration...")
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
            
            # Verify ImageKit.io URLs
            print(f"\n🌐 ImageKit.io Processing Results:")
            original_url = event_data.get('original_image_url')
            thumbnail_url = event_data.get('thumbnail_url')
            banner_url = event_data.get('banner_url')
            
            print(f"   Original Image: {original_url}")
            print(f"   Thumbnail (400x300): {thumbnail_url}")
            print(f"   Banner (1200x600): {banner_url}")
            
            # Check if URLs are from ImageKit.io
            imagekit_domains = ['ik.imagekit.io', 'imagekit.io']
            
            def is_imagekit_url(url):
                if not url:
                    return False
                return any(domain in url for domain in imagekit_domains)
            
            print(f"\n✅ ImageKit.io Server Verification:")
            for name, url in [('Original', original_url), ('Thumbnail', thumbnail_url), ('Banner', banner_url)]:
                if url:
                    if is_imagekit_url(url):
                        print(f"   ✅ {name}: ImageKit.io Server ✓")
                        # Test accessibility
                        try:
                            img_response = requests.head(url, timeout=10)
                            if img_response.status_code == 200:
                                print(f"       └─ Accessible: {url[:60]}...")
                            else:
                                print(f"       └─ ❌ Not accessible - Status {img_response.status_code}")
                        except Exception as e:
                            print(f"       └─ ❌ Error accessing - {str(e)}")
                    else:
                        print(f"   ❌ {name}: Local Server (not ImageKit.io)")
                        print(f"       └─ URL: {url}")
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

def test_swagger_multipart():
    """Test if Swagger shows proper multipart form fields"""
    print(f"\n📋 Testing Swagger multipart form documentation...")
    
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
                
                # Check for multipart/form-data
                if 'multipart/form-data' in consumes:
                    print(f"   ✅ Multipart/form-data support confirmed")
                else:
                    print(f"   ❌ Multipart/form-data not found")
                
                # Check for image parameter
                image_param = next((p for p in parameters if p.get('name') == 'original_image'), None)
                if image_param and image_param.get('type') == 'file':
                    required = image_param.get('required', False)
                    print(f"   ✅ Image field found: type=file, required={required}")
                else:
                    print(f"   ❌ Image field not properly configured")
                    
                # Count form parameters
                form_params = [p for p in parameters if p.get('in') == 'form']
                print(f"   ✅ Form parameters count: {len(form_params)}")
                
            else:
                print(f"   ❌ Event creation endpoint not found in schema")
        else:
            print(f"   ❌ Swagger schema not accessible: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing Swagger: {str(e)}")

def main():
    """Main test function"""
    print("🚀 ImageKit.io Integration Test")
    print("="*60)
    print("Testing: Event CRUD with ImageKit.io server upload")
    print("Expected: Images uploaded to ImageKit.io (not local storage)")
    print("="*60)
    
    # Get authentication token
    token = get_admin_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    # Test Swagger documentation
    test_swagger_multipart()
    
    # Create event with ImageKit upload
    event = create_event_with_imagekit(token)
    
    print("\n" + "="*60)
    if event:
        original_url = event.get('original_image_url', '')
        thumbnail_url = event.get('thumbnail_url', '')
        banner_url = event.get('banner_url', '')
        
        # Check if any ImageKit URLs were generated
        imagekit_urls = [url for url in [original_url, thumbnail_url, banner_url] 
                        if url and ('ik.imagekit.io' in url or 'imagekit.io' in url)]
        
        if imagekit_urls:
            print("🎉 IMAGEKIT.IO INTEGRATION SUCCESS!")
            print(f"✅ Event created with ImageKit.io server upload")
            print(f"✅ {len(imagekit_urls)} images uploaded to ImageKit.io")
            print(f"✅ Multipart/form-data working correctly")
        else:
            print("⚠️  EVENT CREATED BUT IMAGEKIT INTEGRATION ISSUE")
            print("❌ Images uploaded to local server (not ImageKit.io)")
            print("💡 Check ImageKit.io credentials and configuration")
    else:
        print("❌ TEST FAILED!")
        print("❌ Event creation failed")
    
    print("\n💡 Next Steps:")
    print("   - Check Swagger UI: http://127.0.0.1:8000/api/docs/")
    print("   - Look for multipart form fields with image upload")
    print("   - Verify images are uploaded to ImageKit.io server")

if __name__ == "__main__":
    main()
