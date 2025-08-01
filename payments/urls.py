"""
Clean URL patterns for payments app with better organization
"""

from django.urls import path
from . import views
from .redirect_handler import PaymentRedirectHandler
from .simple_redirect_handler import SimplePaymentRedirectHandler
from .cart_views import CartPaymentView, CartPaymentStatusView

app_name = 'payments'

urlpatterns = [
    # Core Payment Operations
    path('create/', views.CreatePaymentView.as_view(), name='create_payment'),
    path('list/', views.PaymentListView.as_view(), name='payment_list'),
    path('status/<str:merchant_order_id>/', views.PaymentStatusView.as_view(), name='payment_status'),
    
    # Cart-based Payment Operations (NEW)
    path('cart/', CartPaymentView.as_view(), name='cart_payment'),
    path('cart/status/<str:cart_id>/', CartPaymentStatusView.as_view(), name='cart_payment_status'),
    
    # Refund Operations
    path('refund/<str:merchant_order_id>/', views.CreateRefundView.as_view(), name='create_refund'),
    path('refund/status/<str:merchant_refund_id>/', views.RefundStatusView.as_view(), name='refund_status'),
    
    # Webhook Endpoints
    path('webhook/phonepe/', views.PhonePeWebhookView.as_view(), name='phonepe_webhook'),
    
    # Smart Redirect Handler (NEW)
    path('redirect/', PaymentRedirectHandler.as_view(), name='payment_redirect'),
    
    # Simple Redirect Handler (Alternative)
    path('redirect/simple/', SimplePaymentRedirectHandler.as_view(), name='simple_payment_redirect'),
    
    # Latest Payment Status (for frontend)
    path('latest/', views.LatestPaymentStatusView.as_view(), name='latest_payment_status'),
    
    # Utility & Testing Endpoints
    path('health/', views.payment_health_check, name='payment_health'),
    path('test/', views.quick_payment_test, name='quick_test'),
]