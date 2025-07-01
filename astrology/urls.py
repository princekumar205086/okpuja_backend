from django.urls import path
from .views import (
    AstrologyServiceListView,
    AstrologyBookingListView,
    AstrologyBookingCreateView,
    AstrologyBookingDetailView,
    AstrologyBookingUpdateView,
    AstrologyBookingDeleteView
)

urlpatterns = [
    path('services/', AstrologyServiceListView.as_view(), name='astrology-service-list'),
    path('bookings/', AstrologyBookingListView.as_view(), name='astrology-booking-list'),
    path('bookings/create/', AstrologyBookingCreateView.as_view(), name='astrology-booking-create'),
    path('bookings/<int:pk>/', AstrologyBookingDetailView.as_view(), name='astrology-booking-detail'),
    path('bookings/<int:pk>/update/', AstrologyBookingUpdateView.as_view(), name='astrology-booking-update'),
    path('bookings/<int:pk>/delete/', AstrologyBookingDeleteView.as_view(), name='astrology-booking-delete'),
]