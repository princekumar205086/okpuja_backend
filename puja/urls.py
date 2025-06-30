from django.urls import path
from .views import (
    PujaCategoryListView, PujaCategoryCreateView,
    PujaServiceListView, PackageListView,
    PujaBookingListView, PujaBookingCreateView, PujaBookingDetailView
)

urlpatterns = [
    # Categories
    path('categories/', PujaCategoryListView.as_view(), name='puja-category-list'),
    path('categories/create/', PujaCategoryCreateView.as_view(), name='puja-category-create'),
    
    # Services
    path('services/', PujaServiceListView.as_view(), name='puja-service-list'),
    
    # Packages
    path('packages/', PackageListView.as_view(), name='package-list'),
    
    # Bookings
    path('bookings/', PujaBookingListView.as_view(), name='puja-booking-list'),
    path('bookings/create/', PujaBookingCreateView.as_view(), name='puja-booking-create'),
    path('bookings/<int:pk>/', PujaBookingDetailView.as_view(), name='puja-booking-detail'),
]