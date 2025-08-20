from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, AdminBookingViewSet
from .invoice_views import (
    generate_invoice_pdf, public_invoice_pdf,
    generate_invoice_html_view, public_invoice_html_view
)

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'admin/bookings', AdminBookingViewSet, basename='admin-booking')

urlpatterns = [
    path('', include(router.urls)),
    path('invoice/<str:book_id>/', generate_invoice_pdf, name='booking-invoice'),
    path('public/invoice/<str:book_id>/', public_invoice_pdf, name='booking-public-invoice'),
    path('invoice/html/<str:book_id>/', generate_invoice_html_view, name='booking-invoice-html'),
    path('public/invoice/html/<str:book_id>/', public_invoice_html_view, name='booking-public-invoice-html'),
    
    # Enterprise Admin URLs
    path('', include('booking.admin_urls')),
]