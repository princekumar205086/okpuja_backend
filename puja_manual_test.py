"""
Puja App Manual Seeding and Testing Script
"""

def create_sample_data():
    """Create sample puja data manually"""
    
    import os
    import django
    from decimal import Decimal
    from datetime import date, time, timedelta
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    from puja.models import PujaCategory, PujaService, Package, PujaBooking
    
    User = get_user_model()
    
    print("🚀 Creating Puja Sample Data...")
    
    # Create categories
    categories_data = [
        "Ganesh Puja",
        "Durga Puja", 
        "Lakshmi Puja",
        "Shiva Puja",
        "Krishna Puja",
        "Hanuman Puja",
        "Saraswati Puja"
    ]
    
    categories = []
    for cat_name in categories_data:
        category, created = PujaCategory.objects.get_or_create(name=cat_name)
        categories.append(category)
        if created:
            print(f"✅ Created category: {cat_name}")
    
    # Create services
    services = []
    service_types = ['HOME', 'TEMPLE', 'ONLINE']
    durations = [60, 90, 120]
    
    for i, category in enumerate(categories):
        for j in range(2):  # 2 services per category
            service_title = f"Complete {category.name} Ceremony {j+1}"
            service, created = PujaService.objects.get_or_create(
                title=service_title,
                defaults={
                    'image': f"https://ik.imagekit.io/okpuja/puja/{category.name.lower().replace(' ', '-')}.jpg",
                    'description': f"Traditional {category.name} ceremony with authentic rituals and blessings",
                    'category': category,
                    'type': service_types[j % 3],
                    'duration_minutes': durations[j % 3],
                    'is_active': True
                }
            )
            services.append(service)
            if created:
                print(f"✅ Created service: {service_title}")
    
    # Create packages
    packages = []
    package_types = ['BASIC', 'STANDARD', 'PREMIUM']
    base_prices = [800, 1500, 2500]
    locations = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata']
    
    for service in services:
        for i, pkg_type in enumerate(package_types):
            package, created = Package.objects.get_or_create(
                puja_service=service,
                package_type=pkg_type,
                language='HINDI',
                defaults={
                    'location': locations[i % len(locations)],
                    'price': Decimal(str(base_prices[i])),
                    'description': f"{pkg_type.title()} {service.category.name} package with complete rituals",
                    'includes_materials': pkg_type in ['STANDARD', 'PREMIUM'],
                    'priest_count': 1 if pkg_type == 'BASIC' else 2,
                    'is_active': True
                }
            )
            packages.append(package)
            if created:
                print(f"✅ Created package: {pkg_type} for {service.title}")
    
    # Create test user
    test_user, created = User.objects.get_or_create(
        email='puja.test@okpuja.com',
        defaults={
            'first_name': 'Puja',
            'last_name': 'Tester',
            'phone': '+919876543210'
        }
    )
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"✅ Created test user: {test_user.email}")
    
    # Create sample bookings
    booking_statuses = ['PENDING', 'CONFIRMED', 'COMPLETED']
    
    for i in range(min(10, len(packages))):
        package = packages[i]
        booking_date = date.today() + timedelta(days=i+1)
        
        booking, created = PujaBooking.objects.get_or_create(
            user=test_user,
            puja_service=package.puja_service,
            package=package,
            booking_date=booking_date,
            defaults={
                'start_time': time(10, 0),
                'end_time': time(11, 0),
                'status': booking_statuses[i % 3],
                'contact_name': 'Puja Tester',
                'contact_number': '+919876543210',
                'contact_email': 'puja.test@okpuja.com',
                'address': f'Test Address {i+1}, Mumbai, Maharashtra 400001',
                'special_instructions': f'Test booking {i+1} - Please bring extra flowers'
            }
        )
        if created:
            print(f"✅ Created booking: {booking.puja_service.title} on {booking_date}")
    
    print("\n📊 Data Creation Summary:")
    print(f"Categories: {PujaCategory.objects.count()}")
    print(f"Services: {PujaService.objects.count()}")
    print(f"Packages: {Package.objects.count()}")
    print(f"Bookings: {PujaBooking.objects.count()}")
    print(f"Test Users: {User.objects.filter(email__contains='puja.test').count()}")
    
    return True

def test_puja_functionality():
    """Test basic puja functionality"""
    
    import os
    import django
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
    django.setup()
    
    from puja.models import PujaCategory, PujaService, Package, PujaBooking
    from puja.serializers import PujaCategorySerializer, PujaServiceSerializer
    
    print("\n🧪 Testing Puja Functionality...")
    
    try:
        # Test model queries
        categories = PujaCategory.objects.all()
        services = PujaService.objects.filter(is_active=True)
        packages = Package.objects.filter(is_active=True)
        bookings = PujaBooking.objects.all()
        
        print(f"✅ Query test passed - {categories.count()} categories, {services.count()} services")
        
        # Test serializers
        if categories.exists():
            cat_serializer = PujaCategorySerializer(categories.first())
            print(f"✅ Category serializer test passed: {cat_serializer.data['name']}")
        
        if services.exists():
            service_serializer = PujaServiceSerializer(services.first())
            print(f"✅ Service serializer test passed: {service_serializer.data['title']}")
        
        # Test relationships
        if services.exists():
            service = services.first()
            service_packages = service.packages.all()
            service_bookings = service.bookings.all()
            print(f"✅ Relationship test passed - Service has {service_packages.count()} packages, {service_bookings.count()} bookings")
        
        # Test filtering
        home_services = PujaService.objects.filter(type='HOME', is_active=True)
        print(f"✅ Filtering test passed - {home_services.count()} HOME services found")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_complete_test():
    """Run complete puja app test"""
    print("🎯 Starting Complete Puja App Test")
    print("=" * 50)
    
    try:
        # Step 1: Create sample data
        if create_sample_data():
            print("✅ Sample data creation successful")
        else:
            print("❌ Sample data creation failed")
            return False
        
        # Step 2: Test functionality
        if test_puja_functionality():
            print("✅ Functionality tests passed")
        else:
            print("❌ Functionality tests failed")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Puja app is working correctly!")
        print("✅ Sample data has been created!")
        print("✅ Ready for API testing!")
        
        print("\n📝 Next Steps:")
        print("1. Test API endpoints using Postman or curl")
        print("2. Verify admin panel functionality")
        print("3. Test booking flow end-to-end")
        print("4. Implement suggested improvements")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Complete test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_complete_test()
    exit(0 if success else 1)
