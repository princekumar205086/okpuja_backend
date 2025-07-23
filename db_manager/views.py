import os
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.permissions import IsAdminUser
from .models import BackupConfig, DatabaseBackup, RestoreLog
from .serializers import (
    BackupConfigSerializer, DatabaseBackupSerializer, RestoreLogSerializer,
    CreateBackupSerializer, RestoreBackupSerializer
)
from .services import DatabaseBackupService


class BackupConfigViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing backup configuration
    """
    queryset = BackupConfig.objects.all()
    serializer_class = BackupConfigSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get current backup configuration",
        responses={200: BackupConfigSerializer}
    )
    def list(self, request):
        config = BackupConfig.get_current_config()
        serializer = self.get_serializer(config)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Update backup configuration",
        request_body=BackupConfigSerializer,
        responses={200: BackupConfigSerializer}
    )
    def update(self, request, pk=None):
        config = BackupConfig.get_current_config()
        serializer = self.get_serializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DatabaseBackupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin-only viewset for managing database backups
    """
    queryset = DatabaseBackup.objects.all()
    serializer_class = DatabaseBackupSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status', 'backup_type', 'storage_type']
    search_fields = ['backup_id', 'file_name']
    ordering = ['-created_at']
    
    @swagger_auto_schema(
        operation_description="Create a new database backup",
        request_body=CreateBackupSerializer,
        responses={
            201: openapi.Response('Backup created successfully', DatabaseBackupSerializer),
            400: 'Bad request'
        }
    )
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        serializer = CreateBackupSerializer(data=request.data)
        if serializer.is_valid():
            service = DatabaseBackupService()
            try:
                backup = service.create_backup(
                    user=request.user,
                    backup_type=serializer.validated_data.get('backup_type', 'MANUAL'),
                    custom_path=serializer.validated_data.get('custom_path')
                )
                return Response(
                    DatabaseBackupSerializer(backup).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Download a backup file",
        responses={
            200: openapi.Response('File download', schema=openapi.Schema(type=openapi.TYPE_FILE)),
            404: 'Backup not found'
        }
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        backup = get_object_or_404(DatabaseBackup, backup_id=pk, status='COMPLETED')
        
        if not os.path.exists(backup.file_path):
            raise Http404("Backup file not found on disk")
        
        response = FileResponse(
            open(backup.file_path, 'rb'),
            as_attachment=True,
            filename=backup.file_name
        )
        response['Content-Type'] = 'application/zip'
        return response
    
    @swagger_auto_schema(
        operation_description="Delete a backup",
        responses={
            204: 'Backup deleted successfully',
            404: 'Backup not found'
        }
    )
    @action(detail=True, methods=['delete'])
    def delete_backup(self, request, pk=None):
        backup = get_object_or_404(DatabaseBackup, backup_id=pk)
        
        # Delete file if exists
        if os.path.exists(backup.file_path):
            os.remove(backup.file_path)
        
        # Update status
        backup.status = 'DELETED'
        backup.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        operation_description="Create automatic backup for today",
        responses={
            201: openapi.Response('Auto backup created', DatabaseBackupSerializer),
            200: openapi.Response('Auto backup already exists', DatabaseBackupSerializer)
        }
    )
    @action(detail=False, methods=['post'])
    def auto_backup(self, request):
        service = DatabaseBackupService()
        try:
            backup = service.auto_backup()
            if backup:
                serializer = DatabaseBackupSerializer(backup)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'message': 'Auto backup is disabled'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RestoreLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin-only viewset for managing database restore operations
    """
    queryset = RestoreLog.objects.all()
    serializer_class = RestoreLogSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status']
    search_fields = ['restore_id', 'backup__backup_id']
    ordering = ['-initiated_at']
    
    @swagger_auto_schema(
        operation_description="Restore database from backup",
        request_body=RestoreBackupSerializer,
        responses={
            201: openapi.Response('Restore initiated', RestoreLogSerializer),
            400: 'Bad request'
        }
    )
    @action(detail=False, methods=['post'])
    def restore_backup(self, request):
        serializer = RestoreBackupSerializer(data=request.data)
        if serializer.is_valid():
            service = DatabaseBackupService()
            try:
                restore_log = service.restore_backup(
                    backup_id=serializer.validated_data['backup_id'],
                    user=request.user
                )
                return Response(
                    RestoreLogSerializer(restore_log).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Direct download view (for admin download links)
def download_backup(request, backup_id):
    """Direct download view for backup files"""
    if not request.user.is_authenticated or request.user.role != 'ADMIN':
        raise Http404()
    
    service = DatabaseBackupService()
    file_path = service.get_backup_file_path(backup_id)
    
    if not file_path or not os.path.exists(file_path):
        raise Http404("Backup file not found")
    
    backup = get_object_or_404(DatabaseBackup, backup_id=backup_id)
    
    response = FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=backup.file_name
    )
    response['Content-Type'] = 'application/zip'
    return response
