#!/usr/bin/env python3
"""
Manual Employee Endpoints Validation Script
Simple script to validate that all employee endpoints are working correctly
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_endpoint(method, endpoint, headers=None, data=None, description=""):
    """Test a single endpoint and return result"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🧪 Testing: {method} {endpoint}")
    if description:
        print(f"   Description: {description}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        else:
            print(f"   ❌ Unsupported method: {method}")
            return False
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code < 400:
            print(f"   ✅ Success")
            if response.content:
                try:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: List with {len(response_data)} items")
                        print(f"   First item: {json.dumps(response_data[0], indent=2)[:200]}...")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    else:
                        print(f"   Response: {str(response_data)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            return True
        else:
            print(f"   ❌ Failed")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def get_jwt_token(email, password):
    """Get JWT token for authentication"""
    response = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": email,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        return data.get('access')
    return None

def main():
    """Main testing function"""
    print("🚀 Employee Endpoints Manual Validation")
    print("=" * 60)
    print("⚠️  Make sure Django server is running on localhost:8000")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Employee Registration
    print("\n📝 1. EMPLOYEE REGISTRATION")
    timestamp = datetime.now().strftime('%H%M%S')
    registration_payload = {
        "email": f"newemployee{timestamp}@test.com",
        "phone": f"98765431{timestamp[-2:]}",  # Unique phone number
        "password": "testpass123",
        "password2": "testpass123",
        "role": "EMPLOYEE",
        "employee_registration_code": "EMP2025OK5"  # From settings
    }
    
    results['registration'] = test_endpoint(
        "POST", "/auth/register/", 
        data=registration_payload,
        description="Register new employee account"
    )
    
    # Test 2: Employee Login
    print("\n🔐 2. EMPLOYEE LOGIN")
    # Try to login with existing employee account
    login_payload = {
        "email": "employee@test.com",
        "password": "emp123"
    }
    
    login_result = test_endpoint(
        "POST", "/auth/login/",
        data=login_payload,
        description="Employee login to get JWT token"
    )
    results['login'] = login_result
    
    # Get token for subsequent tests
    employee_token = get_jwt_token("employee@test.com", "emp123")
    admin_token = get_jwt_token("admin@test.com", "admin123")
    
    if employee_token:
        print(f"   ✅ Employee token obtained")
        employee_headers = {"Authorization": f"Bearer {employee_token}"}
    else:
        print(f"   ❌ Could not get employee token")
        employee_headers = {}
    
    if admin_token:
        print(f"   ✅ Admin token obtained")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
    else:
        print(f"   ❌ Could not get admin token")
        admin_headers = {}
    
    # Test 3: Role Check
    print("\n👤 3. ROLE CHECK")
    results['role_check'] = test_endpoint(
        "GET", "/auth/check-role/",
        headers=employee_headers,
        description="Check employee role and permissions"
    )
    
    # Test 4: Employee Profile
    print("\n📋 4. EMPLOYEE PROFILE")
    results['profile_get'] = test_endpoint(
        "GET", "/auth/profile/",
        headers=employee_headers,
        description="Get employee profile information"
    )
    
    # Test 5: Employee Bookings View
    print("\n📅 5. EMPLOYEE BOOKINGS")
    results['employee_bookings'] = test_endpoint(
        "GET", "/booking/bookings/",
        headers=employee_headers,
        description="Employee view assigned bookings"
    )
    
    # Test 6: Admin - Get Employees List
    print("\n👥 6. ADMIN - EMPLOYEES LIST")
    results['admin_employees'] = test_endpoint(
        "GET", "/booking/admin/bookings/employees/",
        headers=admin_headers,
        description="Admin get list of employees"
    )
    
    # Test 7: Admin - Dashboard
    print("\n📊 7. ADMIN - DASHBOARD")
    results['admin_dashboard'] = test_endpoint(
        "GET", "/booking/admin/dashboard/",
        headers=admin_headers,
        description="Admin dashboard with employee metrics"
    )
    
    # Test 8: Admin - All Bookings
    print("\n📝 8. ADMIN - ALL BOOKINGS")
    results['admin_bookings'] = test_endpoint(
        "GET", "/booking/admin/bookings/",
        headers=admin_headers,
        description="Admin view all bookings"
    )
    
    # Test 9: Admin - Users List
    print("\n👤 9. ADMIN - USERS LIST")
    results['admin_users'] = test_endpoint(
        "GET", "/auth/users/",
        headers=admin_headers,
        description="Admin list all users"
    )
    
    # Test 10: Filter employees only
    print("\n🔍 10. ADMIN - FILTER EMPLOYEES")
    results['filter_employees'] = test_endpoint(
        "GET", "/auth/users/?role=EMPLOYEE",
        headers=admin_headers,
        description="Admin filter users by employee role"
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS SUMMARY")
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
        print("⚠️  Some endpoints need attention.")
        
        # Provide specific fixes
        print("\n🔧 SPECIFIC FIXES NEEDED:")
        
        if not results.get('admin_employees'):
            print("❌ Admin Employees List:")
            print("   • Fixed: Added AdminBookingViewSet to router")
            print("   • Endpoint should now be available at /booking/admin/bookings/employees/")
        
        if not results.get('registration'):
            print("❌ Employee Registration:")
            print("   • Check EMPLOYEE_REGISTRATION_CODE in settings")
            print("   • Current code: EMP2025OK5")
        
        if not results.get('login'):
            print("❌ Employee Login:")
            print("   • Check if employee@test.com user exists")
            print("   • Run: python manage.py shell -> User.objects.filter(email='employee@test.com')")
    
    print("\n📝 NEXT STEPS:")
    print("   1. Fix any failing endpoints based on the errors shown")
    print("   2. Check Django server logs for detailed error messages")
    print("   3. Verify database has proper test data")
    print("   4. Test manually using curl or Postman")
    
    return results

if __name__ == "__main__":
    main()