from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from puja.models import PujaService, Package

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup test environment for payment testing'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Setting up test environment...")
        
        # Create test user
        email = "asliprinceraj@gmail.com"
        password = "testpass123"
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"✅ Created user: {user.email}")
        else:
            user.set_password(password)
            user.save()
            self.stdout.write(f"✅ Updated user: {user.email}")
        
        # Create test puja service if none exist
        if not PujaService.objects.exists():
            service = PujaService.objects.create(
                name="Test Puja Service",
                description="Test puja service for payment testing",
                is_active=True
            )
            
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
            
            self.stdout.write(f"✅ Created test puja service: {service.name}")
        
        # Show summary
        services = PujaService.objects.filter(is_active=True)
        self.stdout.write(f"\n📊 Test Environment Summary:")
        self.stdout.write(f"   User: {user.email}")
        self.stdout.write(f"   Password: {password}")
        self.stdout.write(f"   Services: {services.count()}")
        
        for service in services[:3]:
            packages = Package.objects.filter(puja_service=service, is_active=True)
            self.stdout.write(f"   - {service.name} (ID: {service.id})")
            for package in packages:
                self.stdout.write(f"     * {package.name} (ID: {package.id}) - ₹{package.price}")
        
        self.stdout.write(f"\n✅ Test environment ready!")
        self.stdout.write(f"🧪 Run payment tests with:")
        self.stdout.write(f"   Email: {user.email}")
        self.stdout.write(f"   Password: {password}")
        if services.exists():
            first_service = services.first()
            first_package = first_service.packages.filter(is_active=True).first()
            if first_package:
                self.stdout.write(f"   Service ID: {first_service.id}")
                self.stdout.write(f"   Package ID: {first_package.id}")
