from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit
import uuid
import os

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
    original_image = models.ImageField(
        _('image'),
        upload_to=event_image_upload_path
    )
    
    # Image specifications
    thumbnail = ImageSpecField(
        source='original_image',
        processors=[ResizeToFill(400, 300)],
        format='JPEG',
        options={'quality': 85}
    )
    
    banner = ImageSpecField(
        source='original_image',
        processors=[ResizeToFit(1200, 600)],
        format='JPEG',
        options={'quality': 90}
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
        if not self.slug:
            self.slug = slugify(self.title)
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