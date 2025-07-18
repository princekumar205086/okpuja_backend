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
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings',
        help_text="Employee/Priest assigned to handle this booking"
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
        send_booking_notification(self.id)
    
    def can_be_rescheduled(self):
        """Check if booking can be rescheduled"""
        return self.status not in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]
    
    def can_be_assigned(self):
        """Check if booking can be assigned to an employee"""
        return self.status not in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]
    
    def reschedule(self, new_date, new_time, rescheduled_by):
        """Reschedule booking to new date/time"""
        if not self.can_be_rescheduled():
            raise ValidationError("Cannot reschedule completed or cancelled bookings")
        
        old_date = self.selected_date
        old_time = self.selected_time
        
        self.selected_date = new_date
        self.selected_time = new_time
        self.save()
        
        # Send reschedule notification
        from core.tasks import send_booking_reschedule_notification
        send_booking_reschedule_notification.delay(
            self.id, old_date, old_time, rescheduled_by.id
        )
    
    def assign_to(self, employee, assigned_by):
        """Assign booking to an employee"""
        if not self.can_be_assigned():
            raise ValidationError("Cannot assign completed or cancelled bookings")
        
        old_assigned = self.assigned_to
        self.assigned_to = employee
        self.save()
        
        # Send assignment notification
        from core.tasks import send_booking_assignment_notification
        send_booking_assignment_notification.delay(
            self.id, assigned_by.id, old_assigned.id if old_assigned else None
        )

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
    """Send notifications when booking is created or status changes"""
    from core.tasks import send_booking_confirmation, send_booking_notification
    
    if created and instance.status == BookingStatus.CONFIRMED:
        # Send confirmation email for new confirmed bookings
        send_booking_confirmation.delay(instance.id)
    elif not created:
        # Send status update notifications for existing bookings
        send_booking_notification.delay(instance.id)