"""
Puja Data Seeder - Creates comprehensive test data for the puja application
Generates realistic content for categories, services, packages, and bookings
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import timedelta, date, time
import random
from faker import Faker
from decimal import Decimal

from puja.models import PujaCategory, PujaService, Package, PujaBooking

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed the puja app with realistic test data for development and testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            type=int,
            default=12,
            help='Number of categories to create (default: 12)'
        )
        parser.add_argument(
            '--services',
            type=int,
            default=50,
            help='Number of puja services to create (default: 50)'
        )
        parser.add_argument(
            '--packages',
            type=int,
            default=150,
            help='Number of packages to create (default: 150)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=100,
            help='Number of bookings to create (default: 100)'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of test users to create (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing puja data before seeding'
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.clear_existing_data()
        
        with transaction.atomic():
            users = self.create_users(options['users'])
            categories = self.create_categories(options['categories'])
            services = self.create_services(options['services'], categories)
            packages = self.create_packages(options['packages'], services)
            bookings = self.create_bookings(options['bookings'], users, services, packages)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded puja app with realistic data!')
        )
        self.print_summary()
    
    def clear_existing_data(self):
        """Clear existing puja data"""
        self.stdout.write('Clearing existing puja data...')
        
        PujaBooking.objects.all().delete()
        Package.objects.all().delete()
        PujaService.objects.all().delete()
        PujaCategory.objects.all().delete()
        
        # Clear test users (keep admin users)
        User.objects.filter(email__contains='pujauser').delete()
        
        self.stdout.write(self.style.SUCCESS('Existing puja data cleared.'))
    
    def create_users(self, count):
        """Create test users for bookings"""
        self.stdout.write(f'Creating {count} test users...')
        
        # Check if users already exist
        existing_users = list(User.objects.filter(email__contains='pujauser'))
        if len(existing_users) >= count:
            return existing_users[:count]
        
        users = existing_users[:]
        needed = count - len(existing_users)
        
        for i in range(needed):
            try:
                # Create user
                user = User.objects.create_user(
                    email=f'pujauser{i+1+len(existing_users)}@okpuja.com',
                    password='testpass123',
                    phone=f'+91987654{i+1000:04d}'  # Valid Indian phone format
                )
                
                # Create user profile with name
                from accounts.models import UserProfile
                UserProfile.objects.create(
                    user=user,
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                
                users.append(user)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not create user: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'Using {len(users)} users for bookings.'))
        return users
    
    def create_categories(self, count):
        """Create puja categories with Hindu spiritual themes"""
        self.stdout.write(f'Creating {count} puja categories...')
        
        category_data = [
            {'name': 'Ganesh Puja', 'description': 'Lord Ganesha worship ceremonies for removing obstacles'},
            {'name': 'Durga Puja', 'description': 'Divine Mother Durga worship and protection rituals'},
            {'name': 'Lakshmi Puja', 'description': 'Goddess Lakshmi worship for wealth and prosperity'},
            {'name': 'Saraswati Puja', 'description': 'Goddess Saraswati worship for knowledge and wisdom'},
            {'name': 'Shiva Puja', 'description': 'Lord Shiva worship and meditation rituals'},
            {'name': 'Krishna Puja', 'description': 'Lord Krishna worship and devotional ceremonies'},
            {'name': 'Hanuman Puja', 'description': 'Lord Hanuman worship for strength and courage'},
            {'name': 'Vishnu Puja', 'description': 'Lord Vishnu worship for protection and preservation'},
            {'name': 'Navagraha Puja', 'description': 'Nine planetary deities worship for cosmic harmony'},
            {'name': 'Mahalakshmi Puja', 'description': 'Grand Lakshmi worship for abundance and fortune'},
            {'name': 'Kali Puja', 'description': 'Goddess Kali worship for protection and transformation'},
            {'name': 'Surya Puja', 'description': 'Sun god worship for health and vitality'},
            {'name': 'Graha Shanti', 'description': 'Planetary peace rituals for astrological remedies'},
            {'name': 'Vastu Puja', 'description': 'Home and space purification ceremonies'},
            {'name': 'Marriage Rituals', 'description': 'Wedding ceremonies and pre-marriage rituals'},
            {'name': 'Housewarming', 'description': 'Griha Pravesh and new home blessing ceremonies'},
            {'name': 'Festival Pujas', 'description': 'Special festival worship and celebrations'},
            {'name': 'Ancestral Rituals', 'description': 'Pitru Paksha and ancestor worship ceremonies'}
        ]
        
        categories = []
        for i, data in enumerate(category_data[:count]):
            category, created = PujaCategory.objects.get_or_create(
                name=data['name'],
                defaults={'created_at': timezone.now()}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            categories.append(category)
        
        self.stdout.write(self.style.SUCCESS(f'Processed {len(categories)} categories.'))
        return categories
    
    def create_services(self, count, categories):
        """Create puja services with realistic content"""
        self.stdout.write(f'Creating {count} puja services...')
        
        service_templates = [
            {
                'titles': [
                    'Complete {deity} Puja with Aarti',
                    'Traditional {deity} Worship Ceremony',
                    'Sacred {deity} Puja Rituals',
                    'Divine {deity} Blessing Ceremony',
                    'Authentic {deity} Puja Service'
                ],
                'descriptions': [
                    'Experience the divine blessings of {deity} through our authentic and traditional puja ceremony. Our experienced priests will conduct the complete ritual with proper mantras, offerings, and spiritual guidance.',
                    'Join us for a sacred {deity} puja that follows ancient Vedic traditions. This comprehensive ceremony includes all necessary rituals, prayers, and blessings for your spiritual well-being.',
                    'Immerse yourself in the divine energy of {deity} with our traditional puja service. Complete with proper preparations, mantras, and ceremonial offerings.',
                    'Seek the blessings of {deity} through our authentic puja ceremony conducted by learned priests following traditional scriptures and practices.'
                ]
            }
        ]
        
        deity_names = {
            'Ganesh Puja': ['Ganesha', 'Ganapati', 'Vinayaka'],
            'Durga Puja': ['Durga', 'Divine Mother', 'Maa Durga'],
            'Lakshmi Puja': ['Lakshmi', 'Goddess Lakshmi', 'Maa Lakshmi'],
            'Saraswati Puja': ['Saraswati', 'Goddess Saraswati', 'Maa Saraswati'],
            'Shiva Puja': ['Shiva', 'Lord Shiva', 'Mahadev'],
            'Krishna Puja': ['Krishna', 'Lord Krishna', 'Govind'],
            'Hanuman Puja': ['Hanuman', 'Lord Hanuman', 'Bajrangbali'],
            'Vishnu Puja': ['Vishnu', 'Lord Vishnu', 'Narayana'],
            'Navagraha Puja': ['Nine Planets', 'Navagraha', 'Planetary Deities'],
            'Mahalakshmi Puja': ['Mahalakshmi', 'Great Goddess Lakshmi', 'Divine Mother'],
            'Kali Puja': ['Kali', 'Goddess Kali', 'Divine Mother Kali'],
            'Surya Puja': ['Surya', 'Sun God', 'Solar Deity']
        }
        
        # Sample image URLs for puja services
        sample_images = [
            'https://ik.imagekit.io/okpuja/puja/services/ganesh-puja.jpg',
            'https://ik.imagekit.io/okpuja/puja/services/durga-puja.jpg',
            'https://ik.imagekit.io/okpuja/puja/services/lakshmi-puja.jpg',
            'https://ik.imagekit.io/okpuja/puja/services/shiva-puja.jpg',
            'https://ik.imagekit.io/okpuja/puja/services/krishna-puja.jpg',
            'https://ik.imagekit.io/okpuja/puja/services/hanuman-puja.jpg',
            'https://ik.imagekit.io/okpuja/puja/services/saraswati-puja.jpg',
            'https://ik.imagekit.io/okpuja/puja/services/vishnu-puja.jpg'
        ]
        
        services = []
        for i in range(count):
            category = random.choice(categories)
            template = random.choice(service_templates)
            
            # Get deity names for this category
            deities = deity_names.get(category.name, ['Divine', 'Sacred', 'Holy'])
            deity = random.choice(deities)
            
            title = random.choice(template['titles']).format(deity=deity)
            description = random.choice(template['descriptions']).format(deity=deity)
            
            service = PujaService.objects.create(
                title=title,
                image=random.choice(sample_images),
                description=description,
                category=category,
                type=random.choice(['HOME', 'TEMPLE', 'ONLINE']),
                duration_minutes=random.choice([30, 45, 60, 90, 120, 180]),
                is_active=random.choice([True, True, True, False])  # 75% active
            )
            services.append(service)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(services)} puja services.'))
        return services
    
    def create_packages(self, count, services):
        """Create packages for puja services"""
        self.stdout.write(f'Creating {count} packages...')
        
        # Indian cities for location
        indian_cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata',
            'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur',
            'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri-Chinchwad',
            'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik',
            'Faridabad', 'Meerut', 'Rajkot', 'Kalyan-Dombivali', 'Vasai-Virar',
            'Varanasi', 'Srinagar', 'Dhanbad', 'Jodhpur', 'Amritsar', 'Raipur'
        ]
        
        package_descriptions = {
            'BASIC': [
                'Essential puja ceremony with basic offerings and prayers. Perfect for individual worship.',
                'Simple yet authentic puja ritual with necessary mantras and basic preparations.',
                'Traditional puja ceremony with fundamental rituals and blessings.'
            ],
            'STANDARD': [
                'Complete puja ceremony with enhanced offerings, detailed rituals, and spiritual guidance.',
                'Comprehensive puja service with proper arrangements, extended prayers, and ceremonial items.',
                'Full traditional puja with authentic rituals, mantras, and divine blessings.'
            ],
            'PREMIUM': [
                'Elaborate puja ceremony with premium offerings, extended rituals, and personalized spiritual consultation.',
                'Luxury puja experience with finest arrangements, detailed ceremonies, and comprehensive spiritual guidance.',
                'Grand puja celebration with premium preparations, extensive rituals, and divine abundance.'
            ],
            'CUSTOM': [
                'Personalized puja ceremony tailored to your specific requirements and spiritual needs.',
                'Customized puja service designed according to your family traditions and preferences.',
                'Bespoke puja experience created specifically for your unique spiritual journey.'
            ]
        }
        
        packages = []
        packages_per_service = count // len(services) + 1
        
        for service in services:
            service_packages = 0
            for lang in ['HINDI', 'ENGLISH', 'SANSKRIT']:
                for pkg_type in ['BASIC', 'STANDARD', 'PREMIUM']:
                    if service_packages >= packages_per_service:
                        break
                    
                    # Calculate price based on package type and service duration
                    base_price = {
                        'BASIC': 500,
                        'STANDARD': 1500,
                        'PREMIUM': 3500,
                        'CUSTOM': 5000
                    }[pkg_type]
                    
                    # Adjust price based on service duration and type
                    duration_multiplier = service.duration_minutes / 60
                    type_multiplier = {
                        'HOME': 1.5,
                        'TEMPLE': 1.0,
                        'ONLINE': 0.7
                    }[service.type]
                    
                    final_price = base_price * duration_multiplier * type_multiplier
                    final_price = round(final_price / 50) * 50  # Round to nearest 50
                    
                    package = Package.objects.create(
                        puja_service=service,
                        location=random.choice(indian_cities),
                        language=lang,
                        package_type=pkg_type,
                        price=Decimal(str(final_price)),
                        description=random.choice(package_descriptions[pkg_type]),
                        includes_materials=random.choice([True, False]),
                        priest_count=random.choice([1, 1, 1, 2, 2, 3]),  # Weighted towards 1
                        is_active=random.choice([True, True, True, False])  # 75% active
                    )
                    packages.append(package)
                    service_packages += 1
                    
                    if len(packages) >= count:
                        break
                
                if len(packages) >= count:
                    break
            
            if len(packages) >= count:
                break
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(packages)} packages.'))
        return packages
    
    def create_bookings(self, count, users, services, packages):
        """Create realistic puja bookings"""
        self.stdout.write(f'Creating {count} puja bookings...')
        
        if not users:
            self.stdout.write(self.style.WARNING('No users available for bookings.'))
            return []
        
        # Indian cities for addresses
        indian_cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata',
            'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur',
            'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri-Chinchwad',
            'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik',
            'Faridabad', 'Meerut', 'Rajkot', 'Kalyan-Dombivali', 'Vasai-Virar',
            'Varanasi', 'Srinagar', 'Dhanbad', 'Jodhpur', 'Amritsar', 'Raipur'
        ]
        
        special_instructions = [
            'Please bring tulsi leaves for the ceremony',
            'Need vegetarian prasad only',
            'Family has specific dietary restrictions',
            'Prefer morning time for the puja',
            'Please include Aarti in the ceremony',
            'Need English translation of mantras',
            'Family prefers traditional approach',
            'Please bring additional flowers',
            'Need longer duration for detailed ritual',
            'Include special prayers for health'
        ]
        
        bookings = []
        for i in range(count):
            # Select random service and its valid package
            service = random.choice([s for s in services if s.is_active])
            service_packages = [p for p in packages if p.puja_service == service and p.is_active]
            
            if not service_packages:
                continue
                
            package = random.choice(service_packages)
            user = random.choice(users)
            
            # Generate booking date (future dates weighted more)
            days_ahead = random.choices(
                range(1, 365),
                weights=[30] * 30 + [20] * 60 + [10] * 90 + [5] * 184,
                k=1
            )[0]
            booking_date = date.today() + timedelta(days=days_ahead)
            
            # Generate realistic start time (6 AM to 8 PM)
            start_hour = random.choice([6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20])
            start_minute = random.choice([0, 15, 30, 45])
            start_time = time(start_hour, start_minute)
            
            # Calculate end time based on service duration
            end_minutes = start_time.hour * 60 + start_time.minute + service.duration_minutes
            end_hour = (end_minutes // 60) % 24
            end_minute = end_minutes % 60
            end_time = time(end_hour, end_minute)
            
            # Generate status with realistic distribution
            status = random.choices(
                ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'],
                weights=[30, 40, 25, 5],
                k=1
            )[0]
            
            # Generate Indian addresses
            address_templates = [
                f'{random.randint(1, 999)}, {fake.street_name()}, {random.choice(indian_cities)}',
                f'Flat {random.randint(101, 999)}, {fake.street_name()} Society, {random.choice(indian_cities)}',
                f'House No. {random.randint(1, 200)}, Sector {random.randint(1, 50)}, {random.choice(indian_cities)}'
            ]
            
            booking = PujaBooking.objects.create(
                user=user,
                puja_service=service,
                package=package,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                status=status,
                contact_name=f'{user.profile.first_name} {user.profile.last_name}' if hasattr(user, 'profile') else f'User {user.id}',
                contact_number=user.phone or '+91' + ''.join([str(random.randint(0, 9)) for _ in range(10)]),
                contact_email=user.email,
                address=random.choice(address_templates),
                special_instructions=random.choice(special_instructions) if random.random() < 0.6 else '',
                cancellation_reason='Change in schedule' if status == 'CANCELLED' else ''
            )
            bookings.append(booking)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(bookings)} puja bookings.'))
        return bookings
    
    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.HTTP_INFO('PUJA DATA SEEDING SUMMARY'))
        self.stdout.write('='*60)
        
        # Import models at function level to avoid circular imports
        from django.db import models
        
        # Categories summary
        categories = PujaCategory.objects.all()
        self.stdout.write(f'\n📚 CATEGORIES ({categories.count()}):')
        for cat in categories:
            service_count = cat.services.count()
            self.stdout.write(f'   • {cat.name}: {service_count} services')
        
        # Services summary
        services = PujaService.objects.all()
        active_services = services.filter(is_active=True)
        self.stdout.write(f'\n🕉️  SERVICES:')
        self.stdout.write(f'   • Total: {services.count()}')
        self.stdout.write(f'   • Active: {active_services.count()}')
        self.stdout.write(f'   • Inactive: {services.count() - active_services.count()}')
        
        service_types = services.values_list('type', flat=True)
        for stype in ['HOME', 'TEMPLE', 'ONLINE']:
            count = list(service_types).count(stype)
            self.stdout.write(f'   • {stype}: {count}')
        
        # Packages summary
        packages = Package.objects.all()
        active_packages = packages.filter(is_active=True)
        self.stdout.write(f'\n📦 PACKAGES:')
        self.stdout.write(f'   • Total: {packages.count()}')
        self.stdout.write(f'   • Active: {active_packages.count()}')
        
        package_types = packages.values_list('package_type', flat=True)
        for ptype in ['BASIC', 'STANDARD', 'PREMIUM', 'CUSTOM']:
            count = list(package_types).count(ptype)
            self.stdout.write(f'   • {ptype}: {count}')
        
        # Bookings summary
        bookings = PujaBooking.objects.all()
        self.stdout.write(f'\n📅 BOOKINGS ({bookings.count()}):')
        
        booking_statuses = bookings.values_list('status', flat=True)
        for status in ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']:
            count = list(booking_statuses).count(status)
            self.stdout.write(f'   • {status}: {count}')
        
        # Users summary
        puja_users = User.objects.filter(email__contains='pujauser')
        self.stdout.write(f'\n👥 TEST USERS: {puja_users.count()}')
        
        # Price summary
        if packages.exists():
            min_price = packages.aggregate(min_price=models.Min('price'))['min_price']
            max_price = packages.aggregate(max_price=models.Max('price'))['max_price']
            avg_price = packages.aggregate(avg_price=models.Avg('price'))['avg_price']
            self.stdout.write(f'\n💰 PRICING:')
            self.stdout.write(f'   • Min Price: ₹{min_price}')
            self.stdout.write(f'   • Max Price: ₹{max_price}')
            self.stdout.write(f'   • Avg Price: ₹{round(float(avg_price), 2) if avg_price else 0}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎉 Puja seeding completed successfully!'))
        self.stdout.write(self.style.HTTP_INFO('Your puja app is now ready for testing with realistic data.'))
        self.stdout.write('='*60)
