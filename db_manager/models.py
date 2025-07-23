import os
from django.db import models
from django.conf import settings
from accounts.models import User


class BackupConfig(models.Model):
    """Configuration for backup settings"""
    STORAGE_CHOICES = [
        ('LOCAL', 'Local Storage'),
        ('GDRIVE', 'Google Drive'),
        ('SYSTEM', 'System Path'),
    ]
    
    storage_type = models.CharField(max_length=10, choices=STORAGE_CHOICES, default='LOCAL')
    storage_path = models.CharField(max_length=500, default='backups/', help_text="Path where backups will be stored")
    auto_backup_enabled = models.BooleanField(default=True)
    backup_retention_days = models.PositiveIntegerField(default=7, help_text="Number of days to keep backups")
    max_backup_files = models.PositiveIntegerField(default=10, help_text="Maximum number of backup files to keep")
    
    # Google Drive settings (for future implementation)
    gdrive_folder_id = models.CharField(max_length=100, blank=True, null=True)
    gdrive_credentials = models.TextField(blank=True, null=True, help_text="JSON credentials for Google Drive")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = "Backup Configuration"
        verbose_name_plural = "Backup Configurations"
    
    def __str__(self):
        return f"Backup Config - {self.storage_type}"
    
    @classmethod
    def get_current_config(cls):
        """Get current backup configuration"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class DatabaseBackup(models.Model):
    """Model to track database backups"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('DELETED', 'Deleted'),
    ]
    
    BACKUP_TYPES = [
        ('MANUAL', 'Manual'),
        ('AUTO', 'Automatic'),
        ('SCHEDULED', 'Scheduled'),
    ]
    
    backup_id = models.CharField(max_length=50, unique=True)
    backup_type = models.CharField(max_length=10, choices=BACKUP_TYPES, default='MANUAL')
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    storage_type = models.CharField(max_length=10, default='LOCAL')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    tables_count = models.PositiveIntegerField(default=0)
    records_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Database Backup"
        verbose_name_plural = "Database Backups"
    
    def __str__(self):
        return f"Backup {self.backup_id} - {self.status}"
    
    @property
    def file_size_human(self):
        """Return human readable file size"""
        if self.file_size == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(self.file_size, 1024)))
        p = math.pow(1024, i)
        s = round(self.file_size / p, 2)
        return f"{s} {size_names[i]}"


class RestoreLog(models.Model):
    """Model to track database restore operations"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    restore_id = models.CharField(max_length=50, unique=True)
    backup = models.ForeignKey(DatabaseBackup, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Restore details
    restored_tables = models.PositiveIntegerField(default=0)
    restored_records = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-initiated_at']
        verbose_name = "Restore Log"
        verbose_name_plural = "Restore Logs"
    
    def __str__(self):
        return f"Restore {self.restore_id} - {self.status}"
