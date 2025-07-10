from django.db import models
from django.conf import settings
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, SmartResize
from accounts.models import ImageKitField
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL

def puja_service_image_path(instance, filename):
    """Generate file path for puja service images"""
    return f'puja/services/{instance.id}/{filename}'

class PujaCategory(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Puja Category"
        verbose_name_plural = "Puja Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class PujaService(models.Model):
    class ServiceType(models.TextChoices):
        HOME = 'HOME', 'At Home'
        TEMPLE = 'TEMPLE', 'At Temple'
        ONLINE = 'ONLINE', 'Online'

    title = models.CharField(max_length=255, db_index=True)
    image = ImageKitField(_('image URL'))
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
    description = models.TextField()
    category = models.ForeignKey(
        PujaCategory,
        on_delete=models.PROTECT,
        related_name='services'
    )
    type = models.CharField(
        max_length=10,
        choices=ServiceType.choices,
        default=ServiceType.HOME
    )
    duration_minutes = models.PositiveIntegerField(
        help_text="Approximate duration in minutes"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Puja Service"
        verbose_name_plural = "Puja Services"
        ordering = ['title']
        indexes = [
            models.Index(fields=['title', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"

class Package(models.Model):
    class Language(models.TextChoices):
        HINDI = 'HINDI', 'Hindi'
        ENGLISH = 'ENGLISH', 'English'
        SANSKRIT = 'SANSKRIT', 'Sanskrit'
        REGIONAL = 'REGIONAL', 'Regional'

    class PackageType(models.TextChoices):
        BASIC = 'BASIC', 'Basic'
        STANDARD = 'STANDARD', 'Standard'
        PREMIUM = 'PREMIUM', 'Premium'
        CUSTOM = 'CUSTOM', 'Custom'

    puja_service = models.ForeignKey(
        PujaService,
        on_delete=models.CASCADE,
        related_name='packages'
    )
    location = models.CharField(max_length=255)
    language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.HINDI
    )
    package_type = models.CharField(
        max_length=10,
        choices=PackageType.choices,
        default=PackageType.STANDARD
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price in INR"
    )
    description = models.TextField()
    includes_materials = models.BooleanField(
        default=False,
        help_text="Does this package include puja materials?"
    )
    priest_count = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of priests required"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service Package"
        verbose_name_plural = "Service Packages"
        ordering = ['puja_service', 'price']
        unique_together = ['puja_service', 'language', 'package_type']

    def __str__(self):
        return f"{self.puja_service.title} - {self.get_language_display()} {self.get_package_type_display()}"

class PujaBooking(models.Model):
    class BookingStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        FAILED = 'FAILED', 'Failed'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='puja_bookings',
        null=True,
        blank=True
    )
    puja_service = models.ForeignKey(
        PujaService,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=10,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    contact_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    contact_email = models.EmailField()
    address = models.TextField()
    special_instructions = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Puja Booking"
        verbose_name_plural = "Puja Bookings"
        ordering = ['-booking_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['booking_date', 'status']),
            models.Index(fields=['puja_service', 'status']),
        ]

    def __str__(self):
        return f"{self.puja_service.title} - {self.booking_date} ({self.get_status_display()})"