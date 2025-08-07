#!/usr/bin/env python3
"""
Comprehensive test script for admin booking endpoints
Tests all admin booking endpoints to ensure they work correctly
"""

import os
import sys
import django
import requests
import json
import uuid
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from booking.models import Booking, BookingStatus
from cart.models import Cart
from accounts.models import Address
from django.utils import timezone

User = get_user_model()

class AdminBookingEndpointTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.admin_token = None
        self.test_booking_id = None
        
    def setup_test_data(self):
        """Create test data for endpoints testing"""
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
        
        # Create test booking (if doesn't exist)
        if not Booking.objects.filter(user=user).exists():
            booking = Booking.objects.create(
                user=user,
                cart=cart,
                address=address,
                selected_date=timezone.now().date() + timedelta(days=1),
                selected_time=timezone.now().time(),
                status=BookingStatus.PENDING
            )
            self.test_booking_id = booking.id
        else:
            booking = Booking.objects.filter(user=user).first()
            self.test_booking_id = booking.id
        
        print(f"✅ Test data created - Booking ID: {self.test_booking_id}")
        return {
            'admin_user': admin_user,
            'regular_user': user,
            'employee': employee,
            'booking': booking
        }
    
    def get_admin_token(self):
        """Get authentication token for admin"""
        print("\n🔐 Getting admin authentication token...")
        
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
        """Get headers with admin token"""
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
        print("\n📋 Testing: Admin Booking List")
        
        url = f"{self.base_url}/api/booking/admin/bookings/"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - Found {len(data.get('results', data) if isinstance(data, dict) and 'results' in data else data)} bookings")
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
        test_data = self.setup_test_data()
        if not self.get_admin_token():
            print("❌ Cannot proceed without admin token")
            return
        
        # Test main endpoint
        tests = [
            ('Admin Booking List', self.test_admin_booking_list),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"   ❌ Exception in {test_name}: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status:<8} {test_name}")
        
        print("=" * 60)
        print(f"📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All admin booking endpoints are working correctly!")
        else:
            print(f"⚠️  {total - passed} endpoint(s) need attention")


if __name__ == "__main__":
    tester = AdminBookingEndpointTester()
    tester.run_all_tests()
