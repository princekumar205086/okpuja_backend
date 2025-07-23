from django.core.management.base import BaseCommand
from db_manager.services import DatabaseBackupService


class Command(BaseCommand):
    help = 'Clean up old database backups'

    def handle(self, *args, **options):
        service = DatabaseBackupService()
        
        try:
            service._cleanup_old_backups()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleaned up old backups')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Cleanup failed: {str(e)}'))
