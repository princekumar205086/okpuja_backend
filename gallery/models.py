from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit, SmartResize
import uuid
import os

def gallery_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('gallery', str(instance.category.id), filename)

class PublicationStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Draft')
    PUBLISHED = 'PUBLISHED', _('Published')
    ARCHIVED = 'ARCHIVED', _('Archived')

class GalleryCategory(models.Model):
    title = models.CharField(
        _('title'),
        max_length=255,
        unique=True
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
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED
    )
    position = models.PositiveSmallIntegerField(
        _('position'),
        default=0,
        help_text=_('Position in category listings')
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
        verbose_name = _('gallery category')
        verbose_name_plural = _('gallery categories')
        ordering = ['position', 'title']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['position']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('gallery:category_detail', kwargs={'slug': self.slug})

class GalleryItem(models.Model):
    category = models.ForeignKey(
        GalleryCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('category')
    )
    title = models.CharField(
        _('title'),
        max_length=255
    )
    description = models.TextField(
        _('description'),
        blank=True,
        null=True
    )
    original_image = models.ImageField(
        _('original image'),
        upload_to=gallery_image_upload_path
    )
    
    # Image specifications
    thumbnail = ImageSpecField(
        source='original_image',
        processors=[SmartResize(300, 300)],
        format='JPEG',
        options={'quality': 85}
    )
    
    medium = ImageSpecField(
        source='original_image',
        processors=[SmartResize(800, 600)],
        format='JPEG',
        options={'quality': 90}
    )
    
    large = ImageSpecField(
        source='original_image',
        processors=[ResizeToFit(1200, 1200)],
        format='JPEG',
        options={'quality': 95}
    )
    
    web_optimized = ImageSpecField(
        source='original_image',
        processors=[ResizeToFit(1600, 1600)],
        format='JPEG',
        options={'quality': 90, 'progressive': True}
    )
    
    popularity = models.PositiveIntegerField(
        _('popularity'),
        default=0,
        help_text=_('Number of views/likes')
    )
    is_featured = models.BooleanField(
        _('featured item'),
        default=False,
        help_text=_('Show in featured sections')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    taken_at = models.DateTimeField(
        _('taken at'),
        blank=True,
        null=True,
        help_text=_('Date when the photo was taken')
    )

    class Meta:
        verbose_name = _('gallery item')
        verbose_name_plural = _('gallery items')
        ordering = ['-is_featured', '-popularity', '-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['popularity']),
        ]

    def __str__(self):
        return self.title

    def increment_popularity(self):
        self.popularity += 1
        self.save(update_fields=['popularity'])

class GalleryView(models.Model):
    item = models.ForeignKey(
        GalleryItem,
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('gallery view')
        verbose_name_plural = _('gallery views')
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['user']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"View of {self.item.title} at {self.created_at}"