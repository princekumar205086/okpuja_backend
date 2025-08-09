from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import uuid
import os
import logging

logger = logging.getLogger(__name__)

# Initialize ImageKit client
imagekit = ImageKit(
    private_key=settings.IMAGEKIT_PRIVATE_KEY,
    public_key=settings.IMAGEKIT_PUBLIC_KEY,
    url_endpoint=settings.IMAGEKIT_URL_ENDPOINT
)

def upload_to_imagekit(file, file_name, folder="events"):
    """Upload file to ImageKit.io and return URL"""
    try:
        from io import BytesIO
        
        options = UploadFileRequestOptions(
            use_unique_file_name=True,
            folder=folder,
            is_private_file=False,
            overwrite_file=False,
            overwrite_ai_tags=True,
            overwrite_tags=True,
            overwrite_custom_metadata=True
        )

        # Handle file upload
        if hasattr(file, 'read'):
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            file_data = (file_name, BytesIO(file_content))
        else:
            file_data = file

        response = imagekit.upload_file(
            file=file_data,
            file_name=file_name,
            options=options
        )

        # Check for valid response and URL
        if (hasattr(response, 'response_metadata') and 
            getattr(response.response_metadata, 'http_status_code', None) == 200):
            if hasattr(response, 'url') and response.url:
                return response.url
            elif (hasattr(response.response_metadata, 'raw') and 
                  response.response_metadata.raw.get('url')):
                return response.response_metadata.raw['url']
            else:
                raise Exception("ImageKit upload succeeded but no URL returned")
        else:
            raise Exception(f"ImageKit upload failed: {getattr(response.response_metadata, 'raw', 'No metadata')}")

    except Exception as e:
        logger.error(f"ImageKit upload error: {e}")
        raise Exception(f"ImageKit upload error: {e}")

def event_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('events', filename)

class PublicationStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Draft')
    PUBLISHED = 'PUBLISHED', _('Published')
    ARCHIVED = 'ARCHIVED', _('Archived')

class Event(models.Model):
    title = models.CharField(
        _('title'),
        max_length=255
    )
    slug = models.SlugField(
        _('slug'),
        max_length=255,
        unique=True,
        blank=True
    )
    description = models.TextField(
        _('description'),
        blank=True,
        null=True
    )
    # Store uploaded image temporarily (will be uploaded to ImageKit)
    original_image = models.ImageField(
        _('image'),
        upload_to=event_image_upload_path
    )
    
    # ImageKit URLs (will be populated after upload)
    imagekit_original_url = models.URLField(
        _('ImageKit Original URL'),
        max_length=500,
        blank=True,
        null=True
    )
    imagekit_thumbnail_url = models.URLField(
        _('ImageKit Thumbnail URL'),
        max_length=500,
        blank=True,
        null=True
    )
    imagekit_banner_url = models.URLField(
        _('ImageKit Banner URL'),
        max_length=500,
        blank=True,
        null=True
    )
    
    event_date = models.DateField(
        _('event date')
    )
    start_time = models.TimeField(
        _('start time'),
        blank=True,
        null=True
    )
    end_time = models.TimeField(
        _('end time'),
        blank=True,
        null=True
    )
    location = models.CharField(
        _('location'),
        max_length=255,
        blank=True,
        null=True
    )
    registration_link = models.URLField(
        _('registration link'),
        blank=True,
        null=True
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED
    )
    is_featured = models.BooleanField(
        _('featured event'),
        default=False
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ['-event_date', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['event_date']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate slug if not exists
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Upload to ImageKit if image is uploaded and URLs are not set
        if self.original_image and not self.imagekit_original_url:
            try:
                from PIL import Image
                from io import BytesIO
                
                # Upload original image to ImageKit
                original_name = f"event-{self.slug or 'temp'}-original.jpg"
                self.imagekit_original_url = upload_to_imagekit(
                    self.original_image,
                    original_name,
                    folder="events/originals"
                )
                
                # Create and upload thumbnail (400x300)
                img = Image.open(self.original_image)
                img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                
                thumbnail_buffer = BytesIO()
                img.save(thumbnail_buffer, format='JPEG', quality=85)
                thumbnail_buffer.seek(0)
                
                thumbnail_name = f"event-{self.slug or 'temp'}-thumbnail.jpg"
                self.imagekit_thumbnail_url = upload_to_imagekit(
                    (thumbnail_name, thumbnail_buffer),
                    thumbnail_name,
                    folder="events/thumbnails"
                )
                
                # Create and upload banner (1200x600)
                img = Image.open(self.original_image)
                img.thumbnail((1200, 600), Image.Resampling.LANCZOS)
                
                banner_buffer = BytesIO()
                img.save(banner_buffer, format='JPEG', quality=90)
                banner_buffer.seek(0)
                
                banner_name = f"event-{self.slug or 'temp'}-banner.jpg"
                self.imagekit_banner_url = upload_to_imagekit(
                    (banner_name, banner_buffer),
                    banner_name,
                    folder="events/banners"
                )
                
                logger.info(f"Successfully uploaded images to ImageKit for event: {self.title}")
                
            except Exception as e:
                logger.error(f"Failed to upload images to ImageKit for event {self.title}: {e}")
                # Continue saving even if ImageKit upload fails
        
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('misc:event_detail', kwargs={'slug': self.slug})

class JobOpening(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', _('Full Time')
        PART_TIME = 'PART_TIME', _('Part Time')
        CONTRACT = 'CONTRACT', _('Contract')
        INTERNSHIP = 'INTERNSHIP', _('Internship')
        VOLUNTEER = 'VOLUNTEER', _('Volunteer')

    title = models.CharField(
        _('title'),
        max_length=255
    )
    slug = models.SlugField(
        _('slug'),
        max_length=255,
        unique=True,
        blank=True
    )
    description = models.TextField(
        _('description')
    )
    responsibilities = models.TextField(
        _('responsibilities'),
        blank=True,
        null=True
    )
    requirements = models.TextField(
        _('requirements'),
        blank=True,
        null=True
    )
    job_type = models.CharField(
        _('job type'),
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME
    )
    location = models.CharField(
        _('location'),
        max_length=255,
        blank=True,
        null=True
    )
    salary_range = models.CharField(
        _('salary range'),
        max_length=100,
        blank=True,
        null=True
    )
    application_deadline = models.DateTimeField(
        _('application deadline')
    )
    application_link = models.URLField(
        _('application link'),
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        _('active'),
        default=True
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('job opening')
        verbose_name_plural = _('job openings')
        ordering = ['-application_deadline', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['job_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['application_deadline']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
    def is_open(self):
        return self.is_active and self.application_deadline > timezone.now()
        
    def get_absolute_url(self):
        return reverse('misc:job_detail', kwargs={'slug': self.slug})

class ContactUsStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    REPLIED = 'REPLIED', _('Replied')
    CLOSED = 'CLOSED', _('Closed')

class ContactUs(models.Model):
    class ContactSubject(models.TextChoices):
        GENERAL = 'GENERAL', _('General Inquiry')
        SERVICE = 'SERVICE', _('Service Inquiry')
        BOOKING = 'BOOKING', _('Booking Issue')
        PAYMENT = 'PAYMENT', _('Payment Issue')
        TECHNICAL = 'TECHNICAL', _('Technical Issue')
        JOB = 'JOB', _('Job Application')
        OTHER = 'OTHER', _('Other')

    name = models.CharField(
        _('name'),
        max_length=255
    )
    email = models.EmailField(
        _('email')
    )
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        null=True
    )
    subject = models.CharField(
        _('subject'),
        max_length=20,
        choices=ContactSubject.choices,
        default=ContactSubject.GENERAL
    )
    message = models.TextField(
        _('message')
    )
    status = models.CharField(
        _('status'),
        max_length=10,
        choices=ContactUsStatus.choices,
        default=ContactUsStatus.PENDING
    )
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        blank=True,
        null=True
    )
    user_agent = models.CharField(
        _('user agent'),
        max_length=255,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    replied_at = models.DateTimeField(
        _('replied at'),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('contact us message')
        verbose_name_plural = _('contact us messages')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['subject']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Contact from {self.name} - {self.subject}"

    def mark_as_replied(self):
        if self.status != ContactUsStatus.REPLIED:
            self.status = ContactUsStatus.REPLIED
            self.replied_at = timezone.now()
            self.save()
            
    def mark_as_closed(self):
        if self.status != ContactUsStatus.CLOSED:
            self.status = ContactUsStatus.CLOSED
            self.save()