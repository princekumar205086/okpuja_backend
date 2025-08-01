from django.urls import path
from .views import (
    CreatePaymentOrderFromCartView, 
    PhonePeWebhookView,
    CheckPaymentStatusView,
)
from .simple_redirect_handler import SimpleRedirectView

app_name = 'payments'

urlpatterns = [
    path('cart/', CreatePaymentOrderFromCartView.as_view(), name='payment-cart-create'),
    path('webhook/phonepe/', PhonePeWebhookView.as_view(), name='phonepe-webhook'),
    path('status/<str:merchant_order_id>/', CheckPaymentStatusView.as_view(), name='payment-status'),
    path('redirect/simple/', SimpleRedirectView.as_view(), name='payment-redirect-simple'),
]
