"""
Comprehensive Puja App Testing Suite
Tests all major functionality including models, serializers, views, and API endpoints
"""

import json
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from puja.models import PujaCategory, PujaService, Package, PujaBooking
from puja.serializers import (
    PujaCategorySerializer, PujaServiceSerializer, 
    PackageSerializer, PujaBookingSerializer, CreatePujaBookingSerializer
)

User = get_user_model()

class PujaModelTests(TestCase):
    """Test Puja models functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@okpuja.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='+919876543210'
        )
        
        self.category = PujaCategory.objects.create(
            name='Ganesh Puja'
        )
        
        self.service = PujaService.objects.create(
            title='Complete Ganesh Puja with Aarti',
            image='https://example.com/ganesh.jpg',
            description='Traditional Ganesh puja ceremony',
            category=self.category,
            type='HOME',
            duration_minutes=60
        )
        
        self.package = Package.objects.create(
            puja_service=self.service,
            location='Mumbai',
            language='HINDI',
            package_type='STANDARD',
            price=Decimal('1500.00'),
            description='Complete puja package',
            includes_materials=True,
            priest_count=1
        )
    
    def test_puja_category_creation(self):
        """Test PujaCategory model"""
        self.assertEqual(str(self.category), 'Ganesh Puja')
        self.assertTrue(self.category.created_at)
        self.assertTrue(self.category.updated_at)
    
    def test_puja_service_creation(self):
        """Test PujaService model"""
        self.assertEqual(str(self.service), 'Complete Ganesh Puja with Aarti (At Home)')
        self.assertEqual(self.service.category, self.category)
        self.assertEqual(self.service.type, 'HOME')
        self.assertTrue(self.service.is_active)
    
    def test_package_creation(self):
        """Test Package model"""
        expected_str = f"{self.service.title} - Hindi Standard"
        self.assertEqual(str(self.package), expected_str)
        self.assertEqual(self.package.puja_service, self.service)
        self.assertEqual(self.package.price, Decimal('1500.00'))
        self.assertTrue(self.package.includes_materials)
    
    def test_puja_booking_creation(self):
        """Test PujaBooking model"""
        booking = PujaBooking.objects.create(
            user=self.user,
            puja_service=self.service,
            package=self.package,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            contact_name='Test User',
            contact_number='+919876543210',
            contact_email='test@example.com',
            address='Test Address, Mumbai'
        )
        
        expected_str = f"{self.service.title} - {booking.booking_date} (Pending)"
        self.assertEqual(str(booking), expected_str)
        self.assertEqual(booking.status, 'PENDING')
        self.assertEqual(booking.user, self.user)
    
    def test_model_relationships(self):
        """Test model relationships"""
        # Category -> Services
        self.assertIn(self.service, self.category.services.all())
        
        # Service -> Packages
        self.assertIn(self.package, self.service.packages.all())
        
        # Create booking and test relationships
        booking = PujaBooking.objects.create(
            user=self.user,
            puja_service=self.service,
            package=self.package,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            contact_name='Test User',
            contact_number='+919876543210',
            contact_email='test@example.com',
            address='Test Address'
        )
        
        # Service -> Bookings
        self.assertIn(booking, self.service.bookings.all())
        
        # Package -> Bookings
        self.assertIn(booking, self.package.bookings.all())
        
        # User -> Bookings
        self.assertIn(booking, self.user.puja_bookings.all())

class PujaSerializerTests(TestCase):
    """Test Puja serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@okpuja.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.category = PujaCategory.objects.create(name='Test Category')
        self.service = PujaService.objects.create(
            title='Test Service',
            image='https://example.com/test.jpg',
            description='Test description',
            category=self.category,
            type='HOME',
            duration_minutes=60
        )
        self.package = Package.objects.create(
            puja_service=self.service,
            location='Mumbai',
            language='HINDI',
            package_type='STANDARD',
            price=Decimal('1500.00'),
            description='Test package'
        )
    
    def test_category_serializer(self):
        """Test PujaCategorySerializer"""
        serializer = PujaCategorySerializer(self.category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Category')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_service_serializer(self):
        """Test PujaServiceSerializer"""
        serializer = PujaServiceSerializer(self.service)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Service')
        self.assertEqual(data['image_url'], 'https://example.com/test.jpg')
        self.assertEqual(data['type'], 'HOME')
        self.assertEqual(data['duration_minutes'], 60)
        self.assertIn('category_detail', data)
    
    def test_package_serializer(self):
        """Test PackageSerializer"""
        serializer = PackageSerializer(self.package)
        data = serializer.data
        
        self.assertEqual(data['location'], 'Mumbai')
        self.assertEqual(data['language'], 'HINDI')
        self.assertEqual(data['package_type'], 'STANDARD')
        self.assertEqual(float(data['price']), 1500.00)
        self.assertIn('puja_service_detail', data)
    
    def test_booking_serializer_validation(self):
        """Test CreatePujaBookingSerializer validation"""
        # Test valid data
        valid_data = {
            'puja_service': self.service.id,
            'package': self.package.id,
            'booking_date': (date.today() + timedelta(days=7)).isoformat(),
            'start_time': '10:00:00',
            'contact_name': 'Test User',
            'contact_number': '+919876543210',
            'contact_email': 'test@example.com',
            'address': 'Test Address'
        }
        
        serializer = CreatePujaBookingSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test past date validation
        invalid_data = valid_data.copy()
        invalid_data['booking_date'] = (date.today() - timedelta(days=1)).isoformat()
        
        serializer = CreatePujaBookingSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('booking_date', serializer.errors)
        
        # Test invalid time validation
        invalid_data = valid_data.copy()
        invalid_data['start_time'] = '03:00:00'  # Too early
        
        serializer = CreatePujaBookingSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('start_time', serializer.errors)
        
        # Test invalid phone number
        invalid_data = valid_data.copy()
        invalid_data['contact_number'] = '123'  # Invalid format
        
        serializer = CreatePujaBookingSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contact_number', serializer.errors)

class PujaAPITests(APITestCase):
    """Test Puja API endpoints"""
    
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            email='testuser@okpuja.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.admin_user = User.objects.create_user(
            email='admin@okpuja.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create test data
        self.category = PujaCategory.objects.create(name='Test Category')
        self.service = PujaService.objects.create(
            title='Test Service',
            image='https://example.com/test.jpg',
            description='Test description',
            category=self.category,
            type='HOME',
            duration_minutes=60
        )
        self.package = Package.objects.create(
            puja_service=self.service,
            location='Mumbai',
            language='HINDI',
            package_type='STANDARD',
            price=Decimal('1500.00'),
            description='Test package'
        )
        
        # Setup API client
        self.client = APIClient()
    
    def get_user_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_category_list_api(self):
        """Test category list API (public)"""
        url = reverse('puja-category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Category')
    
    def test_category_create_api(self):
        """Test category creation API (admin only)"""
        url = reverse('puja-category-create')
        data = {'name': 'New Category'}
        
        # Test unauthorized access
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test regular user access
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test admin access
        admin_token = self.get_user_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Category')
    
    def test_service_list_api(self):
        """Test service list API (public)"""
        url = reverse('puja-service-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Service')
    
    def test_service_filtering(self):
        """Test service filtering"""
        # Create additional services
        PujaService.objects.create(
            title='Temple Service',
            image='https://example.com/temple.jpg',
            description='Temple service',
            category=self.category,
            type='TEMPLE',
            duration_minutes=90
        )
        
        url = reverse('puja-service-list')
        
        # Test filter by type
        response = self.client.get(url, {'type': 'HOME'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'HOME')
        
        # Test filter by category
        response = self.client.get(url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Test search
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_package_list_api(self):
        """Test package list API"""
        url = reverse('package-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['location'], 'Mumbai')
    
    def test_package_filtering(self):
        """Test package filtering"""
        # Create additional package
        Package.objects.create(
            puja_service=self.service,
            location='Delhi',
            language='ENGLISH',
            package_type='PREMIUM',
            price=Decimal('2500.00'),
            description='Premium package'
        )
        
        url = reverse('package-list')
        
        # Test filter by service
        response = self.client.get(url, {'puja_service': self.service.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Test filter by language
        response = self.client.get(url, {'language': 'HINDI'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test price range filter
        response = self.client.get(url, {'min_price': 2000})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(float(response.data[0]['price']), 2500.00)
    
    def test_booking_creation_api(self):
        """Test booking creation API"""
        url = reverse('puja-booking-create')
        data = {
            'puja_service': self.service.id,
            'package': self.package.id,
            'booking_date': (date.today() + timedelta(days=7)).isoformat(),
            'start_time': '10:00:00',
            'contact_name': 'Test User',
            'contact_number': '+919876543210',
            'contact_email': 'test@example.com',
            'address': 'Test Address, Mumbai'
        }
        
        # Test unauthorized access
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test authorized access
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify booking was created
        booking = PujaBooking.objects.get(id=response.data['id'])
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.puja_service, self.service)
        self.assertEqual(booking.package, self.package)
    
    def test_booking_list_api(self):
        """Test booking list API"""
        # Create a booking
        booking = PujaBooking.objects.create(
            user=self.user,
            puja_service=self.service,
            package=self.package,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            contact_name='Test User',
            contact_number='+919876543210',
            contact_email='test@example.com',
            address='Test Address'
        )
        
        url = reverse('puja-booking-list')
        
        # Test unauthorized access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test user access (should see own bookings)
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], booking.id)
        
        # Test admin access (should see all bookings)
        admin_token = self.get_user_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_booking_detail_api(self):
        """Test booking detail API"""
        booking = PujaBooking.objects.create(
            user=self.user,
            puja_service=self.service,
            package=self.package,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            contact_name='Test User',
            contact_number='+919876543210',
            contact_email='test@example.com',
            address='Test Address'
        )
        
        url = reverse('puja-booking-detail', kwargs={'pk': booking.id})
        
        # Test unauthorized access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test user access (owner)
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], booking.id)
        
        # Test update booking
        update_data = {'special_instructions': 'Updated instructions'}
        response = self.client.patch(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        booking.refresh_from_db()
        self.assertEqual(booking.special_instructions, 'Updated instructions')

class PujaIntegrationTests(APITestCase):
    """Integration tests for complete puja booking flow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='customer@okpuja.com',
            password='testpass123',
            first_name='Customer',
            last_name='Test'
        )
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    
    def test_complete_booking_flow(self):
        """Test complete booking flow from category to booking"""
        
        # Step 1: Create category
        category = PujaCategory.objects.create(name='Ganesh Puja')
        
        # Step 2: Create service
        service = PujaService.objects.create(
            title='Complete Ganesh Puja',
            image='https://example.com/ganesh.jpg',
            description='Traditional Ganesh puja ceremony',
            category=category,
            type='HOME',
            duration_minutes=90
        )
        
        # Step 3: Create packages
        basic_package = Package.objects.create(
            puja_service=service,
            location='Mumbai',
            language='HINDI',
            package_type='BASIC',
            price=Decimal('800.00'),
            description='Basic puja package'
        )
        
        premium_package = Package.objects.create(
            puja_service=service,
            location='Mumbai',
            language='HINDI',
            package_type='PREMIUM',
            price=Decimal('2500.00'),
            description='Premium puja package',
            includes_materials=True,
            priest_count=2
        )
        
        # Step 4: Browse categories
        categories_url = reverse('puja-category-list')
        response = self.client.get(categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Step 5: Browse services by category
        services_url = reverse('puja-service-list')
        response = self.client.get(services_url, {'category': category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Complete Ganesh Puja')
        
        # Step 6: Browse packages for service
        packages_url = reverse('package-list')
        response = self.client.get(packages_url, {'puja_service': service.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Step 7: Create booking with premium package
        booking_url = reverse('puja-booking-create')
        booking_data = {
            'puja_service': service.id,
            'package': premium_package.id,
            'booking_date': (date.today() + timedelta(days=14)).isoformat(),
            'start_time': '09:00:00',
            'contact_name': 'Customer Test',
            'contact_number': '+919876543210',
            'contact_email': 'customer@okpuja.com',
            'address': '123 Test Street, Mumbai, Maharashtra 400001',
            'special_instructions': 'Please bring extra flowers for the ceremony'
        }
        
        response = self.client.post(booking_url, booking_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        booking_id = response.data['id']
        
        # Step 8: Verify booking details
        booking_detail_url = reverse('puja-booking-detail', kwargs={'pk': booking_id})
        response = self.client.get(booking_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        booking_data = response.data
        self.assertEqual(booking_data['status'], 'PENDING')
        self.assertEqual(booking_data['puja_service']['title'], 'Complete Ganesh Puja')
        self.assertEqual(booking_data['package']['package_type'], 'PREMIUM')
        self.assertEqual(float(booking_data['package']['price']), 2500.00)
        
        # Step 9: List user's bookings
        bookings_url = reverse('puja-booking-list')
        response = self.client.get(bookings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], booking_id)
        
        # Step 10: Update booking
        update_data = {
            'special_instructions': 'Updated: Please bring extra flowers and fruits'
        }
        response = self.client.patch(booking_detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        response = self.client.get(booking_detail_url)
        self.assertEqual(
            response.data['special_instructions'],
            'Updated: Please bring extra flowers and fruits'
        )

def run_puja_tests():
    """Run all puja tests and return results"""
    from django.test.utils import get_runner
    from django.conf import settings
    import sys
    
    # Configure test runner
    test_runner = get_runner(settings)()
    
    # Run tests
    test_labels = [
        'puja.tests.PujaModelTests',
        'puja.tests.PujaSerializerTests', 
        'puja.tests.PujaAPITests',
        'puja.tests.PujaIntegrationTests'
    ]
    
    result = test_runner.run_tests(test_labels)
    
    if result == 0:
        print("✅ All puja tests passed!")
    else:
        print(f"❌ {result} test(s) failed")
    
    return result

if __name__ == '__main__':
    run_puja_tests()
