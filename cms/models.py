from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import uuid
import os

def cms_document_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('cms/documents', filename)

class PublicationStatus(models.TextChoices):
    DRAFT = 'DRAFT', _('Draft')
    PUBLISHED = 'PUBLISHED', _('Published')
    ARCHIVED = 'ARCHIVED', _('Archived')

class CMSPageBase(models.Model):
    """
    Abstract base model for all CMS pages
    """
    title = models.CharField(
        _('title'),
        max_length=255,
        validators=[MinLengthValidator(10)]
    )
    slug = models.SlugField(
        _('URL slug'),
        max_length=255,
        unique=True,
        help_text=_('A URL-friendly version of the title')
    )
    content = models.TextField(
        _('content'),
        validators=[MinLengthValidator(50)]
    )
    meta_title = models.CharField(
        _('meta title'),
        max_length=255,
        blank=True,
        null=True
    )
    meta_description = models.TextField(
        _('meta description'),
        blank=True,
        null=True
    )
    meta_keywords = models.CharField(
        _('meta keywords'),
        max_length=255,
        blank=True,
        null=True
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT
    )
    version = models.PositiveIntegerField(
        _('version'),
        default=1
    )
    is_current = models.BooleanField(
        _('current version'),
        default=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_%(class)s',
        verbose_name=_('created by')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_%(class)s',
        verbose_name=_('updated by')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    published_at = models.DateTimeField(
        _('published at'),
        blank=True,
        null=True
    )

    class Meta:
        abstract = True
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['is_current']),
        ]

    def __str__(self):
        return f"{self.title} (v{self.version})"

    def save(self, *args, **kwargs):
        # Set published_at when status changes to PUBLISHED
        if self.status == PublicationStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        # If this is a new version, mark previous versions as not current
        if self.pk is None and self.is_current:
            self.__class__.objects.filter(
                slug=self.slug
            ).update(is_current=False)
        
        super().save(*args, **kwargs)

class TermsOfService(CMSPageBase):
    attachment = models.FileField(
        _('attachment'),
        upload_to=cms_document_upload_path,
        blank=True,
        null=True
    )
    requires_consent = models.BooleanField(
        _('requires user consent'),
        default=True
    )

    class Meta(CMSPageBase.Meta):
        verbose_name = _('terms of service')
        verbose_name_plural = _('terms of service')

    def get_absolute_url(self):
        return reverse('cms:terms_detail', kwargs={'slug': self.slug})

class PrivacyPolicy(CMSPageBase):
    attachment = models.FileField(
        _('attachment'),
        upload_to=cms_document_upload_path,
        blank=True,
        null=True
    )
    requires_consent = models.BooleanField(
        _('requires user consent'),
        default=True
    )

    class Meta(CMSPageBase.Meta):
        verbose_name = _('privacy policy')
        verbose_name_plural = _('privacy policies')

    def get_absolute_url(self):
        return reverse('cms:privacy_detail', kwargs={'slug': self.slug})

class CancellationRefundPolicy(CMSPageBase):
    refund_period_days = models.PositiveSmallIntegerField(
        _('refund period (days)'),
        default=7
    )
    cancellation_fee_percentage = models.DecimalField(
        _('cancellation fee (%)'),
        max_digits=5,
        decimal_places=2,
        default=0.00
    )

    class Meta(CMSPageBase.Meta):
        verbose_name = _('cancellation & refund policy')
        verbose_name_plural = _('cancellation & refund policies')

    def get_absolute_url(self):
        return reverse('cms:cancellation_detail', kwargs={'slug': self.slug})

class UserConsent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consents'
    )
    terms = models.ForeignKey(
        TermsOfService,
        on_delete=models.CASCADE,
        related_name='user_consents'
    )
    privacy_policy = models.ForeignKey(
        PrivacyPolicy,
        on_delete=models.CASCADE,
        related_name='user_consents'
    )
    ip_address = models.GenericIPAddressField(protocol='both', unpack_ipv4=False)
    user_agent = models.CharField(max_length=255)
    consented_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('user consent')
        verbose_name_plural = _('user consents')
        unique_together = ('user', 'terms', 'privacy_policy')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['consented_at']),
        ]

    def __str__(self):
        return f"Consent by {self.user.email} at {self.consented_at}"