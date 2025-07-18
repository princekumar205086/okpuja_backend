from django.contrib import admin
from .models import Payment, Refund

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'merchant_transaction_id', 'booking', 'amount', 
        'method', 'status', 'created_at'
    )
    list_filter = ('status', 'method', 'created_at')
    search_fields = (
        'merchant_transaction_id', 'transaction_id', 'booking__book_id',
        'booking__user__email'
    )
    readonly_fields = (
        'merchant_transaction_id', 'transaction_id',
        'gateway_response', 'created_at', 'updated_at'
    )
    actions = ['resend_notifications']

    def resend_notifications(self, request, queryset):
        for payment in queryset:
            payment.send_notification()
        self.message_user(request, f"Notifications resent for {queryset.count()} payments")
    resend_notifications.short_description = "Resend payment notifications"

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        'refund_id', 'payment', 'amount', 'status', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'refund_id', 'payment__merchant_transaction_id', 
        'payment__booking__book_id'
    )
    readonly_fields = (
        'refund_id', 'gateway_response', 'created_at'
    )
    raw_id_fields = ('payment', 'processed_by')