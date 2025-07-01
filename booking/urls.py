from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, AdminBookingViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'admin/bookings', AdminBookingViewSet, basename='admin-booking')

urlpatterns = [
    path('', include(router.urls)),
]