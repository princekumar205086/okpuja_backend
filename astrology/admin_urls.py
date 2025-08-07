"""
Admin URLs for Astrology system
Enterprise-level admin endpoints with comprehensive management capabilities
"""
from django.urls import path
from .admin_views import (
    AdminAstrologyDashboardView,
    AdminBookingManagementView,
    AdminBookingDetailView,
    AdminBulkBookingActionsView,
    AdminServiceManagementView,
    AdminReportsView,
    send_manual_notification
)

app_name = 'astrology_admin'

urlpatterns = [
    # Dashboard and Analytics
    path('dashboard/', AdminAstrologyDashboardView.as_view(), name='admin-dashboard'),
    path('reports/', AdminReportsView.as_view(), name='admin-reports'),
    
    # Booking Management
    path('bookings/', AdminBookingManagementView.as_view(), name='admin-bookings-list'),
    path('bookings/<str:astro_book_id>/', AdminBookingDetailView.as_view(), name='admin-booking-detail'),
    path('bookings/bulk-actions/', AdminBulkBookingActionsView.as_view(), name='admin-bulk-actions'),
    
    # Service Management
    path('services/', AdminServiceManagementView.as_view(), name='admin-services'),
    
    # Notifications
    path('notifications/send/', send_manual_notification, name='admin-send-notification'),
]
