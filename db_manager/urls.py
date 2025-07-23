from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BackupConfigViewSet, DatabaseBackupViewSet, RestoreLogViewSet, download_backup

router = DefaultRouter()
router.register(r'config', BackupConfigViewSet)
router.register(r'backups', DatabaseBackupViewSet)
router.register(r'restore-logs', RestoreLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('download/<str:backup_id>/', download_backup, name='download_backup'),
]
