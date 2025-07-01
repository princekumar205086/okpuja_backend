from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from model_utils import Choices
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
import uuid

from cart.models import Cart
from accounts.models import Address

User = settings.AUTH_USER_MODEL

class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"
    REJECTED = "REJECTED", "Rejected"
    FAILED = "FAILED", "Failed"
    COMPLETED = "COMPLETED", "Completed"

class Booking(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        db_index=True
    )
    cart = models.ForeignKey(
        Cart, 
        on_delete=models.PROTECT, 
        related_name='bookings'
    )
    book_id = models.CharField(
        max_length=50, 
        unique=True,
        db_index=True
    )
    selected_date = models.DateField()
    selected_time = models.TimeField()
    address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='bookings'
    )
    status = models.CharField(
        max_length=20, 
        choices=BookingStatus.choices, 
        default=BookingStatus.PENDING,
        db_index=True
    )
    cancellation_reason = models.TextField(null=True, blank=True)
    failure_reason = models.TextField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"Booking #{self.book_id} - {self.user.email}"

    def clean(self):
        if self.status == BookingStatus.CANCELLED and not self.cancellation_reason:
            raise ValidationError("Cancellation reason is required when cancelling a booking")
        if self.status == BookingStatus.REJECTED and not self.rejection_reason:
            raise ValidationError("Rejection reason is required when rejecting a booking")
        if self.status == BookingStatus.FAILED and not self.failure_reason:
            raise ValidationError("Failure reason is required when marking booking as failed")

    def save(self, *args, **kwargs):
        if not self.book_id:
            self.book_id = self.generate_booking_id()
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_booking_id(self):
        return f"BK-{uuid.uuid4().hex[:8].upper()}"

    @property
    def total_amount(self):
        """Calculate total amount including any discounts"""
        return self.cart.total_price

    def send_status_notification(self):
        """Send notification based on booking status"""
        from core.tasks import send_booking_notification
        send_booking_notification.delay(self.id)

class BookingAttachment(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    image = ProcessedImageField(
        upload_to='booking_attachments/%Y/%m/%d/',
        processors=[ResizeToFill(800, 600)],
        format='JPEG',
        options={'quality': 80}
    )
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    """Send notifications when booking status changes"""
    if not created:
        instance.send_status_notification()