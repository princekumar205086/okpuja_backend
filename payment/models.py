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
    # Make booking nullable to allow payment creation before booking
    booking = models.ForeignKey(
        'booking.Booking',
        on_delete=models.PROTECT,
        related_name="payments",
        db_index=True,
        null=True,
        blank=True,
        help_text="Booking created after successful payment"
    )
    # Add cart field to link payment to cart before booking creation
    cart = models.ForeignKey(
        'cart.Cart',
        on_delete=models.PROTECT,
        related_name="payments",
        db_index=True,
        help_text="Cart being purchased"
    )
    # Add user field for direct user reference
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
        db_index=True,
        help_text="User making the payment"
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
            models.Index(fields=['cart', 'status']),
            models.Index(fields=['user', 'status']),
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
        
        # Check if the status is being updated to SUCCESS
        status_changed_to_success = False
        if self.pk is not None:
            try:
                orig = Payment.objects.get(pk=self.pk)
                if orig.status != PaymentStatus.SUCCESS and self.status == PaymentStatus.SUCCESS:
                    status_changed_to_success = True
            except Payment.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Create booking after saving if status changed to SUCCESS
        if status_changed_to_success and not self.booking:
            try:
                self.create_booking_from_cart()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to create booking for payment {self.id}: {str(e)}")

    def create_booking_from_cart(self):
        """Create booking after successful payment"""
        from booking.models import Booking, BookingStatus
        from accounts.models import Address
        from django.db import transaction
        from datetime import datetime
        
        if self.status != PaymentStatus.SUCCESS:
            raise ValueError("Can only create booking from successful payments")
        
        if self.booking:
            raise ValueError("Booking already exists for this payment")
        
        if not self.cart:
            raise ValueError("No cart associated with this payment")
        
        with transaction.atomic():
            # Find the user's default address or create one if needed
            default_address = Address.objects.filter(user=self.user, is_default=True).first()
            if not default_address:
                default_address = Address.objects.filter(user=self.user).order_by('-created_at').first()
                if not default_address:
                    # Create a basic address if none exists
                    default_address = Address.objects.create(
                        user=self.user,
                        address_line_1="Default Address",
                        city="Unknown",
                        state="Unknown",
                        pincode="000000",
                        is_default=True
                    )

            # Parse time from cart
            selected_time_str = self.cart.selected_time
            try:
                # Handle different time formats
                if "AM" in selected_time_str or "PM" in selected_time_str:
                    parsed_time = datetime.strptime(selected_time_str, '%I:%M %p').time()
                else:
                    parsed_time = datetime.strptime(selected_time_str, '%H:%M').time()
            except ValueError:
                # Fallback to default time
                parsed_time = datetime.strptime("10:00", '%H:%M').time()
            
            # Create booking from cart data
            booking = Booking.objects.create(
                user=self.user,
                cart=self.cart,
                selected_date=self.cart.selected_date,
                selected_time=parsed_time,
                address=default_address,
                status=BookingStatus.CONFIRMED
            )
            
            # Link payment to booking
            self.booking = booking
            Payment.objects.filter(pk=self.pk).update(booking=booking)
            
            # Mark cart as converted
            self.cart.status = 'CONVERTED'
            self.cart.save()
            
            return booking

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
    
    def create_booking_from_cart(self):
        """Create booking after successful payment"""
        from booking.models import Booking
        from django.db import transaction
        from datetime import datetime
        
        if self.status != PaymentStatus.SUCCESS:
            raise ValueError("Can only create booking from successful payments")
        
        if self.booking:
            raise ValueError("Booking already exists for this payment")
        
        if not self.cart:
            raise ValueError("No cart associated with this payment")
        
        with transaction.atomic():
            # Parse time from cart (assuming it's stored as string)
            selected_time = self.cart.selected_time
            if isinstance(selected_time, str):
                try:
                    # Try to parse as time format (HH:MM or HH:MM:SS)
                    if ':' in selected_time:
                        time_parts = selected_time.split(':')
                        if len(time_parts) == 2:
                            selected_time = datetime.strptime(selected_time, '%H:%M').time()
                        elif len(time_parts) == 3:
                            selected_time = datetime.strptime(selected_time, '%H:%M:%S').time()
                    else:
                        # If no colon, treat as hour only
                        selected_time = datetime.strptime(f"{selected_time}:00", '%H:%M').time()
                except ValueError:
                    # If parsing fails, use a default time
                    selected_time = datetime.strptime("10:00", '%H:%M').time()
            
            # Create booking from cart data
            booking = Booking.objects.create(
                user=self.user,
                cart=self.cart,
                selected_date=self.cart.selected_date,
                selected_time=selected_time,
                address=self.user.addresses.filter(is_default=True).first(),
                status='CONFIRMED'  # Since payment is successful
            )
            
            # Link payment to booking
            self.booking = booking
            self.save()
            
            # Mark cart as converted
            self.cart.status = 'CONVERTED'
            self.cart.save()
            
            # Send booking confirmation
            from core.tasks import send_booking_confirmation
            send_booking_confirmation.delay(booking.id)
            
            return booking

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