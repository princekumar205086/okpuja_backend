#!/usr/bin/env python3
"""
Create test user and data for payment testing
"""

import sys
import os
import django

# Add the project directory to the Python path
sys.path.append(r'C:\Users\Prince Raj\Desktop\nextjs project\okpuja_backend')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

# Setup Django
django.setup()

def create_test_user():
    """Create test user with specified credentials"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    email = "asliprinceraj@gmail.com"
    password = "testpass123"
    
    try:
        # Check if user already exists
        user = User.objects.filter(email=email).first()
        if user:
            print(f"✅ User already exists: {user.email}")
            # Update password to ensure it's correct
            user.set_password(password)
            user.save()
            print(f"🔄 Password updated for user: {user.email}")
        else:
            # Create new user
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name="Test",
                last_name="User",
                is_active=True
            )
            print(f"✅ User created: {user.email}")
        
        return user
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return None

def create_test_data():
    """Create test puja services and packages if they don't exist"""
    from puja.models import PujaService, Package
    
    try:
        # Check if we have puja services
        service_count = PujaService.objects.count()
        print(f"📊 Found {service_count} puja services")
        
        if service_count == 0:
            print("Creating test puja service...")
            # Create a test puja service
            service = PujaService.objects.create(
                name="Test Puja Service",
                description="Test puja service for payment testing",
                is_active=True
            )
            
            # Create test packages
            Package.objects.create(
                puja_service=service,
                name="Basic Package",
                description="Basic test package",
                price=100.00,
                is_active=True
            )
            
            Package.objects.create(
                puja_service=service,
                name="Premium Package", 
                description="Premium test package",
                price=500.00,
                is_active=True
            )
            
            print(f"✅ Created test puja service: {service.name}")
        
        # Show available services
        services = PujaService.objects.filter(is_active=True)[:3]
        for service in services:
            packages = Package.objects.filter(puja_service=service, is_active=True)
            print(f"📋 Service: {service.name} (ID: {service.id})")
            for package in packages:
                print(f"   Package: {package.name} (ID: {package.id}) - ₹{package.price}")
        
        return services.first() if services.exists() else None
        
    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")
        return None

def main():
    print("🔧 Setting up test environment...")
    print("=" * 50)
    
    # Create test user
    user = create_test_user()
    if not user:
        print("❌ Failed to create test user")
        return
    
    # Create test puja services
    service = create_test_data()
    if not service:
        print("❌ Failed to create test data")
        return
    
    print("\n✅ Test environment setup complete!")
    print(f"👤 Test user: {user.email}")
    print(f"🔑 Password: testpass123")
    print(f"🛕 Test service: {service.name} (ID: {service.id})")
    
    packages = service.packages.filter(is_active=True)
    if packages.exists():
        package = packages.first()
        print(f"📦 Test package: {package.name} (ID: {package.id}) - ₹{package.price}")
        
        print(f"\n📝 Test Parameters:")
        print(f"   Email: {user.email}")
        print(f"   Password: testpass123")
        print(f"   Puja Service ID: {service.id}")
        print(f"   Package ID: {package.id}")
        print(f"   Package Price: ₹{package.price}")

if __name__ == "__main__":
    main()
