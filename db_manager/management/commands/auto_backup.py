from django.core.management.base import BaseCommand
from db_manager.services import DatabaseBackupService


class Command(BaseCommand):
    help = 'Create automatic database backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force backup even if one exists for today',
        )

    def handle(self, *args, **options):
        service = DatabaseBackupService()
        
        try:
            if options['force']:
                # Force backup with admin user
                from accounts.models import User
                admin_user = User.objects.filter(role=User.Role.ADMIN).first()
                if not admin_user:
                    self.stdout.write(self.style.ERROR('No admin user found'))
                    return
                
                backup = service.create_backup(admin_user, backup_type='AUTO')
                self.stdout.write(
                    self.style.SUCCESS(f'Forced backup created: {backup.backup_id}')
                )
            else:
                backup = service.auto_backup()
                if backup:
                    self.stdout.write(
                        self.style.SUCCESS(f'Auto backup created: {backup.backup_id}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('Auto backup is disabled or already exists for today')
                    )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
