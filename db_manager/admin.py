from django.contrib import admin
from django.utils.html import format_html
from .models import BackupConfig, DatabaseBackup, RestoreLog


@admin.register(BackupConfig)
class BackupConfigAdmin(admin.ModelAdmin):
    list_display = ('storage_type', 'auto_backup_enabled', 'backup_retention_days', 'updated_at', 'updated_by')
    fields = (
        'storage_type', 'storage_path', 'auto_backup_enabled', 
        'backup_retention_days', 'max_backup_files'
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    list_display = (
        'backup_id', 'backup_type', 'status', 'file_size_display', 
        'created_by', 'created_at', 'download_link'
    )
    list_filter = ('status', 'backup_type', 'storage_type', 'created_at')
    search_fields = ('backup_id', 'file_name', 'created_by__email')
    readonly_fields = (
        'backup_id', 'file_name', 'file_path', 'file_size', 
        'tables_count', 'records_count', 'completed_at'
    )
    
    fieldsets = (
        ('Backup Info', {
            'fields': ('backup_id', 'backup_type', 'status', 'storage_type')
        }),
        ('File Details', {
            'fields': ('file_name', 'file_path', 'file_size')
        }),
        ('Statistics', {
            'fields': ('tables_count', 'records_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        return obj.file_size_human
    file_size_display.short_description = 'File Size'
    
    def download_link(self, obj):
        if obj.status == 'COMPLETED' and obj.file_path:
            return format_html(
                '<a href="/api/db-manager/download/{}" target="_blank">Download</a>',
                obj.backup_id
            )
        return '-'
    download_link.short_description = 'Download'


@admin.register(RestoreLog)
class RestoreLogAdmin(admin.ModelAdmin):
    list_display = (
        'restore_id', 'backup', 'status', 'restored_tables', 
        'restored_records', 'initiated_by', 'initiated_at'
    )
    list_filter = ('status', 'initiated_at')
    search_fields = ('restore_id', 'backup__backup_id', 'initiated_by__email')
    readonly_fields = (
        'restore_id', 'backup', 'restored_tables', 
        'restored_records', 'completed_at'
    )
    
    fieldsets = (
        ('Restore Info', {
            'fields': ('restore_id', 'backup', 'status')
        }),
        ('Statistics', {
            'fields': ('restored_tables', 'restored_records')
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at')
        }),
        ('Error Info', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
