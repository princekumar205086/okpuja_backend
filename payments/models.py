"""
Payment Models for PhonePe Integration
Clean and optimized models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class PaymentOrder(models.Model):
    """Payment Order Model"""
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('INITIATED', 'Initiated'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('PHONEPE', 'PhonePe'),
        ('UPI', 'UPI'),
        ('CARD', 'Card'),
        ('NETBANKING', 'Net Banking'),
        ('WALLET', 'Wallet'),
    ]
    
    # Primary Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_orders')
    
    # Cart Integration (optional)
    cart_id = models.CharField(max_length=100, null=True, blank=True, db_index=True, help_text="Associated cart ID")
    
    # Address Integration (for booking creation)
    address_id = models.PositiveIntegerField(null=True, blank=True, help_text="Selected address ID for delivery/service")
    
    # Payment Details
    amount = models.PositiveIntegerField(help_text="Amount in paisa (₹1 = 100 paisa)")
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    
    # PhonePe Specific Fields
    phonepe_payment_url = models.URLField(null=True, blank=True, help_text="PhonePe checkout URL")
    phonepe_transaction_id = models.CharField(max_length=100, null=True, blank=True)
    phonepe_response = models.JSONField(null=True, blank=True, help_text="Raw PhonePe response")
    
    # Metadata
    description = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional order metadata")
    
    # URLs
    redirect_url = models.URLField(help_text="URL to redirect after payment")
    callback_url = models.URLField(null=True, blank=True, help_text="Webhook callback URL")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments_order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant_order_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.merchant_order_id} - ₹{self.amount/100} - {self.status}"
    
    @property
    def amount_in_rupees(self):
        """Get amount in rupees"""
        return self.amount / 100
    
    def is_expired(self):
        """Check if payment order is expired"""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
    
    def mark_success(self, phonepe_transaction_id=None, phonepe_response=None):
        """Mark payment as successful"""
        self.status = 'SUCCESS'
        self.completed_at = timezone.now()
        if phonepe_transaction_id:
            self.phonepe_transaction_id = phonepe_transaction_id
        if phonepe_response:
            self.phonepe_response = phonepe_response
        self.save()
    
    def mark_failed(self, phonepe_response=None):
        """Mark payment as failed"""
        self.status = 'FAILED'
        if phonepe_response:
            self.phonepe_response = phonepe_response
        self.save()


class PaymentRefund(models.Model):
    """Payment Refund Model"""
    
    REFUND_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    
    # Primary Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant_refund_id = models.CharField(max_length=100, unique=True, db_index=True)
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE, related_name='refunds')
    
    # Refund Details
    amount = models.PositiveIntegerField(help_text="Refund amount in paisa")
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='PENDING')
    reason = models.TextField(null=True, blank=True)
    
    # PhonePe Specific Fields
    phonepe_refund_id = models.CharField(max_length=100, null=True, blank=True)
    phonepe_response = models.JSONField(null=True, blank=True, help_text="Raw PhonePe refund response")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments_refund'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant_refund_id']),
            models.Index(fields=['payment_order', 'status']),
        ]
    
    def __str__(self):
        return f"Refund {self.merchant_refund_id} - ₹{self.amount/100} - {self.status}"
    
    @property
    def amount_in_rupees(self):
        """Get refund amount in rupees"""
        return self.amount / 100
    
    def mark_success(self, phonepe_refund_id=None, phonepe_response=None):
        """Mark refund as successful"""
        self.status = 'SUCCESS'
        self.processed_at = timezone.now()
        if phonepe_refund_id:
            self.phonepe_refund_id = phonepe_refund_id
        if phonepe_response:
            self.phonepe_response = phonepe_response
        self.save()
    
    def mark_failed(self, phonepe_response=None):
        """Mark refund as failed"""
        self.status = 'FAILED'
        if phonepe_response:
            self.phonepe_response = phonepe_response
        self.save()


class PaymentWebhook(models.Model):
    """Webhook Log Model"""
    
    EVENT_TYPES = [
        ('PAYMENT_SUCCESS', 'Payment Success'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('REFUND_SUCCESS', 'Refund Success'),
        ('REFUND_FAILED', 'Refund Failed'),
    ]
    
    # Primary Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    merchant_order_id = models.CharField(max_length=100, db_index=True)
    
    # Webhook Data
    raw_data = models.JSONField(help_text="Raw webhook payload")
    headers = models.JSONField(default=dict, help_text="Webhook headers")
    
    # Processing Status
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(null=True, blank=True)
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments_webhook'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['merchant_order_id']),
            models.Index(fields=['event_type', 'processed']),
        ]
    
    def __str__(self):
        return f"Webhook {self.event_type} - {self.merchant_order_id}"
    
    def mark_processed(self, error=None):
        """Mark webhook as processed"""
        self.processed = True
        self.processed_at = timezone.now()
        if error:
            self.processing_error = str(error)
        self.save()
