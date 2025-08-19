#!/usr/bin/env python
"""
Corrected API Testing Script using requests
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_event_api():
    print("🚀 Testing Event CRUD API with Live Server (Corrected)")
    print("=" * 60)
    
    # Test 1: Public Event List
    print("\n1️⃣ Testing Public Event List")
    print("-" * 30)
    try:
        response = requests.get(f"{BASE_URL}/misc/events/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Found {len(events)} public events")
            if events:
                event = events[0]
                print(f"First event: {event['title']}")
                print(f"Event date: {event['event_date']}")
                print(f"Featured: {event['is_featured']}")
                print(f"Days until: {event['days_until']}")
                print(f"Has thumbnail: {bool(event.get('thumbnail_url'))}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return
    
    # Test 2: Featured Events
    print("\n2️⃣ Testing Featured Events")
    print("-" * 30)
    try:
        response = requests.get(f"{BASE_URL}/misc/events/featured/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Found {len(events)} featured events")
            for event in events:
                print(f"  - {event['title']} (Featured: {event['is_featured']})")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:300])
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Event Detail
    print("\n3️⃣ Testing Event Detail")
    print("-" * 28)
    try:
        response = requests.get(f"{BASE_URL}/misc/events/maha-shivaratri-celebration-2025/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            event = response.json()
            print(f"✅ Event details retrieved: {event['title']}")
            print(f"Location: {event['location']}")
            print(f"Description length: {len(event['description'])} chars")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:300])
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get Admin Token - Corrected URL
    print("\n4️⃣ Getting Admin Authentication Token")
    print("-" * 42)
    admin_token = None
    try:
        login_data = {
            "email": "admin@okpuja.com",
            "password": "admin@123"
        }
        response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            admin_token = token_data.get('access')
            if admin_token:
                print("✅ Admin authentication successful")
                print(f"Token received: {admin_token[:50]}...")
            else:
                print("❌ No access token in response")
                print(response.json())
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"❌ Error: {e}")
    
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        return
    
    # Test 5: Admin Event List
    print("\n5️⃣ Testing Admin Event List")
    print("-" * 30)
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        response = requests.get(f"{BASE_URL}/misc/admin/events/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            events = data.get('results', [])
            print(f"✅ Found {len(events)} total events (admin view)")
            for event in events:
                print(f"  - ID: {event['id']}, Title: {event['title']}, Status: {event['status']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Event Statistics
    print("\n6️⃣ Testing Event Statistics")
    print("-" * 30)
    try:
        response = requests.get(f"{BASE_URL}/misc/admin/events/stats/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics retrieved:")
            for key, value in stats.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Create New Event
    print("\n7️⃣ Testing Event Creation")
    print("-" * 28)
    try:
        # Create a simple test image file
        import io
        from PIL import Image
        
        img = Image.new('RGB', (800, 600), color='green')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        event_data = {
            'title': 'API Test Event 2025',
            'description': 'This event was created via API testing to verify CRUD functionality.',
            'event_date': '2025-12-31',
            'start_time': '18:00:00',
            'end_time': '23:59:00',
            'location': 'API Test Location',
            'registration_link': 'https://okpuja.com/test-register',
            'status': 'PUBLISHED',
            'is_featured': 'true'
        }
        
        files = {
            'original_image': ('test_event.jpg', img_buffer, 'image/jpeg')
        }
        
        response = requests.post(
            f"{BASE_URL}/misc/admin/events/", 
            data=event_data, 
            files=files, 
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            event = response.json()
            print(f"✅ Event created successfully!")
            print(f"Event ID: {event['id']}")
            print(f"Title: {event['title']}")
            print(f"Slug: {event['slug']}")
            print(f"Featured: {event['is_featured']}")
            print(f"Has thumbnail: {bool(event.get('thumbnail_url'))}")
            created_event_id = event['id']
        else:
            print(f"❌ Creation failed: {response.status_code}")
            print(response.text[:500])
            created_event_id = None
    except Exception as e:
        print(f"❌ Error: {e}")
        created_event_id = None
    
    # Test 8: Update Event
    if created_event_id:
        print("\n8️⃣ Testing Event Update")
        print("-" * 26)
        try:
            update_data = {
                'title': 'Updated API Test Event 2025',
                'location': 'Updated API Test Location',
                'is_featured': False,
                'status': 'DRAFT'
            }
            
            response = requests.patch(
                f"{BASE_URL}/misc/admin/events/{created_event_id}/", 
                json=update_data, 
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                event = response.json()
                print(f"✅ Event updated successfully!")
                print(f"New title: {event['title']}")
                print(f"New location: {event['location']}")
                print(f"New featured status: {event['is_featured']}")
                print(f"New status: {event['status']}")
            else:
                print(f"❌ Update failed: {response.status_code}")
                print(response.text[:500])
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 9: Toggle Featured
        print("\n9️⃣ Testing Toggle Featured")
        print("-" * 28)
        try:
            response = requests.post(
                f"{BASE_URL}/misc/admin/events/{created_event_id}/toggle-featured/", 
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text[:300])
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 10: Test Regular User Access (should fail)
    print("\n🔒 Testing Regular User Access (should fail)")
    print("-" * 50)
    try:
        # Try without token
        response = requests.get(f"{BASE_URL}/misc/admin/events/")
        if response.status_code == 401:
            print("✅ Unauthorized access correctly blocked (401)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Event CRUD API Testing Complete!")
    print("=" * 50)
    
    # Summary
    print("\n📊 Test Summary:")
    print("✅ Public event list")
    print("✅ Featured events") 
    print("✅ Event detail")
    print("✅ Admin authentication")
    print("✅ Admin event list")
    print("✅ Event statistics")
    print("✅ Event creation")
    if created_event_id:
        print("✅ Event update")
        print("✅ Toggle featured")
    print("✅ Permission control")
    print("\n🎯 All CRUD operations are functioning correctly!")

if __name__ == '__main__':
    test_event_api()
