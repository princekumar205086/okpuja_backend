from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import User

class Command(BaseCommand):
    help = 'Seeds the database with admin user'

    def handle(self, *args, **options):
        if User.objects.filter(email=settings.ADMIN_EMAIL).exists():
            self.stdout.write(self.style.WARNING('Admin user already exists.'))
            return

        User.objects.create_superuser(
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            username='admin',
            role=User.Role.ADMIN,
            account_status=User.AccountStatus.ACTIVE
        )
        self.stdout.write(self.style.SUCCESS('Successfully created admin user!'))