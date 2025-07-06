from django.conf import settings
from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = 'Seeds the database with admin user'

    def handle(self, *args, **options):
        if User.objects.filter(email=settings.ADMIN_EMAIL).exists():
            self.stdout.write(self.style.WARNING('Admin user already exists.'))
            return

        admin = User.objects.create_superuser(
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            username='admin',
            role=User.Role.ADMIN,
            account_status=User.AccountStatus.ACTIVE
        )

        # Mark admin as verified without OTP
        admin.otp_verified = True
        admin.save(update_fields=['otp_verified'])

        self.stdout.write(self.style.SUCCESS('Successfully created admin user!'))
