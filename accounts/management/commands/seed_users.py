from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import User, UserProfile
import random
from faker import Faker

class Command(BaseCommand):
    help = 'Seeds the database with test users'

    def handle(self, *args, **options):
        fake = Faker()
        
        # Create admin user
        if not User.objects.filter(email=settings.ADMIN_EMAIL).exists():
            admin = User.objects.create_superuser(
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                username='admin',
                role=User.Role.ADMIN,
                account_status=User.AccountStatus.ACTIVE,
                otp_verified=True,
                is_active=True
            )
            UserProfile.objects.create(
                user=admin,
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created'))

        # Create verified test users
        test_users = [
            {
                'email': 'user1@example.com',
                'password': 'testpass123',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+919876543210'
            },
            {
                'email': 'user2@example.com',
                'password': 'testpass123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'phone': '+919876543211'
            }
        ]

        for user_data in test_users:
            if not User.objects.filter(email=user_data['email']).exists():
                user = User.objects.create(
                    email=user_data['email'],
                    phone=user_data['phone'],
                    role=User.Role.USER,
                    account_status=User.AccountStatus.ACTIVE,
                    otp_verified=True,
                    is_active=True
                )
                user.set_password(user_data['password'])
                user.save()

                UserProfile.objects.create(
                    user=user,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                self.stdout.write(self.style.SUCCESS(f'User {user_data["email"]} created'))

        # Create unverified users (for testing OTP flow)
        for _ in range(3):
            email = fake.email()
            if not User.objects.filter(email=email).exists():
                user = User.objects.create(
                    email=email,
                    phone=f'+91{fake.msisdn()[3:]}',
                    role=User.Role.USER,
                    account_status=User.AccountStatus.PENDING,
                    otp_verified=False,
                    is_active=False
                )
                user.set_password('testpass123')
                user.generate_otp()  # Generates OTP but doesn't verify
                user.save()

                UserProfile.objects.create(
                    user=user,
                    first_name=fake.first_name(),
                    last_name=fake.last_name()
                )
                self.stdout.write(self.style.WARNING(f'Unverified user {email} created'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded user data!'))