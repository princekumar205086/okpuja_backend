"""
Clean URL patterns for payments app
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment Order URLs
    path('create/', views.CreatePaymentView.as_view(), name='create_payment'),
    path('list/', views.PaymentListView.as_view(), name='payment_list'),
    path('status/<str:merchant_order_id>/', views.PaymentStatusView.as_view(), name='payment_status'),
    
    # Refund URLs
    path('refund/<str:merchant_order_id>/', views.CreateRefundView.as_view(), name='create_refund'),
    path('refund/status/<str:merchant_refund_id>/', views.RefundStatusView.as_view(), name='refund_status'),
    
    # Webhook
    path('webhook/phonepe/', views.PhonePeWebhookView.as_view(), name='phonepe_webhook'),
    
    # Utility endpoints
    path('health/', views.payment_health_check, name='payment_health'),
    path('test/', views.quick_payment_test, name='quick_test'),
]
