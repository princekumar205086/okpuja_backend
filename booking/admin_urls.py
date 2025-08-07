"""
Admin URL patterns for Booking system
Enterprise-level admin endpoints with comprehensive management
"""
from django.urls import path, include
from . import admin_views

# Admin URL patterns
admin_urlpatterns = [
    # Dashboard and Analytics
    path('dashboard/', admin_views.AdminBookingDashboardView.as_view(), name='admin-booking-dashboard'),
    
    # Booking Management - Order matters! Specific URLs first
    path('bookings/', admin_views.AdminBookingManagementView.as_view(), name='admin-booking-management'),
    path('bookings/bulk-actions/', admin_views.AdminBookingBulkActionsView.as_view(), name='admin-booking-bulk-actions'),
    path('bookings/<int:pk>/', admin_views.AdminBookingDetailView.as_view(), name='admin-booking-detail'),
    
    # Reports and Analytics
    path('reports/', admin_views.AdminBookingReportsView.as_view(), name='admin-booking-reports'),
    
    # Notifications
    path('notifications/send-manual/', admin_views.send_manual_booking_notification, name='admin-booking-send-notification'),
]

urlpatterns = [
    # Include admin URLs under admin/ prefix
    path('admin/', include(admin_urlpatterns)),
]
