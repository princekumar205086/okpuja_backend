from django.urls import path, include
from .views import (
    AstrologyServiceListView,
    AstrologyServiceCreateView,
    AstrologyServiceDetailView,
    AstrologyServiceUpdateView,
    AstrologyServiceDeleteView,
    AstrologyServiceImageUploadView,
    AstrologyBookingListView,
    AstrologyBookingCreateView,
    AstrologyBookingDetailView,
    AstrologyBookingUpdateView,
    AstrologyBookingDeleteView,
    AstrologyBookingRescheduleView,
    AstrologyBookingWithPaymentView,
    AstrologyBookingConfirmationView
)

urlpatterns = [
    # Public endpoints
    path('services/', AstrologyServiceListView.as_view(), name='astrology-service-list'),
    path('services/<int:pk>/', AstrologyServiceDetailView.as_view(), name='astrology-service-detail'),
    path('bookings/book-with-payment/', AstrologyBookingWithPaymentView.as_view(), name='astrology-booking-with-payment'),
    path('bookings/confirmation/', AstrologyBookingConfirmationView.as_view(), name='astrology-booking-confirmation'),
    
    # User authenticated endpoints
    path('bookings/', AstrologyBookingListView.as_view(), name='astrology-booking-list'),
    path('bookings/create/', AstrologyBookingCreateView.as_view(), name='astrology-booking-create'),
    path('bookings/<int:pk>/', AstrologyBookingDetailView.as_view(), name='astrology-booking-detail'),
    path('bookings/<int:pk>/update/', AstrologyBookingUpdateView.as_view(), name='astrology-booking-update'),
    path('bookings/<int:pk>/reschedule/', AstrologyBookingRescheduleView.as_view(), name='astrology-booking-reschedule'),
    path('bookings/<int:pk>/delete/', AstrologyBookingDeleteView.as_view(), name='astrology-booking-delete'),
    
    # Admin endpoints (require admin permissions)
    path('services/create/', AstrologyServiceCreateView.as_view(), name='astrology-service-create'),
    path('services/<int:pk>/update/', AstrologyServiceUpdateView.as_view(), name='astrology-service-update'),
    path('services/<int:pk>/delete/', AstrologyServiceDeleteView.as_view(), name='astrology-service-delete'),
    path('services/<int:pk>/image/', AstrologyServiceImageUploadView.as_view(), name='astrology-service-image-upload'),
    
    # Advanced Admin endpoints
    path('admin/', include('astrology.admin_urls')),
]