from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

User = settings.AUTH_USER_MODEL

# Initialize ImageKit client with enhanced configuration
imagekit = ImageKit(
    private_key=settings.IMAGEKIT_PRIVATE_KEY,
    public_key=settings.IMAGEKIT_PUBLIC_KEY,
    url_endpoint=settings.IMAGEKIT_URL_ENDPOINT
)

class ImageKitField(models.CharField):
    """Enhanced custom field to store ImageKit URLs with validation"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 500)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('null', True)
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if value and not value.startswith(('http://', 'https://')):
            raise ValueError("ImageKit URL must be a valid HTTP/HTTPS URL")

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
    
    # Store only the image URL (uploaded to ImageKit)
    image_url = ImageKitField('Service Image URL')
    image_thumbnail_url = ImageKitField('Service Thumbnail URL')
    image_card_url = ImageKitField('Service Card URL')
    
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

    def save_service_image(self, image_file):
        """
        Enhanced service image upload with better file handling
        and error management
        """
        try:
            import os
            import uuid
            from PIL import Image
            from io import BytesIO
            from rest_framework import serializers

            # Read file content once
            if hasattr(image_file, 'read'):
                file_bytes = image_file.read()
                # Reset file pointer if it's a file object
                if hasattr(image_file, 'seek'):
                    image_file.seek(0)
            else:
                with open(image_file, 'rb') as f:
                    file_bytes = f.read()

            # Validate image
            try:
                img_test = Image.open(BytesIO(file_bytes))
                img_test.verify()
                # Reset BytesIO after verification
                del img_test
            except Exception as e:
                raise serializers.ValidationError(f"Invalid image file: {str(e)}")

            # Generate unique filename
            original_filename = getattr(image_file, 'name', 'service.jpg')
            ext = os.path.splitext(original_filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                raise serializers.ValidationError("Unsupported image format. Please upload JPG, JPEG, PNG, GIF, or WEBP.")

            filename = f"service_{self.id}_{uuid.uuid4()}{ext}"

            # Upload original image
            self.image_url = upload_to_imagekit(
                file_bytes,
                filename,
                folder="astrology/services"
            )

            # Create and upload thumbnail
            thumbnail_bytes = self._create_thumbnail(file_bytes)
            thumbnail_filename = f"thumb_{filename}"
            self.image_thumbnail_url = upload_to_imagekit(
                thumbnail_bytes,
                thumbnail_filename,
                folder="astrology/services/thumbnails"
            )

            # Create and upload card image (medium size)
            card_bytes = self._create_card_image(file_bytes)
            card_filename = f"card_{filename}"
            self.image_card_url = upload_to_imagekit(
                card_bytes,
                card_filename,
                folder="astrology/services/cards"
            )

            self.save()
            return True

        except Exception as e:
            # Log the error in production
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving service image: {str(e)}")
            raise

    def _create_thumbnail(self, image_bytes, size=(150, 150), quality=80):
        """Create optimized thumbnail from image bytes"""
        try:
            from PIL import Image
            from io import BytesIO
            
            with Image.open(BytesIO(image_bytes)) as img:
                img = img.convert('RGB')

                # Maintain aspect ratio while fitting within dimensions
                img.thumbnail(size, Image.Resampling.LANCZOS)

                thumb_io = BytesIO()
                img.save(thumb_io, format='JPEG', quality=quality, optimize=True)
                thumb_io.seek(0)
                return thumb_io.getvalue()
        except Exception as e:
            print(f"Error creating thumbnail: {str(e)}")
            raise

    def _create_card_image(self, image_bytes, size=(300, 200), quality=85):
        """Create optimized card image from image bytes"""
        try:
            from PIL import Image
            from io import BytesIO
            
            with Image.open(BytesIO(image_bytes)) as img:
                img = img.convert('RGB')

                # Maintain aspect ratio while fitting within dimensions
                img.thumbnail(size, Image.Resampling.LANCZOS)

                card_io = BytesIO()
                img.save(card_io, format='JPEG', quality=quality, optimize=True)
                card_io.seek(0)
                return card_io.getvalue()
        except Exception as e:
            print(f"Error creating card image: {str(e)}")
            raise

class AstrologyBooking(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),  # Only confirmed bookings exist (after successful payment)
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ]

    # Unique booking identifier for frontend
    astro_book_id = models.CharField(max_length=100, unique=True, db_index=True, help_text="Unique astrology booking ID")
    
    # Payment reference for tracking
    payment_id = models.CharField(max_length=100, null=True, blank=True, db_index=True, help_text="Associated payment order ID")
    
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
        default='CONFIRMED'  # Default to confirmed since we only create after payment
    )
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    metadata = models.JSONField(default=dict, blank=True, help_text="Payment and booking metadata")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Astrology Booking"
        verbose_name_plural = "Astrology Bookings"
        ordering = ['-preferred_date', '-created_at']
        indexes = [
            models.Index(fields=['astro_book_id']),
            models.Index(fields=['payment_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['preferred_date', 'status']),
            models.Index(fields=['service', 'status']),
        ]

    def __str__(self):
        return f"{self.astro_book_id} - {self.contact_email} - {self.service.title}"

    def save(self, *args, **kwargs):
        # Generate astro_book_id if not set
        if not self.astro_book_id:
            import uuid
            # Format: ASTRO_BOOK_YYYYMMDD_UNIQUEID
            from django.utils import timezone
            today = timezone.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4().hex[:8]).upper()
            self.astro_book_id = f"ASTRO_BOOK_{today}_{unique_id}"
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only send confirmation for new bookings (already confirmed after payment)
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

def upload_to_imagekit(file, file_name, folder=None, is_private=False):
    """Enhanced helper function to upload files to ImageKit with better error handling"""
    try:
        from io import BytesIO
        
        options = UploadFileRequestOptions(
            use_unique_file_name=False,
            folder=folder,
            is_private_file=is_private,
            overwrite_file=True,
            overwrite_ai_tags=True,
            overwrite_tags=True,
            overwrite_custom_metadata=True
        )

        # Handle both file objects and bytes
        if isinstance(file, bytes):
            file = (file_name, BytesIO(file))

        response = imagekit.upload_file(
            file=file,
            file_name=file_name,
            options=options
        )

        # Robust: check for valid response and URL
        if hasattr(response, 'response_metadata') and getattr(response.response_metadata, 'http_status_code', None) == 200:
            if hasattr(response, 'url') and response.url and str(response.url).startswith('http'):
                return response.url
            elif hasattr(response.response_metadata, 'raw') and response.response_metadata.raw.get('url'):
                return response.response_metadata.raw['url']
            else:
                raise Exception(f"ImageKit upload succeeded but no URL returned: {getattr(response.response_metadata, 'raw', {})}")
        else:
            raise Exception(f"ImageKit upload failed: {getattr(response.response_metadata, 'raw', 'No metadata')}")

    except Exception as e:
        import logging
        logging.error(f"ImageKit upload error: {e}")
        raise Exception(f"ImageKit upload error: {e}")