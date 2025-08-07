"""
Admin URLs for Astrology system
Enterprise-level admin endpoints with comprehensive management capabilities
"""
from django.urls import path
from .admin_views import (
    AdminAstrologyDashboardView,
    AdminAstrologyBookingManagementView,
    AdminAstrologerManagementView,
    AdminAstrologyBulkActionsView,
    AdminServiceManagementView,
    AdminAstrologyReportsView,
    send_manual_astrology_notification
)

app_name = 'astrology_admin'

urlpatterns = [
    # Dashboard and Analytics
    path('dashboard/', AdminAstrologyDashboardView.as_view(), name='admin-dashboard'),
    path('reports/', AdminAstrologyReportsView.as_view(), name='admin-reports'),
    
    # Booking Management - Order matters! Specific URLs first
    path('bookings/', AdminAstrologyBookingManagementView.as_view(), name='admin-bookings-list'),
    path('bookings/bulk-actions/', AdminAstrologyBulkActionsView.as_view(), name='admin-bulk-actions'),
    path('bookings/<str:astro_book_id>/', AdminAstrologerManagementView.as_view(), name='admin-booking-detail'),
    
    # Service Management
    path('services/', AdminServiceManagementView.as_view(), name='admin-services'),
    
    # Notifications
    path('notifications/send/', send_manual_astrology_notification, name='admin-send-notification'),
]
