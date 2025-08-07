"""
Comprehensive test script for all admin implementations
Tests Astrology, Puja, and Booking admin systems
"""
import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
sys.path.append('c:\\Users\\Prince Raj\\Desktop\\nextjs project\\okpuja_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

# Import models
from astrology.models import AstrologyBooking, AstrologerProfile
from puja.models import PujaBooking, PujaService, Package, PujaCategory
from booking.models import Booking, BookingStatus
from accounts.models import Address
from cart.models import Cart, CartItem

User = get_user_model()

class ComprehensiveAdminTest:
    def __init__(self):
        self.client = APIClient()
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup test data for all systems"""
        print("🔧 Setting up test data...")
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True,
            first_name='Admin',
            last_name='User'
        )
        
        # Create regular users
        self.test_user1 = User.objects.create_user(
            email='user1@test.com',
            password='userpass123',
            first_name='Test',
            last_name='User1'
        )
        
        self.test_user2 = User.objects.create_user(
            email='user2@test.com',
            password='userpass123',
            first_name='Test',
            last_name='User2'
        )
        
        # Create staff user for assignments
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='staffpass123',
            is_staff=True,
            first_name='Staff',
            last_name='Member'
        )
        
        # Setup authentication
        self.admin_token, created = Token.objects.get_or_create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        
        # Create test addresses
        self.address1 = Address.objects.create(
            user=self.test_user1,
            full_address="123 Test Street, Test City, Test State - 123456"
        )
        
        # Setup Astrology test data
        self.setup_astrology_data()
        
        # Setup Puja test data
        self.setup_puja_data()
        
        # Setup Booking test data
        self.setup_booking_data()
        
        print("✅ Test data setup completed!")
    
    def setup_astrology_data(self):
        """Setup astrology test data"""
        # Create astrologer profiles
        self.astrologer = AstrologerProfile.objects.create(
            user=self.staff_user,
            name="Test Astrologer",
            specializations=["Vedic", "Numerology"],
            experience_years=10,
            rating=4.8,
            hourly_rate=500.00,
            is_available=True
        )
        
        # Create astrology bookings
        for i in range(5):
            AstrologyBooking.objects.create(
                user=self.test_user1 if i % 2 == 0 else self.test_user2,
                astrologer=self.astrologer,
                consultation_type='chat',
                scheduled_datetime=datetime.now() + timedelta(days=i+1),
                duration_minutes=30,
                amount_paid=Decimal('500.00'),
                status='confirmed' if i < 3 else 'pending',
                birth_date='1990-01-01',
                birth_time='12:00',
                birth_place='Test City'
            )
    
    def setup_puja_data(self):
        """Setup puja test data"""
        # Create puja category
        self.puja_category = PujaCategory.objects.create(
            name="Test Puja Category",
            description="Test category for pujas"
        )
        
        # Create puja service
        self.puja_service = PujaService.objects.create(
            title="Test Puja Service",
            description="Test puja service description",
            category=self.puja_category,
            type='HOME',
            is_active=True
        )
        
        # Create package
        self.puja_package = Package.objects.create(
            puja_service=self.puja_service,
            name="Basic Package",
            price=Decimal('1000.00'),
            description="Basic puja package",
            is_active=True
        )
        
        # Create puja bookings
        for i in range(5):
            PujaBooking.objects.create(
                user=self.test_user1 if i % 2 == 0 else self.test_user2,
                puja_service=self.puja_service,
                package=self.puja_package,
                contact_name=f"Test User {i+1}",
                contact_email=f"user{i+1}@test.com",
                contact_number=f"987654321{i}",
                address="Test Address",
                booking_date=(datetime.now() + timedelta(days=i+1)).date(),
                start_time='10:00',
                status='CONFIRMED' if i < 3 else 'PENDING'
            )
    
    def setup_booking_data(self):
        """Setup booking test data"""
        # Create cart
        self.cart = Cart.objects.create(
            user=self.test_user1,
            total_price=Decimal('2000.00')
        )
        
        # Create bookings
        for i in range(5):
            Booking.objects.create(
                user=self.test_user1 if i % 2 == 0 else self.test_user2,
                cart=self.cart if i == 0 else None,
                selected_date=(datetime.now() + timedelta(days=i+1)).date(),
                selected_time='14:00',
                address=self.address1,
                status=BookingStatus.CONFIRMED if i < 3 else BookingStatus.PENDING,
                assigned_to=self.staff_user if i < 2 else None
            )
    
    def test_astrology_admin_endpoints(self):
        """Test all astrology admin endpoints"""
        print("\n🔮 Testing Astrology Admin Endpoints...")
        
        endpoints_to_test = [
            {
                'name': 'Astrology Dashboard',
                'url': '/api/astrology/admin/dashboard/',
                'method': 'GET',
                'expected_keys': ['overview', 'recent_bookings', 'astrologer_performance']
            },
            {
                'name': 'Astrology Bookings Management',
                'url': '/api/astrology/admin/bookings/',
                'method': 'GET',
                'expected_keys': ['results']
            },
            {
                'name': 'Astrology Reports',
                'url': '/api/astrology/admin/reports/?report_type=summary',
                'method': 'GET',
                'expected_keys': ['data']
            },
            {
                'name': 'Astrologer Management',
                'url': '/api/astrology/admin/astrologers/',
                'method': 'GET',
                'expected_keys': ['results']
            }
        ]
        
        results = []
        for endpoint in endpoints_to_test:
            try:
                if endpoint['method'] == 'GET':
                    response = self.client.get(endpoint['url'])
                elif endpoint['method'] == 'POST':
                    response = self.client.post(endpoint['url'], endpoint.get('data', {}))
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    has_expected_keys = all(key in data.get('data', data) for key in endpoint['expected_keys'])
                    
                    results.append({
                        'endpoint': endpoint['name'],
                        'status': '✅ PASS',
                        'status_code': response.status_code,
                        'has_data': has_expected_keys
                    })
                else:
                    results.append({
                        'endpoint': endpoint['name'],
                        'status': '❌ FAIL',
                        'status_code': response.status_code,
                        'error': response.content.decode()[:200]
                    })
            except Exception as e:
                results.append({
                    'endpoint': endpoint['name'],
                    'status': '❌ ERROR',
                    'error': str(e)
                })
        
        return results
    
    def test_puja_admin_endpoints(self):
        """Test all puja admin endpoints"""
        print("\n🕉️ Testing Puja Admin Endpoints...")
        
        endpoints_to_test = [
            {
                'name': 'Puja Dashboard',
                'url': '/api/puja/admin/dashboard/',
                'method': 'GET',
                'expected_keys': ['overview', 'recent_bookings', 'popular_services']
            },
            {
                'name': 'Puja Bookings Management',
                'url': '/api/puja/admin/bookings/',
                'method': 'GET',
                'expected_keys': ['results']
            },
            {
                'name': 'Puja Reports',
                'url': '/api/puja/admin/reports/?report_type=summary',
                'method': 'GET',
                'expected_keys': ['data']
            },
            {
                'name': 'Puja Service Management',
                'url': '/api/puja/admin/services/',
                'method': 'GET',
                'expected_keys': ['results']
            }
        ]
        
        results = []
        for endpoint in endpoints_to_test:
            try:
                if endpoint['method'] == 'GET':
                    response = self.client.get(endpoint['url'])
                elif endpoint['method'] == 'POST':
                    response = self.client.post(endpoint['url'], endpoint.get('data', {}))
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    has_expected_keys = all(key in data.get('data', data) for key in endpoint['expected_keys'])
                    
                    results.append({
                        'endpoint': endpoint['name'],
                        'status': '✅ PASS',
                        'status_code': response.status_code,
                        'has_data': has_expected_keys
                    })
                else:
                    results.append({
                        'endpoint': endpoint['name'],
                        'status': '❌ FAIL',
                        'status_code': response.status_code,
                        'error': response.content.decode()[:200]
                    })
            except Exception as e:
                results.append({
                    'endpoint': endpoint['name'],
                    'status': '❌ ERROR',
                    'error': str(e)
                })
        
        return results
    
    def test_booking_admin_endpoints(self):
        """Test all booking admin endpoints"""
        print("\n📋 Testing Booking Admin Endpoints...")
        
        endpoints_to_test = [
            {
                'name': 'Booking Dashboard',
                'url': '/api/booking/admin/dashboard/',
                'method': 'GET',
                'expected_keys': ['overview', 'recent_bookings', 'status_distribution']
            },
            {
                'name': 'Booking Management',
                'url': '/api/booking/admin/bookings/',
                'method': 'GET',
                'expected_keys': ['results']
            },
            {
                'name': 'Booking Reports',
                'url': '/api/booking/admin/reports/?report_type=summary',
                'method': 'GET',
                'expected_keys': ['data']
            }
        ]
        
        results = []
        for endpoint in endpoints_to_test:
            try:
                if endpoint['method'] == 'GET':
                    response = self.client.get(endpoint['url'])
                elif endpoint['method'] == 'POST':
                    response = self.client.post(endpoint['url'], endpoint.get('data', {}))
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    has_expected_keys = all(key in data.get('data', data) for key in endpoint['expected_keys'])
                    
                    results.append({
                        'endpoint': endpoint['name'],
                        'status': '✅ PASS',
                        'status_code': response.status_code,
                        'has_data': has_expected_keys
                    })
                else:
                    results.append({
                        'endpoint': endpoint['name'],
                        'status': '❌ FAIL',
                        'status_code': response.status_code,
                        'error': response.content.decode()[:200]
                    })
            except Exception as e:
                results.append({
                    'endpoint': endpoint['name'],
                    'status': '❌ ERROR',
                    'error': str(e)
                })
        
        return results
    
    def test_bulk_operations(self):
        """Test bulk operations across all systems"""
        print("\n⚡ Testing Bulk Operations...")
        
        # Get some booking IDs for testing
        astrology_bookings = list(AstrologyBooking.objects.values_list('id', flat=True)[:2])
        puja_bookings = list(PujaBooking.objects.values_list('id', flat=True)[:2])
        booking_bookings = list(Booking.objects.values_list('id', flat=True)[:2])
        
        bulk_operations = []
        
        # Test Astrology bulk operations
        if astrology_bookings:
            bulk_operations.append({
                'name': 'Astrology Bulk Confirm',
                'url': '/api/astrology/admin/bulk-actions/',
                'data': {
                    'booking_ids': astrology_bookings,
                    'action': 'confirm_bookings'
                }
            })
        
        # Test Puja bulk operations
        if puja_bookings:
            bulk_operations.append({
                'name': 'Puja Bulk Confirm',
                'url': '/api/puja/admin/bookings/bulk-actions/',
                'data': {
                    'booking_ids': puja_bookings,
                    'action': 'confirm_bookings'
                }
            })
        
        # Test Booking bulk operations
        if booking_bookings:
            bulk_operations.append({
                'name': 'Booking Bulk Confirm',
                'url': '/api/booking/admin/bookings/bulk-actions/',
                'data': {
                    'booking_ids': booking_bookings,
                    'action': 'confirm_bookings'
                }
            })
        
        results = []
        for operation in bulk_operations:
            try:
                response = self.client.post(operation['url'], operation['data'], format='json')
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    results.append({
                        'operation': operation['name'],
                        'status': '✅ PASS',
                        'processed': data.get('processed', 0),
                        'failed': data.get('failed', 0)
                    })
                else:
                    results.append({
                        'operation': operation['name'],
                        'status': '❌ FAIL',
                        'status_code': response.status_code,
                        'error': response.content.decode()[:200]
                    })
            except Exception as e:
                results.append({
                    'operation': operation['name'],
                    'status': '❌ ERROR',
                    'error': str(e)
                })
        
        return results
    
    def test_notifications(self):
        """Test notification systems"""
        print("\n📧 Testing Notification Systems...")
        
        # Get test booking IDs
        astrology_booking = AstrologyBooking.objects.first()
        puja_booking = PujaBooking.objects.first()
        booking_booking = Booking.objects.first()
        
        notifications = []
        
        if astrology_booking:
            notifications.append({
                'name': 'Astrology Manual Notification',
                'url': '/api/astrology/admin/notifications/send-manual/',
                'data': {
                    'booking_id': astrology_booking.id,
                    'message_type': 'reminder',
                    'custom_message': 'This is a test notification'
                }
            })
        
        if puja_booking:
            notifications.append({
                'name': 'Puja Manual Notification',
                'url': '/api/puja/admin/notifications/send-manual/',
                'data': {
                    'booking_id': puja_booking.id,
                    'message_type': 'reminder',
                    'custom_message': 'This is a test notification'
                }
            })
        
        if booking_booking:
            notifications.append({
                'name': 'Booking Manual Notification',
                'url': '/api/booking/admin/notifications/send-manual/',
                'data': {
                    'booking_id': booking_booking.id,
                    'message_type': 'reminder',
                    'custom_message': 'This is a test notification'
                }
            })
        
        results = []
        for notification in notifications:
            try:
                response = self.client.post(notification['url'], notification['data'], format='json')
                
                if response.status_code in [200, 201]:
                    results.append({
                        'notification': notification['name'],
                        'status': '✅ PASS',
                        'message': 'Notification sent successfully'
                    })
                else:
                    results.append({
                        'notification': notification['name'],
                        'status': '❌ FAIL',
                        'status_code': response.status_code,
                        'error': response.content.decode()[:200]
                    })
            except Exception as e:
                results.append({
                    'notification': notification['name'],
                    'status': '❌ ERROR',
                    'error': str(e)
                })
        
        return results
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Admin System Tests")
        print("=" * 60)
        
        # Test all systems
        astrology_results = self.test_astrology_admin_endpoints()
        puja_results = self.test_puja_admin_endpoints()
        booking_results = self.test_booking_admin_endpoints()
        bulk_results = self.test_bulk_operations()
        notification_results = self.test_notifications()
        
        # Print comprehensive results
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        all_results = {
            "Astrology Admin": astrology_results,
            "Puja Admin": puja_results,
            "Booking Admin": booking_results,
            "Bulk Operations": bulk_results,
            "Notifications": notification_results
        }
        
        total_tests = 0
        total_passed = 0
        
        for category, results in all_results.items():
            print(f"\n🔸 {category}:")
            print("-" * 40)
            
            for result in results:
                total_tests += 1
                status = result.get('status', '❓ UNKNOWN')
                if '✅' in status:
                    total_passed += 1
                
                if 'endpoint' in result:
                    print(f"  {result['endpoint']}: {status}")
                elif 'operation' in result:
                    print(f"  {result['operation']}: {status}")
                elif 'notification' in result:
                    print(f"  {result['notification']}: {status}")
                
                # Print additional details if available
                if 'error' in result:
                    print(f"    Error: {result['error'][:100]}...")
                if 'processed' in result:
                    print(f"    Processed: {result['processed']}, Failed: {result.get('failed', 0)}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📈 FINAL SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {(total_passed / total_tests * 100):.1f}%")
        
        if total_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            print("✅ All admin systems are working correctly!")
        else:
            print(f"\n⚠️  {total_tests - total_passed} tests failed. Please check the errors above.")
        
        print("\n" + "=" * 60)
        print("🏁 Test execution completed!")
        
        return {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'success_rate': (total_passed / total_tests * 100),
            'details': all_results
        }

def main():
    """Main function to run the comprehensive test"""
    try:
        tester = ComprehensiveAdminTest()
        results = tester.run_all_tests()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"admin_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Test results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
