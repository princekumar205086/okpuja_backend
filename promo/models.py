from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Sum
from model_utils import Choices

User = settings.AUTH_USER_MODEL

class PromoCode(models.Model):
    DISCOUNT_TYPES = Choices(
        ('PERCENT', 'Percentage'),
        ('FLAT', 'Flat Amount'),
    )
    
    CODE_TYPES = Choices(
        ('PUBLIC', 'Public (Anyone can use)'),
        ('PRIVATE', 'Private (Specific users)'),
        ('FIRST_ORDER', 'First Order Only'),
        ('USER_SPECIFIC', 'User Specific'),
    )

    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_type = models.CharField(
        max_length=20, 
        choices=DISCOUNT_TYPES,
        default=DISCOUNT_TYPES.PERCENT
    )
    min_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True
    )
    start_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0, editable=False)
    code_type = models.CharField(
        max_length=20,
        choices=CODE_TYPES,
        default=CODE_TYPES.PUBLIC
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_promo_codes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'expiry_date']),
            models.Index(fields=['code_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()}: {self.discount}{'%' if self.discount_type == self.DISCOUNT_TYPES.PERCENT else ''})"

    def clean(self):
        if self.expiry_date <= self.start_date:
            raise ValidationError("Expiry date must be after start date")
        
        if self.discount_type == self.DISCOUNT_TYPES.PERCENT and (self.discount <= 0 or self.discount > 100):
            raise ValidationError("Percentage discount must be between 0 and 100")

    def is_valid_for_user(self, user=None):
        """Check if promo code is valid for a specific user"""
        now = timezone.now()
        
        if not self.is_active:
            return False, "Promo code is inactive"
        
        if now < self.start_date:
            return False, "Promo code not yet active"
        
        if now > self.expiry_date:
            return False, "Promo code has expired"
        
        if self.usage_limit > 0 and self.used_count >= self.usage_limit:
            return False, "Promo code usage limit reached"
        
        if self.code_type == self.CODE_TYPES.FIRST_ORDER and user and user.orders.exists():
            return False, "This promo is only for first order"
        
        return True, "Valid"

    def apply_discount(self, amount):
        """Apply discount to given amount"""
        if self.discount_type == self.DISCOUNT_TYPES.PERCENT:
            discount_amount = (amount * self.discount) / 100
            if self.max_discount_amount:
                discount_amount = min(discount_amount, self.max_discount_amount)
            return amount - discount_amount
        return max(amount - self.discount, 0)

    def increment_usage(self):
        """Atomically increment usage count"""
        PromoCode.objects.filter(pk=self.pk).update(
            used_count=models.F('used_count') + 1
        )
        self.refresh_from_db()


class PromoCodeUsage(models.Model):
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='promo_code_usages'
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['used_at']),
            models.Index(fields=['promo_code', 'user']),
        ]

    @classmethod
    def record_usage(cls, promo_code, user=None, discount_amount=0, original_amount=0):
        """Record promo code usage"""
        return cls.objects.create(
            promo_code=promo_code,
            user=user,
            discount_amount=discount_amount,
            original_amount=original_amount
        )