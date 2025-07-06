import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from imagekitio_storage.storage import MediaStorage


def user_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('users', str(instance.user.id), filename)


def pancard_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('users', str(instance.user.id), 'pancards', filename)


class CustomUserManager(BaseUserManager):
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
        extra_fields.setdefault('is_active', True)  # Added from new code
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = 'USER', _('User')
        ADMIN = 'ADMIN', _('Administrator')
        EMPLOYEE = 'EMPLOYEE', _('Employee/Priest')

    class AccountStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACTIVE = 'ACTIVE', _('Active')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        DEACTIVATED = 'DEACTIVATED', _('Deactivated')

    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=150, blank=True)

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'"
    )
    phone = models.CharField(
        _('phone number'),
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )

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
    verification_token = models.UUIDField(_('verification token'), default=uuid.uuid4, editable=False)

    # OTP Fields
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)

    # Password Reset
    reset_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
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
        ]

    def __str__(self):
        return self.email

    def generate_otp(self):
        """Generate and save OTP"""
        from random import randint
        self.otp = str(randint(10 ** (settings.OTP_LENGTH - 1), 10 ** settings.OTP_LENGTH - 1))
        self.otp_created_at = timezone.now()
        self.otp_verified = False
        self.save(update_fields=['otp', 'otp_created_at', 'otp_verified'])
        return self.otp

    def verify_otp(self, otp):
        """Verify OTP with expiry check"""
        if not self.otp or not self.otp_created_at:
            return False

        expiry_time = self.otp_created_at + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        if timezone.now() > expiry_time:
            return False

        if self.otp == otp:
            self.otp_verified = True
            self.otp = None  # Clear OTP after verification
            self.otp_created_at = None
            self.save(update_fields=['otp_verified', 'otp', 'otp_created_at'])
            return True
        return False

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def is_public_user(self):
        return self.role == self.Role.USER


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user')
    )
    first_name = models.CharField(_('first name'), max_length=100)
    last_name = models.CharField(_('last name'), max_length=100)
    dob = models.DateField(_('date of birth'), blank=True, null=True)

    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to=user_upload_path,
        blank=True,
        null=True,
        default=None,
        storage=MediaStorage()  # Store only profile_picture on ImageKit
    )
    profile_thumbnail = ImageSpecField(
        source='profile_picture',
        processors=[ResizeToFill(150, 150)],
        format='JPEG',
        options={'quality': 80}
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('user')
    )
    address_line1 = models.CharField(_('address line 1'), max_length=255)
    address_line2 = models.CharField(_('address line 2'), max_length=255, blank=True, null=True)
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(_('country'), max_length=100, default='India')
    is_default = models.BooleanField(_('default address'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_address_per_user'
            )
        ]

    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.postal_code}"


class SMSLog(models.Model):
    phone = models.CharField(max_length=15)
    message = models.TextField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMS to {self.phone}"


class PanCard(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='pancard',
        verbose_name=_('user')
    )
    pan_number = models.CharField(_('PAN number'), max_length=10, unique=True)
    pan_card_image = models.ImageField(
        _('PAN card image'),
        upload_to=pancard_upload_path,
        blank=True,
        null=True
    )
    pan_card_thumbnail = ImageSpecField(
        source='pan_card_image',
        processors=[ResizeToFill(150, 150)],
        format='JPEG',
        options={'quality': 80}
    )
    is_verified = models.BooleanField(_('verified'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('PAN Card')
        verbose_name_plural = _('PAN Cards')

    def __str__(self):
        return self.pan_number
