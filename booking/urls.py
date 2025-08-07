from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, AdminBookingViewSet
from .invoice_views import generate_invoice_pdf, public_invoice_pdf

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
# Admin bookings are handled by admin_urls.py instead of router

urlpatterns = [
    path('', include(router.urls)),
    path('invoice/<str:book_id>/', generate_invoice_pdf, name='booking-invoice'),
    path('public/invoice/<str:book_id>/', public_invoice_pdf, name='booking-public-invoice'),
    
    # Enterprise Admin URLs
    path('', include('booking.admin_urls')),
]