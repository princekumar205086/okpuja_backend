import os
import re
import uuid
from datetime import timedelta
from io import BytesIO

from PIL import Image
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from rest_framework import serializers

# Initialize ImageKit client with enhanced configuration
imagekit = ImageKit(
    private_key=settings.IMAGEKIT_PRIVATE_KEY,
    public_key=settings.IMAGEKIT_PUBLIC_KEY,
    url_endpoint=settings.IMAGEKIT_URL_ENDPOINT
)


def validate_indian_phone_number(value):
    """
    Validate Indian phone numbers with the following formats:
    - +91XXXXXXXXXX
    - +91 XX XXXX XXXX
    - 0XXXXXXXXXX
    - 0XX XXXX XXXX
    - XXXXXXXXXX
    """
    pattern = r'^(\+91[\-\s]?)?[0]?(91)?[6789]\d{9}$'
    if not re.match(pattern, value):
        raise ValueError(
            "Enter a valid Indian phone number (10 digits starting with 6-9)"
        )


def upload_to_imagekit(file, file_name, folder=None, is_private=False):
    """Enhanced helper function to upload files to ImageKit with better error handling"""
    try:
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


class CustomUserManager(BaseUserManager):
    """Enhanced user manager with better validation"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Users must have an email address'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('account_status', User.AccountStatus.ACTIVE)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Enhanced User model with India-specific phone validation"""

    class Role(models.TextChoices):
        USER = 'USER', _('User')
        ADMIN = 'ADMIN', _('Administrator')
        EMPLOYEE = 'EMPLOYEE', _('Employee/Priest')

    class AccountStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACTIVE = 'ACTIVE', _('Active')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        DEACTIVATED = 'DEACTIVATED', _('Deactivated')

    # Core fields
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=150, blank=True)

    # India-specific phone number field
    phone = models.CharField(
        _('phone number'),
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        validators=[validate_indian_phone_number],
        help_text=_("Enter 10-digit Indian phone number (starting with 6-9)")
    )

    # Status fields
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.USER
    )
    account_status = models.CharField(
        _('account status'),
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING
    )

    # Verification fields
    email_verified = models.BooleanField(_('email verified'), default=False)
    verification_token = models.UUIDField(
        _('verification token'),
        default=uuid.uuid4,
        editable=False
    )

    # OTP Fields
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)

    # Password Reset
    reset_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        null=True,
        blank=True
    )
    reset_token_created_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)

    # Permissions
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['account_status']),
            models.Index(fields=['phone']),
        ]

    def clean(self):
        """Normalize phone number before saving"""
        super().clean()
        if self.phone:
            # Remove all non-digit characters except leading +
            self.phone = re.sub(r'(?!^\+)\D', '', self.phone)
            # Ensure proper formatting
            if self.phone.startswith('+91'):
                self.phone = '+91' + self.phone[3:]
            elif self.phone.startswith('91'):
                self.phone = '+91' + self.phone[2:]
            elif self.phone.startswith('0'):
                self.phone = '+91' + self.phone[1:]
            else:
                self.phone = '+91' + self.phone

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    def generate_otp(self):
        """Generate and save OTP with enhanced security"""
        from random import randint
        self.otp = str(randint(10 ** (settings.OTP_LENGTH - 1), 10 ** settings.OTP_LENGTH - 1))
        self.otp_created_at = timezone.now()
        self.otp_verified = False
        self.save(update_fields=['otp', 'otp_created_at', 'otp_verified'])
        return self.otp

    def verify_otp(self, otp):
        """Enhanced OTP verification with security checks"""
        if not self.otp or not self.otp_created_at:
            return False

        expiry_time = self.otp_created_at + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        if timezone.now() > expiry_time:
            return False

        if self.otp == otp:
            self.otp_verified = True
            self.otp = None
            self.otp_created_at = None
            self.save(update_fields=['otp_verified', 'otp', 'otp_created_at'])
            return True
        return False

    @property
    def formatted_phone(self):
        """Return phone number in standardized Indian format"""
        if not self.phone:
            return ""
        if self.phone.startswith('+91'):
            return f"+91 {self.phone[3:5]} {self.phone[5:9]} {self.phone[9:]}"
        return self.phone

    @property
    def full_name(self):
        """Get user's full name from profile if available"""
        if hasattr(self, 'profile'):
            return self.profile.__str__()
        return self.email

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def is_public_user(self):
        return self.role == self.Role.USER


class UserProfile(models.Model):
    """Enhanced UserProfile model with better image handling"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user')
    )
    first_name = models.CharField(_('first name'), max_length=100)
    last_name = models.CharField(_('last name'), max_length=100)
    dob = models.DateField(_('date of birth'), blank=True, null=True)

    # Image fields
    profile_picture_url = ImageKitField(_('profile picture URL'))
    profile_thumbnail_url = ImageKitField(_('profile thumbnail URL'))

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save_profile_picture(self, image_file):
        """
        Enhanced profile picture upload with better file handling
        and error management
        """
        try:
            # Read file content once
            if hasattr(image_file, 'read'):
                file_bytes = image_file.read()
            else:
                with open(image_file, 'rb') as f:
                    file_bytes = f.read()

            # Validate image
            try:
                Image.open(BytesIO(file_bytes)).verify()
            except Exception as e:
                raise serializers.ValidationError(f"Invalid image file: {str(e)}")

            # Generate unique filename
            original_filename = getattr(image_file, 'name', 'profile.jpg')
            ext = os.path.splitext(original_filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                raise serializers.ValidationError("Unsupported image format. Please upload JPG, JPEG, PNG, or GIF.")

            filename = f"profile_{self.user.id}_{uuid.uuid4()}{ext}"

            # Upload original image
            self.profile_picture_url = upload_to_imagekit(
                file_bytes,
                filename,
                folder="user_profiles"
            )

            # Create and upload thumbnail
            thumbnail_bytes = self._create_thumbnail(file_bytes)
            thumbnail_filename = f"thumb_{filename}"
            self.profile_thumbnail_url = upload_to_imagekit(
                thumbnail_bytes,
                thumbnail_filename,
                folder="user_profiles/thumbnails"
            )

            self.save()
            return True

        except Exception as e:
            # Log the error in production
            print(f"Error saving profile picture: {str(e)}")
            raise

    def _create_thumbnail(self, image_bytes, size=(150, 150), quality=80):
        """Create optimized thumbnail from image bytes"""
        try:
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


class Address(models.Model):
    """Enhanced Address model with better validation"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('user')
    )
    address_line1 = models.CharField(_('address line 1'), max_length=255)
    address_line2 = models.CharField(
        _('address line 2'),
        max_length=255,
        blank=True,
        null=True
    )
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(
        _('country'),
        max_length=100,
        default='India'
    )
    landmark = models.CharField(
        _('landmark'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Nearby landmark for easy identification')
    )
    is_default = models.BooleanField(_('default address'), default=False)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ['-is_default', '-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_address_per_user'
            )
        ]

    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.postal_code}"

    def get_full_address(self):
        """Get full address formatted for Google Maps"""
        address_parts = [self.address_line1]
        
        if self.address_line2:
            address_parts.append(self.address_line2)
        
        if self.landmark:
            address_parts.append(f"Near {self.landmark}")
        
        address_parts.extend([
            self.city,
            self.state,
            self.postal_code,
            self.country
        ])
        
        return ", ".join(filter(None, address_parts))

    def save(self, *args, **kwargs):
        """Ensure only one default address per user"""
        if self.is_default:
            # Remove default status from other addresses
            Address.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class SMSLog(models.Model):
    """Enhanced SMS logging model"""
    phone = models.CharField(max_length=15)
    message = models.TextField()
    status = models.CharField(max_length=20)
    response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('SMS Log')
        verbose_name_plural = _('SMS Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"SMS to {self.phone} at {self.created_at}"


class PanCard(models.Model):
    """Enhanced PanCard model with better image handling"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='pancard',
        verbose_name=_('user')
    )
    pan_number = models.CharField(
        _('PAN number'),
        max_length=10,
        unique=True
    )

    # Image fields
    pan_card_image_url = ImageKitField(_('PAN card image URL'))
    pan_card_thumbnail_url = ImageKitField(_('PAN card thumbnail URL'))

    # Verification status
    is_verified = models.BooleanField(_('verified'), default=False)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('PAN Card')
        verbose_name_plural = _('PAN Cards')
        ordering = ['-updated_at']

    def __str__(self):
        return self.pan_number

    def save_pan_card_image(self, image_file):
        """Enhanced PAN card image upload with validation"""
        try:
            # Read file content once
            if hasattr(image_file, 'read'):
                file_bytes = image_file.read()
            else:
                with open(image_file, 'rb') as f:
                    file_bytes = f.read()

            # Validate image
            try:
                Image.open(BytesIO(file_bytes)).verify()
            except Exception as e:
                raise serializers.ValidationError(f"Invalid image file: {str(e)}")

            # Generate unique filename
            original_filename = getattr(image_file, 'name', 'pancard.jpg')
            ext = os.path.splitext(original_filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png']:
                raise serializers.ValidationError("Only JPG/PNG images are supported for PAN cards.")

            filename = f"pancard_{self.user.id}_{uuid.uuid4()}{ext}"

            # Upload original image
            self.pan_card_image_url = upload_to_imagekit(
                file_bytes,
                filename,
                folder="pancards"
            )

            # Create and upload thumbnail
            thumbnail_bytes = self._create_thumbnail(file_bytes)
            thumbnail_filename = f"thumb_{filename}"
            self.pan_card_thumbnail_url = upload_to_imagekit(
                thumbnail_bytes,
                thumbnail_filename,
                folder="pancards/thumbnails"
            )

            self.save()
            return True

        except Exception as e:
            # Log the error in production
            print(f"Error saving PAN card image: {str(e)}")
            raise

    def _create_thumbnail(self, image_bytes, size=(200, 150), quality=85):
        """Create optimized thumbnail for PAN card"""
        try:
            with Image.open(BytesIO(image_bytes)) as img:
                img = img.convert('RGB')

                # PAN cards often have different aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)

                thumb_io = BytesIO()
                img.save(thumb_io, format='JPEG', quality=quality, optimize=True)
                thumb_io.seek(0)
                return thumb_io.getvalue()
        except Exception as e:
            print(f"Error creating PAN card thumbnail: {str(e)}")
            raise
