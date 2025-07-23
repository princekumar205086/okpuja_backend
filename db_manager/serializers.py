from rest_framework import serializers
from .models import BackupConfig, DatabaseBackup, RestoreLog


class BackupConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupConfig
        fields = [
            'id', 'storage_type', 'storage_path', 'auto_backup_enabled',
            'backup_retention_days', 'max_backup_files', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DatabaseBackupSerializer(serializers.ModelSerializer):
    file_size_human = serializers.ReadOnlyField()
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = DatabaseBackup
        fields = [
            'id', 'backup_id', 'backup_type', 'file_name', 'file_path',
            'file_size', 'file_size_human', 'storage_type', 'status',
            'error_message', 'created_by_email', 'created_at', 'completed_at',
            'tables_count', 'records_count'
        ]
        read_only_fields = [
            'id', 'backup_id', 'file_name', 'file_path', 'file_size',
            'status', 'error_message', 'created_at', 'completed_at',
            'tables_count', 'records_count'
        ]


class RestoreLogSerializer(serializers.ModelSerializer):
    backup_id = serializers.CharField(source='backup.backup_id', read_only=True)
    initiated_by_email = serializers.CharField(source='initiated_by.email', read_only=True)
    
    class Meta:
        model = RestoreLog
        fields = [
            'id', 'restore_id', 'backup_id', 'status', 'error_message',
            'initiated_by_email', 'initiated_at', 'completed_at',
            'restored_tables', 'restored_records'
        ]
        read_only_fields = [
            'id', 'restore_id', 'status', 'error_message',
            'initiated_at', 'completed_at', 'restored_tables', 'restored_records'
        ]


class CreateBackupSerializer(serializers.Serializer):
    backup_type = serializers.ChoiceField(
        choices=[('MANUAL', 'Manual'), ('SCHEDULED', 'Scheduled')],
        default='MANUAL'
    )
    storage_type = serializers.ChoiceField(
        choices=[('LOCAL', 'Local'), ('GDRIVE', 'Google Drive'), ('SYSTEM', 'System Path')],
        required=False
    )
    custom_path = serializers.CharField(max_length=500, required=False, allow_blank=True)


class RestoreBackupSerializer(serializers.Serializer):
    backup_id = serializers.CharField(max_length=50)
    confirm = serializers.BooleanField(default=False)
    
    def validate_backup_id(self, value):
        try:
            backup = DatabaseBackup.objects.get(backup_id=value, status='COMPLETED')
            return value
        except DatabaseBackup.DoesNotExist:
            raise serializers.ValidationError("Backup not found or not completed")
    
    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm the restore operation")
        return value
