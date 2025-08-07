"""
Admin URL patterns for Puja system
Enterprise-level admin endpoints with proper organization
"""
from django.urls import path, include
from . import admin_views

# Admin URL patterns
admin_urlpatterns = [
    # Dashboard and Analytics
    path('dashboard/', admin_views.AdminPujaDashboardView.as_view(), name='admin-puja-dashboard'),
    
    # Booking Management
    path('bookings/', admin_views.AdminPujaBookingManagementView.as_view(), name='admin-puja-bookings'),
    path('bookings/<int:pk>/', admin_views.AdminPujaBookingDetailView.as_view(), name='admin-puja-booking-detail'),
    path('bookings/bulk-actions/', admin_views.AdminPujaBulkActionsView.as_view(), name='admin-puja-bulk-actions'),
    
    # Service Management
    path('services/', admin_views.AdminPujaServiceManagementView.as_view(), name='admin-puja-services'),
    
    # Reports and Analytics
    path('reports/', admin_views.AdminPujaReportsView.as_view(), name='admin-puja-reports'),
    
    # Notifications
    path('notifications/send-manual/', admin_views.send_manual_puja_notification, name='admin-puja-send-notification'),
]

urlpatterns = [
    # Include admin URLs under admin/ prefix
    path('admin/', include(admin_urlpatterns)),
]
