from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import User
from .models import Event, JobOpening, ContactUs
from PIL import Image
from io import BytesIO
import json
from datetime import datetime, timedelta

class EventModelTest(TestCase):
    def test_event_creation(self):
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            event_date=timezone.now().date() + timedelta(days=1),
            status='PUBLISHED'
        )
        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.slug, "test-event")
        self.assertFalse(event.is_featured)

    def test_event_str_method(self):
        event = Event.objects.create(
            title="Test Event",
            event_date=timezone.now().date() + timedelta(days=1)
        )
        self.assertEqual(str(event), "Test Event")

class EventAPITest(APITestCase):
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            email="admin@okpuja.com",
            password="admin@123",
            role=User.Role.ADMIN,
            account_status=User.AccountStatus.ACTIVE,
            email_verified=True
        )
        
        self.regular_user = User.objects.create_user(
            email="user@test.com",
            password="testpass123",
            role=User.Role.USER,
            account_status=User.AccountStatus.ACTIVE,
            email_verified=True
        )
        
        # Create test image
        self.test_image = self.create_test_image()
        
        # Create test events
        self.event1 = Event.objects.create(
            title="Future Event",
            description="A future event",
            event_date=timezone.now().date() + timedelta(days=30),
            start_time="10:00:00",
            end_time="18:00:00",
            location="Test Location",
            status='PUBLISHED',
            is_featured=True,
            original_image=self.test_image
        )
        
        self.event2 = Event.objects.create(
            title="Draft Event",
            description="A draft event",
            event_date=timezone.now().date() + timedelta(days=15),
            status='DRAFT'
        )
        
        self.client = APIClient()

    def create_test_image(self):
        """Create a test image file"""
        img = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile(
            "test.jpg", 
            img_io.getvalue(), 
            content_type="image/jpeg"
        )

    def test_public_event_list(self):
        """Test public can access event list"""
        url = reverse('event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only published events should be visible
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Future Event')

    def test_public_event_detail(self):
        """Test public can access event detail"""
        url = reverse('event-detail', kwargs={'slug': self.event1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Future Event')

    def test_admin_can_list_all_events(self):
        """Test admin can see all events including drafts"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_admin_can_create_event(self):
        """Test admin can create events"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-list')
        
        data = {
            'title': 'New Event',
            'description': 'New event description',
            'event_date': (timezone.now().date() + timedelta(days=45)).isoformat(),
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'location': 'New Location',
            'registration_link': 'https://example.com/register',
            'status': 'PUBLISHED',
            'is_featured': False,
            'original_image': self.create_test_image()
        }
        
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Event')
        self.assertEqual(response.data['slug'], 'new-event')

    def test_admin_can_update_event(self):
        """Test admin can update events"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-detail', kwargs={'pk': self.event1.pk})
        
        data = {
            'title': 'Updated Event Title',
            'description': 'Updated description',
            'event_date': self.event1.event_date.isoformat(),
            'start_time': '11:00:00',
            'end_time': '19:00:00',
            'location': 'Updated Location',
            'status': 'PUBLISHED',
            'is_featured': False
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Event Title')
        self.assertEqual(response.data['location'], 'Updated Location')

    def test_admin_can_delete_event(self):
        """Test admin can delete events"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-detail', kwargs={'pk': self.event2.pk})
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(pk=self.event2.pk).exists())

    def test_admin_can_toggle_featured(self):
        """Test admin can toggle featured status"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-toggle-featured', kwargs={'pk': self.event1.pk})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        self.event1.refresh_from_db()
        self.assertFalse(self.event1.is_featured)  # Was True, now False

    def test_admin_can_change_status(self):
        """Test admin can change event status"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-change-status', kwargs={'pk': self.event2.pk})
        
        data = {'status': 'PUBLISHED'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        self.event2.refresh_from_db()
        self.assertEqual(self.event2.status, 'PUBLISHED')

    def test_admin_can_get_stats(self):
        """Test admin can get event statistics"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-stats')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_events', response.data)
        self.assertIn('published_events', response.data)
        self.assertIn('draft_events', response.data)
        self.assertEqual(response.data['total_events'], 2)

    def test_regular_user_cannot_access_admin_endpoints(self):
        """Test regular user cannot access admin endpoints"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Test list
        url = reverse('admin-events-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test create
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test update
        url = reverse('admin-events-detail', kwargs={'pk': self.event1.pk})
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_access_admin_endpoints(self):
        """Test anonymous user cannot access admin endpoints"""
        url = reverse('admin-events-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_event_validation(self):
        """Test event validation"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-list')
        
        # Test invalid end time (before start time)
        data = {
            'title': 'Invalid Event',
            'description': 'Invalid event',
            'event_date': (timezone.now().date() + timedelta(days=1)).isoformat(),
            'start_time': '18:00:00',
            'end_time': '09:00:00',  # Before start time
            'status': 'PUBLISHED'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('End time must be after start time', str(response.data))

    def test_event_search_and_filter(self):
        """Test event search and filtering in admin"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-events-list')
        
        # Test status filter
        response = self.client.get(url + '?status=PUBLISHED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test featured filter
        response = self.client.get(url + '?is_featured=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test search
        response = self.client.get(url + '?search=Future')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_featured_events_endpoint(self):
        """Test featured events endpoint"""
        url = reverse('featured-events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Future Event')
        self.assertTrue(response.data[0]['is_featured'])

    def test_image_urls_in_response(self):
        """Test that image URLs are properly included in response"""
        url = reverse('event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        event_data = response.data[0]
        self.assertIn('thumbnail_url', event_data)
        self.assertIn('banner_url', event_data)
        self.assertIn('original_image_url', event_data)
        # URLs should not be None for events with images
        self.assertIsNotNone(event_data['thumbnail_url'])

    def test_days_until_calculation(self):
        """Test days_until field calculation"""
        url = reverse('event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        event_data = response.data[0]
        self.assertIn('days_until', event_data)
        # Should be around 30 days (give or take 1 for test execution time)
        self.assertGreaterEqual(event_data['days_until'], 29)
        self.assertLessEqual(event_data['days_until'], 31)
