from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaymentWebhookView, WebhookDebugView, AdminPaymentViewSet
from .webhook_handler_v2 import PhonePeV2WebhookView, phonepe_v2_webhook

# Create router for payment endpoints
router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'admin/payments', AdminPaymentViewSet, basename='admin-payment')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # PhonePe V2 Webhook endpoints (Official Implementation)
    path('webhook/phonepe/v2/', 
         PhonePeV2WebhookView.as_view(), 
         name='phonepe-v2-webhook'),
    
    path('webhook/phonepe/v2/simple/', 
         phonepe_v2_webhook, 
         name='phonepe-v2-webhook-simple'),
    
    # Generic webhook endpoints (Legacy)
    path('webhook/<str:gateway_name>/', 
         PaymentWebhookView.as_view(), 
         name='payment-webhook'),
    
    # Debug webhook (for testing)
    path('webhook/debug/', 
         WebhookDebugView.as_view(), 
         name='webhook-debug'),
]