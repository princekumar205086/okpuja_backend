#!/usr/bin/env python
"""
Test script for Event CRUD API
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

import requests
import json
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User
from misc.models import Event

def test_event_crud_api():
    """Test the Event CRUD API manually"""
    print("🚀 Testing Event CRUD API")
    print("=" * 50)
    
    # Initialize API client
    client = APIClient()
    
    # Test 1: Public Event List
    print("\n1️⃣ Testing Public Event List")
    print("-" * 30)
    try:
        response = client.get('/api/misc/events/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            events = response.json()
            print(f"Found {len(events)} public events")
            if events:
                print(f"First event: {events[0]['title']}")
                print(f"Image URLs present: {bool(events[0].get('thumbnail_url'))}")
        else:
            print(f"Error: {response.data}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Admin Authentication
    print("\n2️⃣ Testing Admin Authentication")
    print("-" * 35)
    try:
        # Get admin user
        admin_user = User.objects.get(email='admin@okpuja.com')
        print(f"Admin user found: {admin_user.email}")
        print(f"Admin role: {admin_user.role}")
        print(f"Admin active: {admin_user.account_status}")
        
        # Authenticate
        client.force_authenticate(user=admin_user)
        print("✅ Admin authentication successful")
    except User.DoesNotExist:
        print("❌ Admin user not found. Creating admin user...")
        try:
            admin_user = User.objects.create_user(
                email='admin@okpuja.com',
                password='admin@123',
                role=User.Role.ADMIN,
                account_status=User.AccountStatus.ACTIVE,
                email_verified=True
            )
            client.force_authenticate(user=admin_user)
            print("✅ Admin user created and authenticated")
        except Exception as e:
            print(f"❌ Error creating admin: {e}")
            return
    
    # Test 3: Admin Event List
    print("\n3️⃣ Testing Admin Event List")
    print("-" * 30)
    try:
        response = client.get('/api/misc/admin/events/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            events = data.get('results', [])
            print(f"Found {len(events)} total events (admin view)")
            if events:
                print(f"First event: {events[0]['title']}")
                print(f"Event status: {events[0]['status']}")
        else:
            print(f"Error: {response.data}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Create New Event
    print("\n4️⃣ Testing Event Creation")
    print("-" * 28)
    try:
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        from io import BytesIO
        
        # Create test image
        img = Image.new('RGB', (800, 600), color='blue')
        img_io = BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        test_image = SimpleUploadedFile(
            "test_event.jpg", 
            img_io.getvalue(), 
            content_type="image/jpeg"
        )
        
        event_data = {
            'title': 'API Test Event',
            'description': 'This event was created via API testing',
            'event_date': '2025-12-25',
            'start_time': '10:00:00',
            'end_time': '18:00:00',
            'location': 'Test Location',
            'registration_link': 'https://test.com/register',
            'status': 'PUBLISHED',
            'is_featured': True,
            'original_image': test_image
        }
        
        response = client.post('/api/misc/admin/events/', event_data, format='multipart')
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            event = response.json()
            print(f"✅ Event created: {event['title']}")
            print(f"Event ID: {event['id']}")
            print(f"Event Slug: {event['slug']}")
            print(f"Image URLs: {bool(event.get('thumbnail_url'))}")
            created_event_id = event['id']
        else:
            print(f"❌ Error: {response.data}")
            created_event_id = None
    except Exception as e:
        print(f"❌ Error: {e}")
        created_event_id = None
    
    # Test 5: Update Event
    if created_event_id:
        print("\n5️⃣ Testing Event Update")
        print("-" * 26)
        try:
            update_data = {
                'title': 'Updated API Test Event',
                'location': 'Updated Test Location',
                'is_featured': False
            }
            
            response = client.patch(f'/api/misc/admin/events/{created_event_id}/', update_data, format='json')
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                event = response.json()
                print(f"✅ Event updated: {event['title']}")
                print(f"New location: {event['location']}")
                print(f"Featured: {event['is_featured']}")
            else:
                print(f"❌ Error: {response.data}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 6: Event Statistics
    print("\n6️⃣ Testing Event Statistics")
    print("-" * 30)
    try:
        response = client.get('/api/misc/admin/events/stats/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics retrieved:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ Error: {response.data}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Toggle Featured Status
    if created_event_id:
        print("\n7️⃣ Testing Toggle Featured")
        print("-" * 28)
        try:
            response = client.post(f'/api/misc/admin/events/{created_event_id}/toggle-featured/')
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
            else:
                print(f"❌ Error: {response.data}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 8: Regular User Access (should fail)
    print("\n8️⃣ Testing Regular User Access (should fail)")
    print("-" * 50)
    try:
        # Create regular user
        regular_user = User.objects.create_user(
            email='test@user.com',
            password='testpass',
            role=User.Role.USER,
            account_status=User.AccountStatus.ACTIVE
        )
        client.force_authenticate(user=regular_user)
        
        response = client.get('/api/misc/admin/events/')
        print(f"Status: {response.status_code}")
        if response.status_code == 403:
            print("✅ Access correctly denied for regular user")
        else:
            print(f"❌ Unexpected access granted: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Event CRUD API Testing Complete!")
    print("=" * 50)

if __name__ == '__main__':
    test_event_crud_api()
