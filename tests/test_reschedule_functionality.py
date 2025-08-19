#!/usr/bin/env python
"""
Test script for testing reschedule functionality for both Puja and Astrology bookings.

This script tests:
1. Puja booking reschedule (using ViewSet with @action)
2. Astrology booking reschedule (using APIView)

Usage:
python test_reschedule_functionality.py
"""

import os
import sys
import json
import requests
from datetime import datetime, date, time, timedelta
from django.core.wsgi import get_wsgi_application

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
application = get_wsgi_application()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from booking.models import Booking, BookingStatus
from astrology.models import AstrologyBooking, AstrologyService
from puja.models import PujaService, Package
from cart.models import Cart

User = get_user_model()

class RescheduleTestSuite:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.client = Client()
        self.auth_token = None
        self.user = None
        self.admin_user = None
        self.test_results = []
        
    def setup_test_data(self):
        """Create test users, services, and bookings"""
        from datetime import date, time, timedelta
        
        print("🔧 Setting up test data...")
        
        # Clean up existing test data first
        User.objects.filter(email__in=['test.reschedule@example.com', 'admin.reschedule@example.com']).delete()
        User.objects.filter(phone__in=['6123456789', '6123456788']).delete()
        AstrologyBooking.objects.filter(astro_book_id='TEST_ASTRO_BOOK_001').delete()
        Booking.objects.filter(book_id='TEST_BOOK_001').delete()
        
        # Create test user
        self.user, created = User.objects.get_or_create(
            email='test.reschedule@example.com',
            defaults={
                'phone': '6123456789',
                'is_active': True,
                'account_status': 'ACTIVE',
                'role': 'USER',
                'email_verified': True
            }
        )
        if created:
            self.user.set_password('testpass123')
            self.user.save()
        
        # Create admin user  
        self.admin_user, created = User.objects.get_or_create(
            email='admin.reschedule@example.com',
            defaults={
                'phone': '6123456788',
                'is_active': True,
                'account_status': 'ACTIVE',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'email_verified': True
            }
        )
        if created:
            self.admin_user.set_password('adminpass123')
            self.admin_user.save()
        
        # Create astrology service
        self.astrology_service, created = AstrologyService.objects.get_or_create(
            title='Test Horoscope Reading',
            defaults={
                'service_type': 'HOROSCOPE',
                'description': 'Test astrology service for reschedule testing',
                'price': 500.00,
                'duration_minutes': 60,
                'is_active': True
            }
        )
        
        # Create astrology booking
        self.astrology_booking, created = AstrologyBooking.objects.get_or_create(
            astro_book_id='TEST_ASTRO_BOOK_001',
            defaults={
                'user': self.user,
                'service': self.astrology_service,
                'language': 'Hindi',
                'preferred_date': date.today() + timedelta(days=7),
                'preferred_time': time(10, 0),
                'birth_place': 'Delhi',
                'birth_date': date(1990, 1, 1),
                'birth_time': time(12, 0),
                'gender': 'MALE',
                'contact_email': 'test.reschedule@example.com',
                'contact_phone': '6123456789',
                'status': 'CONFIRMED'
            }
        )
        
        print(f"✅ Created astrology booking: {self.astrology_booking.astro_book_id}")
        
        # Create puja service and package for regular booking
        from puja.models import PujaCategory
        category, created = PujaCategory.objects.get_or_create(
            name='Test Category'
        )
        
        puja_service, created = PujaService.objects.get_or_create(
            title='Test Puja Service',
            defaults={
                'description': 'Test puja service for reschedule testing',
                'category': category,
                'type': 'HOME',
                'duration_minutes': 120,
                'is_active': True,
                'image': 'https://example.com/test-image.jpg'
            }
        )
        
        package, created = Package.objects.get_or_create(
            puja_service=puja_service,
            language='HINDI',
            package_type='STANDARD',
            defaults={
                'location': 'Delhi',
                'price': 1000.00,
                'description': 'Test package',
                'includes_materials': True,
                'priest_count': 1,
                'is_active': True
            }
        )
        
        # Create a cart and booking
        cart, created = Cart.objects.get_or_create(
            cart_id='TEST_CART_001',
            defaults={
                'user': self.user,
                'puja_service': puja_service,
                'package': package,
                'selected_date': date.today() + timedelta(days=5),
                'selected_time': '09:00',
                'status': 'CONVERTED'  # Cart used for booking
            }
        )
        
        # Create puja booking
        self.puja_booking, created = Booking.objects.get_or_create(
            book_id='TEST_BOOK_001',
            defaults={
                'user': self.user,
                'cart': cart,
                'selected_date': date.today() + timedelta(days=5),
                'selected_time': time(9, 0),
                'status': BookingStatus.CONFIRMED
            }
        )
        
        print(f"✅ Created puja booking: {self.puja_booking.book_id}")
        print("✅ Test data setup complete!")
    
    def authenticate_user(self, user_email, password):
        """Authenticate user and get token"""
        login_data = {
            'email': user_email,
            'password': password
        }
        
        response = self.client.post('/api/accounts/login/', login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        else:
            print(f"❌ Authentication failed: {response.content}")
            return None
    
    def test_astrology_booking_reschedule(self):
        """Test astrology booking reschedule endpoint"""
        print("\\n🧪 Testing Astrology Booking Reschedule...")
        
        # Authenticate as user
        token = self.authenticate_user('test.reschedule@example.com', 'testpass123')
        if not token:
            print("❌ Failed to authenticate user")
            return False
        
        # Test data
        new_date = date.today() + timedelta(days=10)
        new_time = time(14, 0)  # 2:00 PM
        
        reschedule_data = {
            'preferred_date': new_date.isoformat(),
            'preferred_time': new_time.isoformat(),
            'reason': 'Testing reschedule functionality'
        }
        
        # Test endpoint URL
        url = f'/api/astrology/bookings/{self.astrology_booking.id}/reschedule/'
        
        print(f"📡 PATCH {url}")
        print(f"📤 Request Data: {json.dumps(reschedule_data, indent=2)}")
        
        # Make the request
        headers = {'Authorization': f'Bearer {token}'}
        response = self.client.patch(
            url, 
            data=json.dumps(reschedule_data),
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Data: {response.content.decode()}")
        
        if response.status_code == 200:
            # Verify the booking was updated
            self.astrology_booking.refresh_from_db()
            if (self.astrology_booking.preferred_date == new_date and 
                self.astrology_booking.preferred_time == new_time):
                print("✅ Astrology booking reschedule successful!")
                return True
            else:
                print("❌ Booking was not updated in database")
                return False
        else:
            print(f"❌ Astrology booking reschedule failed: {response.content.decode()}")
            return False
    
    def test_puja_booking_reschedule(self):
        """Test puja booking reschedule endpoint (ViewSet action)"""
        print("\\n🧪 Testing Puja Booking Reschedule...")
        
        # Authenticate as user
        token = self.authenticate_user('test.reschedule@example.com', 'testpass123')
        if not token:
            print("❌ Failed to authenticate user")
            return False
        
        # Test data
        new_date = date.today() + timedelta(days=8)
        new_time = time(16, 0)  # 4:00 PM
        
        reschedule_data = {
            'selected_date': new_date.isoformat(),
            'selected_time': new_time.isoformat(),
            'reason': 'Testing puja booking reschedule functionality'
        }
        
        # Test endpoint URL (ViewSet action)
        url = f'/api/booking/bookings/{self.puja_booking.id}/reschedule/'
        
        print(f"📡 POST {url}")
        print(f"📤 Request Data: {json.dumps(reschedule_data, indent=2)}")
        
        # Make the request
        response = self.client.post(
            url, 
            data=json.dumps(reschedule_data),
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Data: {response.content.decode()}")
        
        if response.status_code == 200:
            # Verify the booking was updated
            self.puja_booking.refresh_from_db()
            if (self.puja_booking.selected_date == new_date and 
                self.puja_booking.selected_time == new_time):
                print("✅ Puja booking reschedule successful!")
                return True
            else:
                print("❌ Booking was not updated in database")
                print(f"Expected: {new_date} at {new_time}")
                print(f"Actual: {self.puja_booking.selected_date} at {self.puja_booking.selected_time}")
                return False
        else:
            print(f"❌ Puja booking reschedule failed: {response.content.decode()}")
            return False
    
    def test_admin_reschedule_permissions(self):
        """Test admin reschedule permissions"""
        print("\\n🧪 Testing Admin Reschedule Permissions...")
        
        # Authenticate as admin
        admin_token = self.authenticate_user('admin.reschedule@example.com', 'adminpass123')
        if not admin_token:
            print("❌ Failed to authenticate admin")
            return False
        
        # Test astrology booking reschedule as admin
        new_date = date.today() + timedelta(days=15)
        new_time = time(11, 0)
        
        reschedule_data = {
            'preferred_date': new_date.isoformat(),
            'preferred_time': new_time.isoformat(),
            'reason': 'Admin reschedule test'
        }
        
        url = f'/api/astrology/bookings/{self.astrology_booking.id}/reschedule/'
        
        response = self.client.patch(
            url, 
            data=json.dumps(reschedule_data),
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
        )
        
        print(f"📡 Admin Astrology Reschedule - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Admin can reschedule astrology bookings!")
            return True
        else:
            print(f"❌ Admin reschedule failed: {response.content.decode()}")
            return False
    
    def test_validation_errors(self):
        """Test validation errors for reschedule"""
        print("\\n🧪 Testing Validation Errors...")
        
        # Authenticate as user
        token = self.authenticate_user('test.reschedule@example.com', 'testpass123')
        if not token:
            print("❌ Failed to authenticate user")
            return False
        
        # Test past date validation
        past_date = date.today() - timedelta(days=1)
        
        reschedule_data = {
            'preferred_date': past_date.isoformat(),
            'preferred_time': time(10, 0).isoformat(),
            'reason': 'Testing past date validation'
        }
        
        url = f'/api/astrology/bookings/{self.astrology_booking.id}/reschedule/'
        
        response = self.client.patch(
            url, 
            data=json.dumps(reschedule_data),
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
        )
        
        print(f"📡 Past Date Test - Status: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Past date validation working correctly!")
            return True
        else:
            print(f"❌ Past date validation failed: Expected 400, got {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all reschedule tests"""
        print("🚀 Starting Reschedule Functionality Tests")
        print("=" * 50)
        
        try:
            # Setup
            self.setup_test_data()
            
            # Run tests
            tests = [
                ('Astrology Booking Reschedule', self.test_astrology_booking_reschedule),
                ('Puja Booking Reschedule', self.test_puja_booking_reschedule),
                ('Admin Reschedule Permissions', self.test_admin_reschedule_permissions),
                ('Validation Errors', self.test_validation_errors),
            ]
            
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                try:
                    if test_func():
                        passed += 1
                        print(f"✅ {test_name}: PASSED")
                    else:
                        print(f"❌ {test_name}: FAILED")
                except Exception as e:
                    print(f"❌ {test_name}: ERROR - {str(e)}")
            
            # Results
            print("\\n" + "=" * 50)
            print(f"🏁 Test Results: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All tests passed! Reschedule functionality is working correctly.")
            else:
                print("⚠️  Some tests failed. Please check the implementation.")
                
        except Exception as e:
            print(f"💥 Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()

def print_endpoint_documentation():
    """Print endpoint documentation"""
    print("\\n" + "=" * 60)
    print("📚 RESCHEDULE ENDPOINTS DOCUMENTATION")
    print("=" * 60)
    
    print("\\n🔮 ASTROLOGY BOOKING RESCHEDULE")
    print("-" * 30)
    print("METHOD: PATCH")
    print("URL: /api/astrology/bookings/{id}/reschedule/")
    print("AUTHENTICATION: Required (Bearer token)")
    print("PERMISSIONS: Owner or Admin/Staff")
    print("")
    print("REQUEST BODY:")
    print(json.dumps({
        "preferred_date": "YYYY-MM-DD",
        "preferred_time": "HH:MM:SS",
        "reason": "Optional reason for rescheduling"
    }, indent=2))
    print("")
    print("RESPONSE (200):")
    print(json.dumps({
        "message": "Astrology booking rescheduled successfully",
        "booking": "{ booking object }",
        "old_date": "Previous date",
        "old_time": "Previous time"
    }, indent=2))
    
    print("\\n🕉️  PUJA BOOKING RESCHEDULE")
    print("-" * 25)
    print("METHOD: POST")
    print("URL: /api/booking/bookings/{id}/reschedule/")
    print("AUTHENTICATION: Required (Bearer token)")
    print("PERMISSIONS: Owner, Assigned Employee, or Admin")
    print("")
    print("REQUEST BODY:")
    print(json.dumps({
        "selected_date": "YYYY-MM-DD",
        "selected_time": "HH:MM:SS",
        "reason": "Optional reason for rescheduling"
    }, indent=2))
    print("")
    print("RESPONSE (200):")
    print(json.dumps({
        "message": "Booking rescheduled successfully",
        "booking": "{ booking object }"
    }, indent=2))
    
    print("\\n🔧 TESTING WITH CURL")
    print("-" * 20)
    print("# Get auth token first:")
    print('curl -X POST http://localhost:8000/api/accounts/login/ \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"email": "user@example.com", "password": "password"}\'')
    print("")
    print("# Reschedule astrology booking:")
    print('curl -X PATCH http://localhost:8000/api/astrology/bookings/1/reschedule/ \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -H "Authorization: Bearer YOUR_TOKEN" \\')
    print('  -d \'{"preferred_date": "2025-08-20", "preferred_time": "14:00:00"}\'')
    print("")
    print("# Reschedule puja booking:")
    print('curl -X POST http://localhost:8000/api/booking/bookings/1/reschedule/ \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -H "Authorization: Bearer YOUR_TOKEN" \\')
    print('  -d \'{"selected_date": "2025-08-20", "selected_time": "16:00:00"}\'')

if __name__ == '__main__':
    print("🔧 Reschedule Functionality Test Suite")
    print("=" * 60)
    
    # Print documentation
    print_endpoint_documentation()
    
    # Run tests if requested
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--run-tests':
        test_suite = RescheduleTestSuite()
        test_suite.run_all_tests()
    else:
        print("\\n" + "=" * 60)
        print("📋 TO RUN TESTS:")
        print("python test_reschedule_functionality.py --run-tests")
        print("")
        print("📋 TO START SERVER:")
        print("python manage.py runserver")
        print("")
        print("📋 MANUAL TESTING:")
        print("Use the CURL commands above or test with Postman/similar tool")
