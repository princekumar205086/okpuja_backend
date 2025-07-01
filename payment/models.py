from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from model_utils import Choices
import uuid
import hashlib
import json
from decimal import Decimal

class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"
    REFUNDED = "REFUNDED", "Refunded"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially Refunded"

class PaymentMethod(models.TextChoices):
    UPI = "UPI", "UPI"
    CREDIT_CARD = "CREDIT_CARD", "Credit Card"
    DEBIT_CARD = "DEBIT_CARD", "Debit Card"
    NET_BANKING = "NET_BANKING", "Net Banking"
    WALLET = "WALLET", "Wallet"
    PHONEPE = "PHONEPE", "PhonePe"
    PAYTM = "PAYTM", "PayTM"
    COD = "COD", "Cash on Delivery"

class Payment(models.Model):
    booking = models.ForeignKey(
        'booking.Booking',
        on_delete=models.PROTECT,
        related_name="payments",
        db_index=True
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Internal transaction ID"
    )
    merchant_transaction_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Merchant reference ID for gateways"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Payment amount in INR"
    )
    currency = models.CharField(
        max_length=3,
        default="INR",
        choices=[("INR", "Indian Rupee")],
        help_text="Currency code"
    )
    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.PHONEPE,
        help_text="Payment method used"
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        help_text="Current payment status"
    )
    phonepe_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="PhonePe's payment reference ID"
    )
    callback_url = models.URLField(
        blank=True,
        null=True,
        help_text="Custom callback URL for webhook"
    )
    redirect_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to redirect after payment completion"
    )
    gateway_response = models.JSONField(
        blank=True,
        null=True,
        help_text="Raw response from payment gateway"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['booking', 'status']),
        ]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.merchant_transaction_id:
            self.merchant_transaction_id = self._generate_merchant_transaction_id()
        if not self.transaction_id:
            self.transaction_id = self._generate_transaction_id()
        super().save(*args, **kwargs)

    def _generate_merchant_transaction_id(self):
        """Generate unique merchant transaction ID"""
        timestamp = str(int(timezone.now().timestamp() * 1000))
        return f"MT{hashlib.sha256(timestamp.encode()).hexdigest()[:15]}"

    def _generate_transaction_id(self):
        """Generate internal transaction ID"""
        return f"TXN{uuid.uuid4().hex[:10].upper()}"

    @property
    def is_refundable(self):
        """Check if payment can be refunded"""
        return (
            self.status == PaymentStatus.SUCCESS and
            self.method != PaymentMethod.COD
        )

    @property
    def amount_refundable(self):
        """Calculate remaining refundable amount"""
        refunds = self.refunds.aggregate(total=models.Sum('amount'))['total'] or 0
        return self.amount - refunds

    def send_notification(self):
        """Trigger payment status notification"""
        from core.tasks import send_payment_notification
        send_payment_notification.delay(self.id)

class Refund(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="refunds"
    )
    refund_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Internal refund reference ID"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount being refunded"
    )
    reason = models.TextField(help_text="Reason for refund")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        help_text="Refund status"
    )
    gateway_response = models.JSONField(
        blank=True,
        null=True,
        help_text="Raw response from payment gateway"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Admin user who processed the refund"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"

    def __str__(self):
        return f"Refund {self.refund_id} - {self.amount} {self.payment.currency}"

    def save(self, *args, **kwargs):
        if not self.refund_id:
            self.refund_id = f"RFND{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

@receiver(post_save, sender=Refund)
def update_payment_status_on_refund(sender, instance, created, **kwargs):
    """Update payment status when refund is created"""
    if created:
        payment = instance.payment
        if payment.amount_refundable <= 0:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED
        payment.save()