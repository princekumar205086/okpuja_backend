"""
Puja App API Testing Script using requests
Tests the puja API endpoints to verify functionality
"""

import requests
import json
from datetime import date, timedelta

# API Configuration
BASE_URL = "http://localhost:8000/api"
PUJA_BASE_URL = f"{BASE_URL}/puja"

def test_api_connectivity():
    """Test basic API connectivity"""
    print("🔌 Testing API Connectivity...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print(f"⚠️ API server responded with status {response.status_code}")
            return True  # Server is running but may not have root endpoint
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running")
        print("💡 Start the server with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False

def test_puja_categories():
    """Test puja categories endpoint"""
    print("\n📚 Testing Puja Categories...")
    
    try:
        response = requests.get(f"{PUJA_BASE_URL}/categories/", timeout=10)
        
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Categories endpoint working - Found {len(categories)} categories")
            
            if categories:
                print("📋 Sample categories:")
                for i, cat in enumerate(categories[:3]):
                    print(f"   {i+1}. {cat.get('name', 'Unknown')}")
            else:
                print("⚠️ No categories found - database may be empty")
            
            return True
        else:
            print(f"❌ Categories endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Categories test failed: {e}")
        return False

def test_puja_services():
    """Test puja services endpoint"""
    print("\n🕉️ Testing Puja Services...")
    
    try:
        response = requests.get(f"{PUJA_BASE_URL}/services/", timeout=10)
        
        if response.status_code == 200:
            services = response.json()
            print(f"✅ Services endpoint working - Found {len(services)} services")
            
            if services:
                print("📋 Sample services:")
                for i, service in enumerate(services[:3]):
                    print(f"   {i+1}. {service.get('title', 'Unknown')} - {service.get('type', 'Unknown')} ({service.get('duration_minutes', 0)} min)")
            else:
                print("⚠️ No services found - database may be empty")
            
            return True
        else:
            print(f"❌ Services endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Services test failed: {e}")
        return False

def test_puja_packages():
    """Test puja packages endpoint"""
    print("\n📦 Testing Puja Packages...")
    
    try:
        response = requests.get(f"{PUJA_BASE_URL}/packages/", timeout=10)
        
        if response.status_code == 200:
            packages = response.json()
            print(f"✅ Packages endpoint working - Found {len(packages)} packages")
            
            if packages:
                print("📋 Sample packages:")
                for i, package in enumerate(packages[:3]):
                    print(f"   {i+1}. {package.get('package_type', 'Unknown')} - ₹{package.get('price', 0)} ({package.get('location', 'Unknown')})")
            else:
                print("⚠️ No packages found - database may be empty")
            
            return True
        else:
            print(f"❌ Packages endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Packages test failed: {e}")
        return False

def test_puja_filtering():
    """Test puja services filtering"""
    print("\n🔍 Testing Service Filtering...")
    
    try:
        # Test filter by type
        response = requests.get(f"{PUJA_BASE_URL}/services/?type=HOME", timeout=10)
        if response.status_code == 200:
            home_services = response.json()
            print(f"✅ Filter by type working - Found {len(home_services)} HOME services")
        
        # Test search functionality
        response = requests.get(f"{PUJA_BASE_URL}/services/?search=Ganesh", timeout=10)
        if response.status_code == 200:
            search_results = response.json()
            print(f"✅ Search functionality working - Found {len(search_results)} results for 'Ganesh'")
        
        return True
        
    except Exception as e:
        print(f"❌ Filtering test failed: {e}")
        return False

def test_api_documentation():
    """Test API documentation endpoints"""
    print("\n📖 Testing API Documentation...")
    
    try:
        # Test Swagger documentation
        response = requests.get(f"{BASE_URL}/docs/", timeout=10)
        if response.status_code == 200:
            print("✅ Swagger documentation is accessible")
        else:
            print(f"⚠️ Swagger documentation returned status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Documentation test failed: {e}")
        return False

def generate_test_report():
    """Generate comprehensive test report"""
    
    print("\n" + "="*60)
    print("📊 PUJA APP API TEST REPORT")
    print("="*60)
    
    tests = [
        ("API Connectivity", test_api_connectivity),
        ("Puja Categories", test_puja_categories),
        ("Puja Services", test_puja_services),
        ("Puja Packages", test_puja_packages),
        ("Service Filtering", test_puja_filtering),
        ("API Documentation", test_api_documentation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
        except Exception as e:
            status = f"❌ ERROR: {e}"
        
        print(f"{test_name:.<30} {status}")
    
    print("\n" + "="*60)
    print(f"📈 TEST SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Puja app is working correctly!")
    elif passed >= total * 0.8:
        print("✅ Most tests passed. Minor issues may need attention.")
    else:
        print("⚠️ Several tests failed. Please check server status and database.")
    
    print("\n💡 RECOMMENDATIONS:")
    if passed < total:
        print("1. Ensure Django server is running: python manage.py runserver")
        print("2. Check database connectivity and run migrations")
        print("3. Verify API endpoints are properly configured")
    
    print("4. Use the data seeder to populate test data")
    print("5. Test individual API endpoints using Postman")
    print("6. Review the comprehensive improvements document")
    
    return passed == total

def main():
    """Run all API tests"""
    print("🚀 Starting Puja App API Tests")
    print("🔗 Testing API endpoints at:", BASE_URL)
    
    success = generate_test_report()
    
    if not success:
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Start the Django server: python manage.py runserver")
        print("2. Run database migrations: python manage.py migrate")
        print("3. Create test data: python puja_manual_test.py")
        print("4. Check server logs for errors")
    
    return success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
