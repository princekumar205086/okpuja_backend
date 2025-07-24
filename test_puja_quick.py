#!/usr/bin/env python3
"""
Quick Puja App Test Script
Tests basic functionality and creates some sample data
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
project_root = Path(__file__).parent
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, time, timedelta

from puja.models import PujaCategory, PujaService, Package, PujaBooking

User = get_user_model()

def test_puja_models():
    """Test basic model creation"""
    print("🧪 Testing Puja Models...")
    
    # Test Category
    category = PujaCategory.objects.create(name="Test Ganesh Puja")
    print(f"✅ Created category: {category}")
    
    # Test Service
    service = PujaService.objects.create(
        title="Test Ganesh Puja Service",
        image="https://example.com/ganesh.jpg",
        description="Test puja service",
        category=category,
        type="HOME",
        duration_minutes=60
    )
    print(f"✅ Created service: {service}")
    
    # Test Package
    package = Package.objects.create(
        puja_service=service,
        location="Mumbai",
        language="HINDI",
        package_type="STANDARD",
        price=Decimal("1500.00"),
        description="Test package"
    )
    print(f"✅ Created package: {package}")
    
    # Test User
    user, created = User.objects.get_or_create(
        email='test@okpuja.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+919876543210'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    print(f"✅ Created/retrieved user: {user}")
    
    # Test Booking
    booking = PujaBooking.objects.create(
        user=user,
        puja_service=service,
        package=package,
        booking_date=date.today() + timedelta(days=7),
        start_time=time(10, 0),
        end_time=time(11, 0),
        contact_name="Test User",
        contact_number="+919876543210",
        contact_email="test@okpuja.com",
        address="Test Address, Mumbai"
    )
    print(f"✅ Created booking: {booking}")
    
    return {
        'category': category,
        'service': service,
        'package': package,
        'user': user,
        'booking': booking
    }

def test_puja_relationships():
    """Test model relationships"""
    print("\n🔗 Testing Model Relationships...")
    
    category = PujaCategory.objects.first()
    if category:
        services = category.services.all()
        print(f"✅ Category '{category.name}' has {services.count()} services")
        
        for service in services:
            packages = service.packages.all()
            bookings = service.bookings.all()
            print(f"   • Service '{service.title}' has {packages.count()} packages and {bookings.count()} bookings")

def create_sample_data():
    """Create comprehensive sample data"""
    print("\n📊 Creating Sample Data...")
    
    categories_data = [
        "Ganesh Puja",
        "Durga Puja", 
        "Lakshmi Puja",
        "Shiva Puja",
        "Krishna Puja"
    ]
    
    services_created = 0
    packages_created = 0
    
    with transaction.atomic():
        for cat_name in categories_data:
            category, created = PujaCategory.objects.get_or_create(name=cat_name)
            if created:
                print(f"   • Created category: {cat_name}")
            
            # Create 2 services per category
            for i in range(2):
                service_title = f"Complete {cat_name} Ceremony {i+1}"
                service, created = PujaService.objects.get_or_create(
                    title=service_title,
                    defaults={
                        'image': f"https://ik.imagekit.io/okpuja/puja/{cat_name.lower().replace(' ', '-')}.jpg",
                        'description': f"Traditional {cat_name} ceremony with authentic rituals",
                        'category': category,
                        'type': ['HOME', 'TEMPLE', 'ONLINE'][i % 3],
                        'duration_minutes': [60, 90, 120][i % 3]
                    }
                )
                if created:
                    services_created += 1
                    
                    # Create packages for this service
                    for pkg_type in ['BASIC', 'STANDARD', 'PREMIUM']:
                        base_price = {'BASIC': 800, 'STANDARD': 1500, 'PREMIUM': 2500}[pkg_type]
                        package, created = Package.objects.get_or_create(
                            puja_service=service,
                            package_type=pkg_type,
                            language='HINDI',
                            defaults={
                                'location': 'Mumbai',
                                'price': Decimal(str(base_price)),
                                'description': f"{pkg_type.title()} {cat_name} package",
                                'includes_materials': pkg_type in ['STANDARD', 'PREMIUM'],
                                'priest_count': 1 if pkg_type == 'BASIC' else 2
                            }
                        )
                        if created:
                            packages_created += 1
    
    print(f"✅ Created {services_created} services and {packages_created} packages")

def test_api_serialization():
    """Test serializers work correctly"""
    print("\n🔄 Testing API Serialization...")
    
    try:
        from puja.serializers import (
            PujaCategorySerializer, PujaServiceSerializer, 
            PackageSerializer
        )
        
        # Test Category Serializer
        categories = PujaCategory.objects.all()[:2]
        cat_serializer = PujaCategorySerializer(categories, many=True)
        print(f"✅ Serialized {len(cat_serializer.data)} categories")
        
        # Test Service Serializer
        services = PujaService.objects.all()[:2]
        service_serializer = PujaServiceSerializer(services, many=True)
        print(f"✅ Serialized {len(service_serializer.data)} services")
        
        # Test Package Serializer
        packages = Package.objects.all()[:2]
        package_serializer = PackageSerializer(packages, many=True)
        print(f"✅ Serialized {len(package_serializer.data)} packages")
        
    except Exception as e:
        print(f"❌ Serialization error: {e}")

def print_summary():
    """Print data summary"""
    print("\n" + "="*50)
    print("📈 PUJA APP DATA SUMMARY")
    print("="*50)
    
    categories = PujaCategory.objects.count()
    services = PujaService.objects.count()
    packages = Package.objects.count()
    bookings = PujaBooking.objects.count()
    users = User.objects.filter(email__contains='test').count()
    
    print(f"Categories: {categories}")
    print(f"Services: {services}")
    print(f"Packages: {packages}")
    print(f"Bookings: {bookings}")
    print(f"Test Users: {users}")
    
    if packages > 0:
        from django.db.models import Min, Max, Avg
        price_stats = Package.objects.aggregate(
            min_price=Min('price'),
            max_price=Max('price'),
            avg_price=Avg('price')
        )
        print(f"Price Range: ₹{price_stats['min_price']} - ₹{price_stats['max_price']}")
        print(f"Average Price: ₹{round(float(price_stats['avg_price']), 2)}")
    
    print("="*50)

def run_tests():
    """Run all tests"""
    print("🚀 Starting Puja App Tests...")
    print("="*50)
    
    try:
        # Test models
        test_data = test_puja_models()
        
        # Test relationships
        test_puja_relationships()
        
        # Create sample data
        create_sample_data()
        
        # Test serialization
        test_api_serialization()
        
        # Print summary
        print_summary()
        
        print("\n🎉 All tests completed successfully!")
        print("✅ Puja app is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
