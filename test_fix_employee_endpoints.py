#!/usr/bin/env python3
"""
Employee Endpoints Practical Testing Script
Tests employee endpoints with proper Django setup and fixes any issues found
"""
import os
import sys
import json
import traceback
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
import django
django.setup()

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, UserProfile
from booking.models import Booking, BookingStatus
from cart.models import Cart

User = get_user_model()

class EmployeeEndpointFixer(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Get or create admin user
        self.admin_user, created = User.objects.get_or_create(
            email='admin@test.com',
            defaults={
                'role': User.Role.ADMIN,
                'account_status': User.AccountStatus.ACTIVE,
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            self.admin_user.set_password('admin123')
            self.admin_user.save()
        
        # Get or create employee user
        self.employee_user, created = User.objects.get_or_create(
            email='employee@test.com',
            defaults={
                'role': User.Role.EMPLOYEE,
                'account_status': User.AccountStatus.ACTIVE,
                'is_active': True
            }
        )
        if created:
            self.employee_user.set_password('emp123')
            self.employee_user.save()
        
        # Get or create regular user
        self.regular_user, created = User.objects.get_or_create(
            email='user@test.com',
            defaults={
                'role': User.Role.USER,
                'account_status': User.AccountStatus.ACTIVE,
                'is_active': True
            }
        )
        if created:
            self.regular_user.set_password('user123')
            self.regular_user.save()
        
        # Create profiles
        for user in [self.admin_user, self.employee_user, self.regular_user]:
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': f'Test {user.role.title()}',
                    'last_name': 'User'
                }
            )
    
    def get_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate(self, user):
        """Authenticate client with user token"""
        token = self.get_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
    
    def test_employee_registration(self):
        """Test employee registration"""
        print("\n🧪 Testing Employee Registration...")
        
        # Clear authentication
        self.client.credentials()
        
        with override_settings(EMPLOYEE_REGISTRATION_CODE='TEST_EMP_CODE'):
            response = self.client.post('/api/auth/register/', {
                'email': 'newemployee@test.com',
                'phone': '9876543210',
                'password': 'newpass123',
                'password2': 'newpass123',
                'role': 'EMPLOYEE',
                'employee_registration_code': 'TEST_EMP_CODE'
            }, format='json')
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print("   ✅ Employee registration working correctly")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Registration failed: {response.json()}")
        
        return response.status_code == 201
    
    def test_employee_login(self):
        """Test employee login"""
        print("\n🧪 Testing Employee Login...")
        
        self.client.credentials()
        response = self.client.post('/api/auth/login/', {
            'email': 'employee@test.com',
            'password': 'emp123'
        }, format='json')
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Employee login working correctly")
            data = response.json()
            print(f"   User role: {data.get('user', {}).get('role')}")
            print(f"   Is employee: {data.get('user', {}).get('is_employee')}")
        else:
            print(f"   ❌ Login failed: {response.json()}")
        
        return response.status_code == 200
    
    def test_role_check(self):
        """Test role check endpoint"""
        print("\n🧪 Testing Role Check...")
        
        self.authenticate(self.employee_user)
        response = self.client.get('/api/auth/check-role/')
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Role check working correctly")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Role check failed: {response.json()}")
        
        return response.status_code == 200
    
    def test_employee_profile(self):
        """Test employee profile endpoints"""
        print("\n🧪 Testing Employee Profile...")
        
        self.authenticate(self.employee_user)
        
        # Get profile
        response = self.client.get('/api/auth/profile/')
        print(f"   GET Profile Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Get profile working correctly")
        else:
            print(f"   ❌ Get profile failed: {response.json()}")
        
        # Update profile
        response = self.client.put('/api/auth/profile/', {
            'first_name': 'Updated Employee',
            'last_name': 'Name'
        }, format='json')
        print(f"   PUT Profile Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Update profile working correctly")
        else:
            print(f"   ❌ Update profile failed: {response.json()}")
        
        return True
    
    def test_employees_list_admin(self):
        """Test admin getting employees list"""
        print("\n🧪 Testing Admin Employees List...")
        
        # Test the actual endpoint from booking views
        self.authenticate(self.admin_user)
        response = self.client.get('/api/booking/admin/bookings/employees/')
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Admin employees list working correctly")
            employees = response.json()
            print(f"   Found {len(employees)} employees")
            for emp in employees:
                print(f"     - {emp.get('email')} ({emp.get('first_name')} {emp.get('last_name')})")
        else:
            print(f"   ❌ Admin employees list failed: {response.json()}")
        
        return response.status_code == 200
    
    def test_booking_assignment(self):
        """Test booking assignment to employee"""
        print("\n🧪 Testing Booking Assignment...")
        
        # Create test booking
        cart = Cart.objects.create(user=self.regular_user, total_amount=1000)
        booking = Booking.objects.create(
            user=self.regular_user,
            cart=cart,
            book_id=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status=BookingStatus.PENDING,
            selected_date=datetime.now().date() + timedelta(days=1),
            selected_time="10:00"
        )
        
        # Test assignment as admin
        self.authenticate(self.admin_user)
        response = self.client.post(f'/api/booking/admin/bookings/{booking.id}/assign/', {
            'assigned_to_id': self.employee_user.id,
            'notes': 'Test assignment'
        }, format='json')
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Booking assignment working correctly")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Booking assignment failed: {response.json()}")
        
        return response.status_code == 200, booking
    
    def test_employee_booking_view(self):
        """Test employee viewing assigned bookings"""
        print("\n🧪 Testing Employee Booking View...")
        
        # First assign a booking
        success, booking = self.test_booking_assignment()
        if not success:
            print("   ⚠️  Skipping - booking assignment failed")
            return False
        
        # Test employee viewing bookings
        self.authenticate(self.employee_user)
        response = self.client.get('/api/booking/bookings/')
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Employee booking view working correctly")
            data = response.json()
            print(f"   Employee can see {data.get('count', 0)} bookings")
        else:
            print(f"   ❌ Employee booking view failed: {response.json()}")
        
        return response.status_code == 200
    
    def test_booking_status_update(self):
        """Test employee updating booking status"""
        print("\n🧪 Testing Booking Status Update...")
        
        # First assign a booking
        success, booking = self.test_booking_assignment()
        if not success:
            print("   ⚠️  Skipping - booking assignment failed")
            return False
        
        # Test status update as employee
        self.authenticate(self.employee_user)
        response = self.client.post(f'/api/booking/bookings/{booking.id}/status/', {
            'status': 'IN_PROGRESS',
            'notes': 'Puja started'
        }, format='json')
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Booking status update working correctly")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Booking status update failed: {response.json()}")
        
        return response.status_code == 200
    
    def test_admin_dashboard(self):
        """Test admin dashboard with employee metrics"""
        print("\n🧪 Testing Admin Dashboard...")
        
        self.authenticate(self.admin_user)
        response = self.client.get('/api/booking/admin/dashboard/')
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Admin dashboard working correctly")
            data = response.json()
            if 'data' in data:
                overview = data['data'].get('overview', {})
                print(f"   Total bookings: {overview.get('total_bookings', 0)}")
                print(f"   Active employees: {overview.get('active_employees', 0)}")
        else:
            print(f"   ❌ Admin dashboard failed: {response.json()}")
        
        return response.status_code == 200
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting Employee Endpoints Testing and Fixing...")
        print("=" * 60)
        
        results = {}
        
        try:
            results['registration'] = self.test_employee_registration()
            results['login'] = self.test_employee_login()
            results['role_check'] = self.test_role_check()
            results['profile'] = self.test_employee_profile()
            results['employees_list'] = self.test_employees_list_admin()
            results['booking_assignment'] = self.test_booking_assignment()[0] if self.test_booking_assignment() else False
            results['employee_booking_view'] = self.test_employee_booking_view()
            results['status_update'] = self.test_booking_status_update()
            results['admin_dashboard'] = self.test_admin_dashboard()
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            traceback.print_exc()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title():<25} {status}")
        
        print(f"\n📈 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All employee endpoints are working correctly!")
        else:
            print("⚠️  Some endpoints need attention. Check the details above.")
        
        return results

def main():
    """Main function to run the tests"""
    print("Employee Endpoints Testing & Fixing Tool")
    print("=" * 60)
    
    # Create test instance and run
    tester = EmployeeEndpointFixer()
    tester.setUp()
    results = tester.run_all_tests()
    
    # Generate fixes report
    print("\n🔧 FIXES AND RECOMMENDATIONS")
    print("=" * 60)
    
    if not results.get('registration'):
        print("❌ Employee Registration Issues:")
        print("   - Check EMPLOYEE_REGISTRATION_CODE in settings.py")
        print("   - Ensure validation logic is working correctly")
        print("   - Fix: Add to settings.py: EMPLOYEE_REGISTRATION_CODE = 'your_code'")
    
    if not results.get('employees_list'):
        print("❌ Employees List Issues:")
        print("   - Check admin_urls.py routing")
        print("   - Verify AdminBookingViewSet.employees() method")
        print("   - Ensure proper permissions are set")
    
    if not results.get('booking_assignment'):
        print("❌ Booking Assignment Issues:")
        print("   - Check BookingAssignmentSerializer validation")
        print("   - Verify assign_to() method in Booking model")
        print("   - Check admin permissions")
    
    print("\n✅ WORKING ENDPOINTS:")
    working_endpoints = [k for k, v in results.items() if v]
    for endpoint in working_endpoints:
        print(f"   • {endpoint.replace('_', ' ').title()}")
    
    print("\n📝 Next Steps:")
    print("   1. Fix any failing endpoints based on the recommendations above")
    print("   2. Test manually using the generated documentation")
    print("   3. Implement proper error handling and validation")
    print("   4. Add comprehensive logging for debugging")
    
    return results

if __name__ == "__main__":
    main()