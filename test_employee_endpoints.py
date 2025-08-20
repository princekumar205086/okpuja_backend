#!/usr/bin/env python3
"""
Comprehensive Employee Endpoints Testing Script
Tests all employee-related endpoints and generates documentation
"""
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Add Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

# Setup Django
import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, UserProfile
from booking.models import Booking, BookingStatus
from cart.models import Cart

User = get_user_model()

class EmployeeEndpointTester:
    def __init__(self):
        self.client = APIClient()
        self.base_url = "http://localhost:8000/api"
        self.endpoints_data = []
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test users and data"""
        print("Setting up test data...")
        
        # Create admin user
        self.admin_user, created = User.objects.get_or_create(
            email='admin@test.com',
            defaults={
                'username': 'admin',
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
        
        # Create employee user
        self.employee_user, created = User.objects.get_or_create(
            email='employee@test.com',
            defaults={
                'username': 'employee',
                'role': User.Role.EMPLOYEE,
                'account_status': User.AccountStatus.ACTIVE,
                'is_active': True
            }
        )
        if created:
            self.employee_user.set_password('emp123')
            self.employee_user.save()
        
        # Create regular user
        self.regular_user, created = User.objects.get_or_create(
            email='user@test.com',
            defaults={
                'username': 'user',
                'role': User.Role.USER,
                'account_status': User.AccountStatus.ACTIVE,
                'is_active': True
            }
        )
        if created:
            self.regular_user.set_password('user123')
            self.regular_user.save()
        
        # Create user profiles
        for user in [self.admin_user, self.employee_user, self.regular_user]:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': f'Test {user.role}',
                    'last_name': 'User'
                }
            )
        
        print("Test data setup complete!")
    
    def get_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate(self, user):
        """Authenticate client with user token"""
        token = self.get_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
    
    def log_endpoint(self, method, endpoint, description, auth_required=True, 
                    admin_only=False, payload=None, response_example=None, status_code=200):
        """Log endpoint information for documentation"""
        self.endpoints_data.append({
            'method': method,
            'endpoint': endpoint,
            'description': description,
            'auth_required': auth_required,
            'admin_only': admin_only,
            'payload': payload,
            'response_example': response_example,
            'status_code': status_code
        })
    
    def test_employee_registration(self):
        """Test employee registration endpoint"""
        print("\n=== Testing Employee Registration ===")
        
        endpoint = "/auth/register/"
        payload = {
            "email": "newemployee@test.com",
            "phone": "9876543210",
            "password": "newpass123",
            "password2": "newpass123",
            "role": "EMPLOYEE",
            "employee_registration_code": "EMP_REG_CODE_2024"  # This needs to be set in settings
        }
        
        self.client.credentials()  # Clear auth
        response = self.client.post(f"{self.base_url}{endpoint}", payload, format='json')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.content else 'No content'}")
        
        self.log_endpoint(
            method="POST",
            endpoint=endpoint,
            description="Register a new employee/priest account",
            auth_required=False,
            payload=payload,
            response_example=response.json() if response.content else None,
            status_code=response.status_code
        )
    
    def test_get_employees_list(self):
        """Test get list of employees endpoint"""
        print("\n=== Testing Get Employees List ===")
        
        # Test as admin
        self.authenticate(self.admin_user)
        endpoint = "/booking/admin/bookings/employees/"
        
        response = self.client.get(f"{self.base_url}{endpoint}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.content else 'No content'}")
        
        self.log_endpoint(
            method="GET",
            endpoint=endpoint,
            description="Get list of employees that can be assigned to bookings",
            auth_required=True,
            admin_only=True,
            response_example=response.json() if response.content else None,
            status_code=response.status_code
        )
    
    def test_assign_booking_to_employee(self):
        """Test assign booking to employee endpoint"""
        print("\n=== Testing Assign Booking to Employee ===")
        
        # First create a test booking
        cart = Cart.objects.create(user=self.regular_user, total_amount=1000)
        booking = Booking.objects.create(
            user=self.regular_user,
            cart=cart,
            book_id=f"BOOK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status=BookingStatus.PENDING,
            selected_date=datetime.now().date() + timedelta(days=1),
            selected_time="10:00"
        )
        
        # Test as admin
        self.authenticate(self.admin_user)
        endpoint = f"/booking/admin/bookings/{booking.id}/assign/"
        payload = {
            "assigned_to_id": self.employee_user.id,
            "notes": "Assigned to experienced priest for Ganesh Puja"
        }
        
        response = self.client.post(f"{self.base_url}{endpoint}", payload, format='json')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.content else 'No content'}")
        
        self.log_endpoint(
            method="POST",
            endpoint=f"/booking/admin/bookings/{{booking_id}}/assign/",
            description="Assign a booking to an employee/priest",
            auth_required=True,
            admin_only=True,
            payload=payload,
            response_example=response.json() if response.content else None,
            status_code=response.status_code
        )
    
    def test_employee_bookings_view(self):
        """Test employee viewing their assigned bookings"""
        print("\n=== Testing Employee Bookings View ===")
        
        # Test as employee
        self.authenticate(self.employee_user)
        endpoint = "/booking/bookings/"
        
        response = self.client.get(f"{self.base_url}{endpoint}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.content else 'No content'}")
        
        self.log_endpoint(
            method="GET",
            endpoint=endpoint,
            description="Employee view their assigned bookings (plus their own bookings)",
            auth_required=True,
            admin_only=False,
            response_example=response.json() if response.content else None,
            status_code=response.status_code
        )
    
    def test_user_role_check(self):
        """Test user role check endpoint"""
        print("\n=== Testing User Role Check ===")
        
        # Test as employee
        self.authenticate(self.employee_user)
        endpoint = "/auth/check-role/"
        
        response = self.client.get(f"{self.base_url}{endpoint}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.content else 'No content'}")
        
        self.log_endpoint(
            method="GET",
            endpoint=endpoint,
            description="Check current user's role and permissions",
            auth_required=True,
            admin_only=False,
            response_example=response.json() if response.content else None,
            status_code=response.status_code
        )
    
    def test_admin_booking_dashboard(self):
        """Test admin booking dashboard with employee metrics"""
        print("\n=== Testing Admin Booking Dashboard ===")
        
        # Test as admin
        self.authenticate(self.admin_user)
        endpoint = "/booking/admin/dashboard/"
        
        response = self.client.get(f"{self.base_url}{endpoint}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.content else 'No content'}")
        
        self.log_endpoint(
            method="GET",
            endpoint=endpoint,
            description="Admin dashboard with booking analytics including employee metrics",
            auth_required=True,
            admin_only=True,
            response_example=response.json() if response.content else None,
            status_code=response.status_code
        )
    
    def test_admin_users_list(self):
        """Test admin users list including employees"""
        print("\n=== Testing Admin Users List ===")
        
        # Test as admin
        self.authenticate(self.admin_user)
        endpoint = "/auth/users/"
        
        response = self.client.get(f"{self.base_url}{endpoint}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.content else 'No content'}")
        
        # Test with role filter
        response_filtered = self.client.get(f"{self.base_url}{endpoint}?role=EMPLOYEE")
        
        print(f"Filtered Response: {response_filtered.json() if response_filtered.content else 'No content'}")
        
        self.log_endpoint(
            method="GET",
            endpoint=endpoint,
            description="List all users (can filter by role=EMPLOYEE to get only employees)",
            auth_required=True,
            admin_only=True,
            response_example=response.json() if response.content else None,
            status_code=response.status_code
        )
    
    def run_all_tests(self):
        """Run all employee endpoint tests"""
        print("Starting Employee Endpoints Testing...")
        
        try:
            self.test_employee_registration()
            self.test_get_employees_list()
            self.test_assign_booking_to_employee()
            self.test_employee_bookings_view()
            self.test_user_role_check()
            self.test_admin_booking_dashboard()
            self.test_admin_users_list()
        except Exception as e:
            print(f"Error during testing: {e}")
            import traceback
            traceback.print_exc()
        
        self.generate_documentation()
    
    def generate_documentation(self):
        """Generate markdown documentation"""
        print("\n=== Generating Documentation ===")
        
        markdown_content = """# Employee Endpoints API Documentation

## Overview
This document provides comprehensive documentation for all employee-related endpoints in the OKPUJA API system.

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Employee Roles
- **USER**: Regular customer
- **EMPLOYEE**: Priest/Service provider who can be assigned to bookings
- **ADMIN**: Administrator with full access

## Endpoints

"""
        
        for endpoint_data in self.endpoints_data:
            markdown_content += f"""### {endpoint_data['method']} {endpoint_data['endpoint']}

**Description**: {endpoint_data['description']}

**Authentication Required**: {'Yes' if endpoint_data['auth_required'] else 'No'}
**Admin Only**: {'Yes' if endpoint_data['admin_only'] else 'No'}

"""
            
            if endpoint_data['payload']:
                markdown_content += f"""**Request Payload Example**:
```json
{json.dumps(endpoint_data['payload'], indent=2)}
```

"""
            
            if endpoint_data['response_example']:
                markdown_content += f"""**Response Example** (Status: {endpoint_data['status_code']}):
```json
{json.dumps(endpoint_data['response_example'], indent=2)}
```

"""
            
            markdown_content += "---\n\n"
        
        # Additional documentation sections
        markdown_content += """## Error Responses

Common error response format:
```json
{
  "error": "Error message description",
  "detail": "Detailed error information"
}
```

### HTTP Status Codes
- **200**: Success
- **201**: Created successfully
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **500**: Internal Server Error

## Employee Registration Process

1. Employee obtains registration code from admin
2. Employee uses registration endpoint with code
3. Admin can view and manage employees
4. Admin assigns bookings to employees
5. Employees view and manage assigned bookings

## Booking Assignment Workflow

1. Admin views unassigned bookings
2. Admin gets list of available employees
3. Admin assigns booking to specific employee
4. Employee receives notification (if configured)
5. Employee manages assigned booking through their booking list

## Employee Permissions

**Employees can**:
- View their own bookings
- View bookings assigned to them
- Update status of assigned bookings
- Access their profile and settings

**Employees cannot**:
- View other employees' bookings
- Access admin-only endpoints
- Assign/reassign bookings
- Access full user management

## Testing Notes

To test these endpoints:

1. **Start the Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Register as employee** (requires valid registration code)
3. **Login to get JWT token**
4. **Use token in Authorization header for protected endpoints**

## Configuration Required

In `settings.py`, set:
```python
EMPLOYEE_REGISTRATION_CODE = "your_secret_code_here"
```

This code is required for employee registration.
"""
        
        # Write documentation to file
        doc_file = "EMPLOYEE_ENDPOINTS_DOCUMENTATION.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Documentation generated: {doc_file}")
        return markdown_content

if __name__ == "__main__":
    tester = EmployeeEndpointTester()
    tester.run_all_tests()