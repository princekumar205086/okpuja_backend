from django.urls import path, include
from .views import (
    PujaCategoryListView, PujaCategoryCreateView, PujaCategoryDetailView,
    PujaServiceListView, PujaServiceCreateView, PujaServiceDetailView,
    PackageListView, PackageCreateView, PackageDetailView,
    PujaBookingListView, PujaBookingCreateView, PujaBookingDetailView,
    PujaBookingRescheduleView
)

urlpatterns = [
    # Categories
    path('categories/', PujaCategoryListView.as_view(), name='puja-category-list'),
    path('categories/create/', PujaCategoryCreateView.as_view(), name='puja-category-create'),
    path('categories/<int:pk>/', PujaCategoryDetailView.as_view(), name='puja-category-detail'),

    # Services
    path('services/', PujaServiceListView.as_view(), name='puja-service-list'),
    path('services/create/', PujaServiceCreateView.as_view(), name='puja-service-create'),
    path('services/<int:pk>/', PujaServiceDetailView.as_view(), name='puja-service-detail'),

    # Packages
    path('packages/', PackageListView.as_view(), name='package-list'),
    path('packages/create/', PackageCreateView.as_view(), name='package-create'),
    path('packages/<int:pk>/', PackageDetailView.as_view(), name='package-detail'),

    # Bookings
    path('bookings/', PujaBookingListView.as_view(), name='puja-booking-list'),
    path('bookings/create/', PujaBookingCreateView.as_view(), name='puja-booking-create'),
    path('bookings/<int:pk>/', PujaBookingDetailView.as_view(), name='puja-booking-detail'),
    path('bookings/<int:pk>/reschedule/', PujaBookingRescheduleView.as_view(), name='puja-booking-reschedule'),

    # Admin URLs - Enterprise level admin endpoints
    path('', include('puja.admin_urls')),
]