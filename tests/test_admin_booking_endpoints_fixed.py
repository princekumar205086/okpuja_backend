#!/usr/bin/env python
import os
import sys
import django
import requests
import json
import uuid
from datetime import datetime, timedelta

# Add Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
django.setup()

from django.utils import timezone
from accounts.models import User, UserProfile, Address
from booking.models import Booking
from cart.models import Cart
from puja.models import PujaService, PujaCategory

class AdminBookingEndpointTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.admin_token = None
        self.test_booking_id = None

    def setup_test_data(self):
        """Create test data for booking endpoints"""
        print("📋 Setting up test data...")
        
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@okpuja.com',
            defaults={
                'password': 'admin@123',
                'role': 'ADMIN',
                'account_status': 'ACTIVE',
                'phone': '+919999999999'
            }
        )
        if created:
            admin_user.set_password('admin@123')
            admin_user.save()
            # Create profile for admin
            from accounts.models import UserProfile
            UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'first_name': 'Admin',
                    'last_name': 'User'
                }
            )
        
        # Create regular user
        user, created = User.objects.get_or_create(
            email='user@test.com',
            defaults={
                'password': 'user123',
                'role': 'USER',
                'account_status': 'ACTIVE',
                'phone': '+919999999998'
            }
        )
        if created:
            user.set_password('user123')
            user.save()
            # Create profile for user
            from accounts.models import UserProfile
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            
        # Create employee user
        employee, created = User.objects.get_or_create(
            email='employee@okpuja.com',
            defaults={
                'password': 'emp123',
                'role': 'EMPLOYEE',
                'account_status': 'ACTIVE',
                'phone': '+919999999997'
            }
        )
        if created:
            employee.set_password('emp123')
            employee.save()
            # Create profile for employee
            from accounts.models import UserProfile
            UserProfile.objects.get_or_create(
                user=employee,
                defaults={
                    'first_name': 'Employee',
                    'last_name': 'User'
                }
            )
        
        # Create address
        address, created = Address.objects.get_or_create(
            user=user,
            defaults={
                'address_line1': '123 Test Street',
                'address_line2': 'Apt 1',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India',
                'is_default': True
            }
        )
        
        # Create cart (if doesn't exist)
        if not Cart.objects.filter(user=user).exists():
            from puja.models import PujaService, PujaCategory
            
            # Create a category and service for testing
            category, created = PujaCategory.objects.get_or_create(
                name='Test Category'
            )
            
            service, created = PujaService.objects.get_or_create(
                title='Test Service',
                defaults={
                    'image': 'https://example.com/test.jpg',
                    'description': 'Test service for booking',
                    'category': category,
                    'type': 'HOME',
                    'duration_minutes': 60
                }
            )
            
            cart = Cart.objects.create(
                user=user,
                service_type='PUJA',
                puja_service=service,
                selected_date=timezone.now().date() + timedelta(days=1),
                selected_time='10:00:00',
                cart_id=f'cart_{uuid.uuid4().hex[:8]}',
                status='ACTIVE'
            )
        else:
            cart = Cart.objects.filter(user=user).first()
        
        # Create booking (if doesn't exist)
        if not Booking.objects.filter(cart=cart).exists():
            booking = Booking.objects.create(
                user=user,
                cart=cart,
                selected_date=timezone.now().date() + timedelta(days=1),
                selected_time=timezone.now().time(),
                address=address,
                status='PENDING'
            )
            self.test_booking_id = booking.id
            print(f"✅ Test data created - Booking ID: {booking.id}")
        else:
            booking = Booking.objects.filter(cart=cart).first()
            self.test_booking_id = booking.id
            print(f"✅ Test data found - Booking ID: {booking.id}")
        
        return {
            'admin_user': admin_user,
            'user': user,
            'employee': employee,
            'booking': booking
        }
    
    def get_admin_token(self):
        """Get authentication token for admin"""
        print("\\n🔐 Getting admin authentication token...")
        
        url = f"{self.base_url}/api/auth/login/"
        data = {
            'email': 'admin@okpuja.com',
            'password': 'admin@123'
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data['access']
                print("✅ Admin token obtained successfully")
                return True
            else:
                print(f"❌ Failed to get admin token: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error getting admin token: {e}")
            return False
    
    def get_headers(self):
        """Get headers with authorization token"""
        return {
            'Authorization': f'Bearer {self.admin_token}',
            'Content-Type': 'application/json'
        }
    
    def get_form_headers(self):
        """Get headers for form data requests"""
        return {
            'Authorization': f'Bearer {self.admin_token}'
            # Don't set Content-Type, let requests handle it for form data
        }

    def test_admin_booking_list(self):
        """Test: GET /api/booking/admin/bookings/ - List all bookings"""
        print("\\n📋 Testing: Admin Booking List")
        
        url = f"{self.base_url}/api/booking/admin/bookings/"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Handle both paginated and non-paginated responses
                if isinstance(data, dict) and 'results' in data:
                    count = data.get('count', len(data['results']))
                elif isinstance(data, list):
                    count = len(data)
                else:
                    count = data.get('count', 1)
                print(f"   ✅ Success - Found {count} bookings")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def test_admin_booking_detail(self):
        """Test: GET /api/booking/admin/bookings/{id}/ - Get booking details"""
        print("\\n📋 Testing: Admin Booking Detail")
        
        if not self.test_booking_id:
            print("   ⚠️ No test booking ID available")
            return False
            
        url = f"{self.base_url}/api/booking/admin/bookings/{self.test_booking_id}/"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - Booking ID: {data.get('book_id', 'N/A')}")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_admin_booking_update_status(self):
        """Test: POST/PATCH /api/booking/admin/bookings/{id}/status/ - Update booking status"""
        print("\\n📋 Testing: Admin Booking Status Update")
        
        if not self.test_booking_id:
            print("   ⚠️ No test booking ID available")
            return False
            
        url = f"{self.base_url}/api/booking/admin/bookings/{self.test_booking_id}/status/"
        data = {
            'status': 'CONFIRMED'
        }
        
        try:
            # Use JSON for these endpoints now that we added JSONParser
            response = requests.post(url, headers=self.get_headers(), json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   ✅ Success - Status updated to: {response_data.get('status', 'N/A')}")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_admin_booking_reschedule(self):
        """Test: POST /api/booking/admin/bookings/{id}/reschedule/ - Reschedule booking"""
        print("\\n📋 Testing: Admin Booking Reschedule")
        
        if not self.test_booking_id:
            print("   ⚠️ No test booking ID available")
            return False
            
        url = f"{self.base_url}/api/booking/admin/bookings/{self.test_booking_id}/reschedule/"
        data = {
            'selected_date': (timezone.now().date() + timedelta(days=2)).isoformat(),
            'selected_time': '14:00:00',
            'reason': 'Test reschedule by admin'
        }
        
        try:
            # Use JSON for these endpoints now that we added JSONParser
            response = requests.post(url, headers=self.get_headers(), json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   ✅ Success - Booking rescheduled")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_admin_booking_assign(self):
        """Test: POST /api/booking/admin/bookings/{id}/assign/ - Assign booking to employee"""
        print("\\n📋 Testing: Admin Booking Assignment")
        
        if not self.test_booking_id:
            print("   ⚠️ No test booking ID available")
            return False
        
        # Get employee ID
        try:
            employee = User.objects.filter(email='employee@okpuja.com').first()
            if not employee:
                print("   ⚠️ No employee user found")
                return False
                
            url = f"{self.base_url}/api/booking/admin/bookings/{self.test_booking_id}/assign/"
            data = {
                'assigned_to_id': employee.id,
                'notes': 'Test assignment by admin'
            }
            
            # Use JSON for these endpoints now that we added JSONParser
            response = requests.post(url, headers=self.get_headers(), json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   ✅ Success - Booking assigned")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def test_admin_employees_list(self):
        """Test: GET /api/booking/admin/bookings/employees/ - Get employees list"""
        print("\\n📋 Testing: Admin Employees List")
        
        url = f"{self.base_url}/api/booking/admin/bookings/employees/"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', 0)
                print(f"   ✅ Success - Found {count} employees")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def test_admin_dashboard_stats(self):
        """Test: GET /api/booking/admin/bookings/dashboard_stats/ - Get dashboard statistics"""
        print("\\n📋 Testing: Admin Dashboard Stats")
        
        url = f"{self.base_url}/api/booking/admin/bookings/dashboard_stats/"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - Stats: {data.get('total_bookings', 0)} total bookings")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_admin_booking_update(self):
        """Test: PUT/PATCH /api/booking/admin/bookings/{id}/ - Update booking details"""
        print("\\n📋 Testing: Admin Booking Update")
        
        if not self.test_booking_id:
            print("   ⚠️ No test booking ID available")
            return False
            
        url = f"{self.base_url}/api/booking/admin/bookings/{self.test_booking_id}/"
        data = {
            'selected_time': '15:30:00'
        }
        
        try:
            # Use JSON for these endpoints now that we added JSONParser
            response = requests.patch(url, headers=self.get_headers(), json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   ✅ Success - Booking updated")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all admin booking endpoint tests"""
        print("🚀 Starting Admin Booking Endpoints Testing")
        print("=" * 60)
        
        # Setup
        try:
            test_data = self.setup_test_data()
        except Exception as e:
            print(f"❌ Failed to setup test data: {e}")
            return
        
        # Get admin token
        if not self.get_admin_token():
            print("❌ Cannot proceed without admin token")
            return
        
        # Run tests
        tests = [
            ('Admin Booking List', self.test_admin_booking_list),
            ('Admin Booking Detail', self.test_admin_booking_detail),
            ('Admin Booking Status Update', self.test_admin_booking_update_status),
            ('Admin Booking Reschedule', self.test_admin_booking_reschedule),
            ('Admin Booking Assignment', self.test_admin_booking_assign),
            ('Admin Employees List', self.test_admin_employees_list),
            ('Admin Dashboard Stats', self.test_admin_dashboard_stats),
            ('Admin Booking Update', self.test_admin_booking_update),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results[test_name] = False
        
        # Print summary
        print("\\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, passed_test in results.items():
            if passed_test:
                print(f"✅ PASS   {test_name}")
                passed += 1
            else:
                print(f"❌ FAIL   {test_name}")
                failed += 1
        
        total = passed + failed
        percentage = (passed / total * 100) if total > 0 else 0
        
        print("=" * 60)
        print(f"📈 Overall: {passed}/{total} tests passed ({percentage:.1f}%)")
        if failed > 0:
            print(f"⚠️  {failed} endpoint(s) need attention")

if __name__ == '__main__':
    tester = AdminBookingEndpointTester()
    tester.run_all_tests()
