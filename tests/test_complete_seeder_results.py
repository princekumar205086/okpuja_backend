#!/usr/bin/env python3
import requests
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

# Configure Django
import django
django.setup()

from accounts.models import User

def test_complete_festival_api():
    """Test the complete festival seeder results and API functionality"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    print("🧪 Testing Complete Hindu Festival API Results")
    print("=" * 60)
    
    # Test 1: Login and get token
    print("\n🔑 Step 1: Admin Authentication")
    login_data = {
        "email": "admin@okpuja.com",
        "password": "admin@123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        if response.status_code == 200:
            token = response.json().get('access')
            print(f"✅ Admin login successful - Token obtained")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return
    
    # Test 2: Get all events (public endpoint)
    print("\n📋 Step 2: Fetch All Events (Public)")
    try:
        response = requests.get(f"{BASE_URL}/api/misc/events/")
        if response.status_code == 200:
            events = response.json()
            total_events = len(events)
            print(f"✅ Public API working - {total_events} events retrieved")
            
            if total_events >= 60:
                print(f"🎉 All 60+ Hindu festivals successfully seeded!")
            
            # Show first few festivals
            print("\n📅 Sample Festival Data:")
            for i, event in enumerate(events[:3]):
                print(f"   {i+1}. {event['title']} ({event['slug']})")
                print(f"      📅 Date: {event['event_date']}")
                print(f"      📝 Status: {'Featured' if event['is_featured'] else 'Regular'}")
                if 'imagekit_original_url' in event and event['imagekit_original_url']:
                    print(f"      🖼️  ImageKit: ✅ Integrated")
                else:
                    print(f"      🖼️  ImageKit: ❌ Missing")
                print()
        else:
            print(f"❌ Public API failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Public API request failed: {e}")
        return
    
    # Test 3: Get admin events
    print("\n🛡️  Step 3: Admin Events Access")
    try:
        response = requests.get(f"{BASE_URL}/api/misc/admin/events/", headers=headers)
        if response.status_code == 200:
            admin_events = response.json()['results'] if 'results' in response.json() else response.json()
            admin_total = len(admin_events) if isinstance(admin_events, list) else response.json().get('count', 0)
            print(f"✅ Admin API working - {admin_total} events accessible to admin")
        else:
            print(f"❌ Admin API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin API request failed: {e}")
    
    # Test 4: Featured festivals
    print("\n⭐ Step 4: Featured Festivals Check")
    featured_count = sum(1 for event in events if event.get('is_featured', False))
    print(f"✅ Featured festivals: {featured_count}")
    
    if featured_count > 0:
        print("\n🌟 Featured Hindu Festivals:")
        featured_events = [e for e in events if e.get('is_featured', False)]
        for event in featured_events[:5]:  # Show first 5 featured
            print(f"   ⭐ {event['title']} - {event['event_date']}")
    
    # Test 5: ImageKit Integration Status
    print("\n🌐 Step 5: ImageKit Integration Verification")
    imagekit_count = sum(1 for event in events if event.get('imagekit_original_url'))
    print(f"✅ Events with ImageKit integration: {imagekit_count}/{total_events}")
    
    if imagekit_count > 0:
        print("\n🖼️  Sample ImageKit URLs:")
        for event in events[:2]:
            if event.get('imagekit_original_url'):
                print(f"   📸 {event['title']}:")
                print(f"      Original: {event['imagekit_original_url'][:60]}...")
                if event.get('imagekit_thumbnail_url'):
                    print(f"      Thumbnail: {event['imagekit_thumbnail_url'][:60]}...")
                if event.get('imagekit_banner_url'):
                    print(f"      Banner: {event['imagekit_banner_url'][:60]}...")
    
    # Test 6: CRUD Operations Test
    print("\n🔧 Step 6: CRUD Operations Test")
    
    # Create test event
    test_event_data = {
        "title": "Test Festival API",
        "slug": "test-festival-api",
        "description": "Testing CRUD API functionality",
        "event_date": "2025-12-31",
        "is_published": True,
        "is_featured": False
    }
    
    try:
        # CREATE
        response = requests.post(f"{BASE_URL}/api/misc/admin/events/", json=test_event_data, headers=headers)
        if response.status_code == 201:
            test_event = response.json()
            test_event_id = test_event['id']
            print(f"✅ CREATE: Test event created (ID: {test_event_id})")
            
            # READ
            response = requests.get(f"{BASE_URL}/api/misc/admin/events/{test_event_id}/", headers=headers)
            if response.status_code == 200:
                print(f"✅ READ: Test event retrieved successfully")
                
                # UPDATE
                update_data = {"title": "Updated Test Festival API"}
                response = requests.patch(f"{BASE_URL}/api/misc/admin/events/{test_event_id}/", json=update_data, headers=headers)
                if response.status_code == 200:
                    print(f"✅ UPDATE: Test event updated successfully")
                    
                    # DELETE
                    response = requests.delete(f"{BASE_URL}/api/misc/admin/events/{test_event_id}/", headers=headers)
                    if response.status_code == 204:
                        print(f"✅ DELETE: Test event deleted successfully")
                    else:
                        print(f"❌ DELETE failed: {response.status_code}")
                else:
                    print(f"❌ UPDATE failed: {response.status_code}")
            else:
                print(f"❌ READ failed: {response.status_code}")
        else:
            print(f"❌ CREATE failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎊 Hindu Festival API Testing Complete!")
    print("✨ Ready for frontend integration with complete festival dataset")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_festival_api()
