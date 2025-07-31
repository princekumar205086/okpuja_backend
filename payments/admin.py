"""
Clean Admin interface for payments app
"""

from django.contrib import admin
from .models import PaymentOrder, PaymentRefund, PaymentWebhook


@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    """Payment Order Admin"""
    
    list_display = [
        'merchant_order_id', 'user', 'amount_in_rupees', 'status',
        'payment_method', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['merchant_order_id', 'user__username', 'user__email']
    readonly_fields = [
        'id', 'merchant_order_id', 'phonepe_transaction_id',
        'created_at', 'updated_at', 'completed_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'merchant_order_id', 'user', 'status')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'payment_method', 'description')
        }),
        ('PhonePe Data', {
            'fields': ('phonepe_payment_url', 'phonepe_transaction_id', 'phonepe_response'),
            'classes': ('collapse',)
        }),
        ('URLs', {
            'fields': ('redirect_url', 'callback_url')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'expires_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def amount_in_rupees(self, obj):
        return f"₹{obj.amount_in_rupees}"
    amount_in_rupees.short_description = 'Amount'


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    """Payment Refund Admin"""
    
    list_display = [
        'merchant_refund_id', 'payment_order', 'amount_in_rupees',
        'status', 'created_at', 'processed_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['merchant_refund_id', 'payment_order__merchant_order_id']
    readonly_fields = [
        'id', 'merchant_refund_id', 'phonepe_refund_id',
        'created_at', 'updated_at', 'processed_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'merchant_refund_id', 'payment_order', 'status')
        }),
        ('Refund Details', {
            'fields': ('amount', 'reason')
        }),
        ('PhonePe Data', {
            'fields': ('phonepe_refund_id', 'phonepe_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )
    
    def amount_in_rupees(self, obj):
        return f"₹{obj.amount_in_rupees}"
    amount_in_rupees.short_description = 'Amount'


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    """Payment Webhook Admin"""
    
    list_display = [
        'merchant_order_id', 'event_type', 'processed',
        'received_at', 'processed_at'
    ]
    list_filter = ['event_type', 'processed', 'received_at']
    search_fields = ['merchant_order_id']
    readonly_fields = [
        'id', 'raw_data', 'headers', 'received_at', 'processed_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'event_type', 'merchant_order_id', 'processed')
        }),
        ('Webhook Data', {
            'fields': ('raw_data', 'headers'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('processing_error', 'received_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )
