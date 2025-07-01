from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFill, SmartResize

User = settings.AUTH_USER_MODEL

def astrology_service_image_path(instance, filename):
    return f'astrology/services/{instance.id}/{filename}'

class AstrologyService(models.Model):
    SERVICE_TYPES = [
        ('HOROSCOPE', 'Horoscope Analysis'),
        ('MATCHING', 'Kundali Matching'),
        ('PREDICTION', 'Future Prediction'),
        ('REMEDIES', 'Astrological Remedies'),
        ('GEMSTONE', 'Gemstone Recommendation'),
        ('VAASTU', 'Vaastu Consultation'),
    ]

    title = models.CharField(max_length=255, db_index=True)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, db_index=True)
    description = models.TextField()
    
    # ImageKit integration for main image
    image = ProcessedImageField(
        upload_to=astrology_service_image_path,
        processors=[ResizeToFill(800, 600)],
        format='JPEG',
        options={'quality': 90}
    )
    image_thumbnail = ImageSpecField(
        source='image',
        processors=[SmartResize(300, 200)],
        format='JPEG',
        options={'quality': 85}
    )
    image_card = ImageSpecField(
        source='image',
        processors=[ResizeToFill(600, 400)],
        format='JPEG',
        options={'quality': 90}
    )
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Astrology Service"
        verbose_name_plural = "Astrology Services"
        ordering = ['title']
        indexes = [
            models.Index(fields=['title', 'is_active']),
            models.Index(fields=['service_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_service_type_display()})"

class AstrologyBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='astrology_bookings'
    )
    service = models.ForeignKey(AstrologyService, on_delete=models.PROTECT)
    language = models.CharField(max_length=50)
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    birth_place = models.CharField(max_length=255)
    birth_date = models.DateField()
    birth_time = models.TimeField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    questions = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Astrology Booking"
        verbose_name_plural = "Astrology Bookings"
        ordering = ['-preferred_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['preferred_date', 'status']),
            models.Index(fields=['service', 'status']),
        ]

    def __str__(self):
        return f"{self.contact_email} - {self.service.title} on {self.preferred_date}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.contact_email:
            self.send_booking_confirmation()

    def send_booking_confirmation(self):
        subject = f"Booking Confirmation for {self.service.title}"
        html_message = render_to_string('astrology/booking_email.html', {
            'booking': self,
            'service': self.service
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.contact_email],
            html_message=html_message,
            fail_silently=False
        )