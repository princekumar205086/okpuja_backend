import os
import json
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.db import transaction, connection
from django.utils import timezone
from io import StringIO
import uuid
import sqlite3
from .models import BackupConfig, DatabaseBackup, RestoreLog


class DatabaseBackupService:
    
    def __init__(self):
        self.config = BackupConfig.get_current_config()
        self.base_backup_dir = self._ensure_backup_directory()
    
    def _ensure_backup_directory(self):
        """Ensure backup directory exists"""
        if self.config.storage_type == 'LOCAL':
            backup_dir = Path(settings.BASE_DIR) / self.config.storage_path
        elif self.config.storage_type == 'SYSTEM':
            backup_dir = Path(self.config.storage_path)
        else:  # GDRIVE - store locally first then upload
            backup_dir = Path(settings.BASE_DIR) / 'temp_backups'
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    def create_backup(self, user, backup_type='MANUAL', custom_path=None):
        """Create a new database backup"""
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Create backup record
        backup = DatabaseBackup.objects.create(
            backup_id=backup_id,
            backup_type=backup_type,
            storage_type=self.config.storage_type,
            status='RUNNING',
            created_by=user
        )
        
        try:
            # Determine backup path
            if custom_path:
                backup_dir = Path(custom_path)
                backup_dir.mkdir(parents=True, exist_ok=True)
            else:
                backup_dir = self.base_backup_dir
            
            # Create backup file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"okpuja_backup_{timestamp}.zip"
            backup_path = backup_dir / backup_filename
            
            # Perform backup
            self._create_backup_file(backup_path, backup)
            
            # Update backup record
            backup.file_name = backup_filename
            backup.file_path = str(backup_path)
            backup.file_size = backup_path.stat().st_size
            backup.status = 'COMPLETED'
            backup.completed_at = timezone.now()
            backup.save()
            
            # Clean old backups
            self._cleanup_old_backups()
            
            return backup
            
        except Exception as e:
            backup.status = 'FAILED'
            backup.error_message = str(e)
            backup.save()
            raise e
    
    def _create_backup_file(self, backup_path, backup_obj):
        """Create the actual backup file"""
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup SQLite database
            db_path = Path(settings.DATABASES['default']['NAME'])
            if db_path.exists():
                zipf.write(db_path, 'database.sqlite3')
            
            # Backup media files (if they exist)
            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists():
                for file_path in media_root.rglob('*'):
                    if file_path.is_file():
                        arcname = Path('media') / file_path.relative_to(media_root)
                        zipf.write(file_path, arcname)
            
            # Create metadata file
            metadata = self._generate_backup_metadata()
            zipf.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
            
            # Get database statistics
            stats = self._get_database_stats()
            backup_obj.tables_count = stats['tables_count']
            backup_obj.records_count = stats['records_count']
    
    def _generate_backup_metadata(self):
        """Generate backup metadata"""
        return {
            'backup_date': datetime.now().isoformat(),
            'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'database_name': str(settings.DATABASES['default']['NAME']),
            'apps': list(settings.INSTALLED_APPS),
            'backup_version': '1.0'
        }
    
    def _get_database_stats(self):
        """Get database statistics"""
        with connection.cursor() as cursor:
            # Get tables count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            tables_count = cursor.fetchone()[0]
            
            # Get total records count
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            total_records = 0
            for table in tables:
                table_name = table[0]
                if not table_name.startswith('sqlite_'):
                    cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
                    total_records += cursor.fetchone()[0]
            
            return {
                'tables_count': tables_count,
                'records_count': total_records
            }
    
    def restore_backup(self, backup_id, user):
        """Restore database from backup"""
        restore_id = f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        try:
            backup = DatabaseBackup.objects.get(backup_id=backup_id, status='COMPLETED')
        except DatabaseBackup.DoesNotExist:
            raise ValueError("Backup not found or not completed")
        
        # Create restore log
        restore_log = RestoreLog.objects.create(
            restore_id=restore_id,
            backup=backup,
            status='RUNNING',
            initiated_by=user
        )
        
        try:
            # Perform restore
            self._restore_from_backup_file(backup.file_path, restore_log)
            
            # Update restore log
            restore_log.status = 'COMPLETED'
            restore_log.completed_at = timezone.now()
            restore_log.save()
            
            return restore_log
            
        except Exception as e:
            restore_log.status = 'FAILED'
            restore_log.error_message = str(e)
            restore_log.save()
            raise e
    
    def _restore_from_backup_file(self, backup_file_path, restore_log):
        """Restore from backup file"""
        backup_path = Path(backup_file_path)
        
        if not backup_path.exists():
            raise FileNotFoundError("Backup file not found")
        
        # Create temporary directory for extraction
        temp_dir = Path(settings.BASE_DIR) / 'temp_restore'
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Read metadata
            metadata_path = temp_dir / 'backup_metadata.json'
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            # Restore database
            db_backup_path = temp_dir / 'database.sqlite3'
            if db_backup_path.exists():
                db_path = Path(settings.DATABASES['default']['NAME'])
                
                # Close all database connections
                connection.close()
                
                # Backup current database
                current_backup = db_path.with_suffix('.backup_before_restore')
                if db_path.exists():
                    shutil.copy2(db_path, current_backup)
                
                # Restore database
                shutil.copy2(db_backup_path, db_path)
                
                # Get restore statistics
                stats = self._get_database_stats()
                restore_log.restored_tables = stats['tables_count']
                restore_log.restored_records = stats['records_count']
            
            # Restore media files
            media_backup_dir = temp_dir / 'media'
            if media_backup_dir.exists():
                media_root = Path(settings.MEDIA_ROOT)
                if media_root.exists():
                    shutil.rmtree(media_root)
                shutil.copytree(media_backup_dir, media_root)
        
        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def _cleanup_old_backups(self):
        """Clean up old backup files"""
        if not self.config.auto_backup_enabled:
            return
        
        # Get backups to delete based on retention policy
        cutoff_date = timezone.now() - timedelta(days=self.config.backup_retention_days)
        old_backups = DatabaseBackup.objects.filter(
            created_at__lt=cutoff_date,
            status='COMPLETED'
        ).order_by('created_at')
        
        # Keep maximum number of backups
        all_backups = DatabaseBackup.objects.filter(status='COMPLETED').order_by('-created_at')
        if all_backups.count() > self.config.max_backup_files:
            excess_backups = all_backups[self.config.max_backup_files:]
            old_backups = old_backups.union(excess_backups)
        
        # Delete old backup files and records
        for backup in old_backups:
            try:
                backup_path = Path(backup.file_path)
                if backup_path.exists():
                    backup_path.unlink()
                backup.status = 'DELETED'
                backup.save()
            except Exception as e:
                print(f"Error deleting backup {backup.backup_id}: {e}")
    
    def auto_backup(self):
        """Create automatic daily backup"""
        if not self.config.auto_backup_enabled:
            return None
        
        # Check if backup already exists for today
        today = timezone.now().date()
        existing_backup = DatabaseBackup.objects.filter(
            backup_type='AUTO',
            created_at__date=today,
            status='COMPLETED'
        ).first()
        
        if existing_backup:
            return existing_backup
        
        # Create auto backup with admin user
        from accounts.models import User
        admin_user = User.objects.filter(role=User.Role.ADMIN).first()
        
        if not admin_user:
            raise ValueError("No admin user found for auto backup")
        
        return self.create_backup(admin_user, backup_type='AUTO')
    
    def get_backup_file_path(self, backup_id):
        """Get backup file path for download"""
        try:
            backup = DatabaseBackup.objects.get(backup_id=backup_id, status='COMPLETED')
            return backup.file_path
        except DatabaseBackup.DoesNotExist:
            return None
