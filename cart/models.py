# cart/models.py
from django.db import models
from django.conf import settings
from puja.models import PujaService, Package
from astrology.models import AstrologyService
from promo.models import PromoCode

User = settings.AUTH_USER_MODEL

class ServiceType(models.TextChoices):
    PUJA = 'PUJA', 'Puja Service'
    ASTROLOGY = 'ASTROLOGY', 'Astrology Service'

class Cart(models.Model):
    class StatusChoices(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        CONVERTED = 'CONVERTED', 'Converted to Booking'
        ABANDONED = 'ABANDONED', 'Abandoned'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    service_type = models.CharField(
        max_length=10,
        choices=ServiceType.choices,
        default=ServiceType.PUJA
    )
    # Puja service fields
    puja_service = models.ForeignKey(
        PujaService, 
        on_delete=models.CASCADE, 
        related_name='carts',
        null=True,
        blank=True
    )
    package = models.ForeignKey(
        Package, 
        on_delete=models.CASCADE, 
        related_name='carts',
        null=True,
        blank=True
    )
    # Astrology service fields
    astrology_service = models.ForeignKey(
        AstrologyService,
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        blank=True
    )
    selected_date = models.DateField()
    selected_time = models.CharField(max_length=100)
    promo_code = models.ForeignKey(
        PromoCode, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='carts'
    )
    cart_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=10, 
        choices=StatusChoices.choices, 
        default=StatusChoices.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"Cart {self.cart_id} - {self.user.email}"

    def clean(self):
        """Validate that either puja or astrology service is set"""
        from django.core.exceptions import ValidationError
        if not self.puja_service and not self.astrology_service:
            raise ValidationError("Either puja_service or astrology_service must be set")
        if self.puja_service and self.astrology_service:
            raise ValidationError("Only one service type can be set at a time")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def service(self):
        """Get the associated service regardless of type"""
        return self.puja_service or self.astrology_service

    @property
    def total_price(self):
        """Calculate total price after applying promo code"""
        base_price = 0
        if self.puja_service and self.package:
            base_price = self.package.price
        elif self.astrology_service:
            base_price = self.astrology_service.service_price
        
        if not self.promo_code:
            return base_price
            
        if self.promo_code.discount_type == 'PERCENTAGE':
            return base_price * (1 - self.promo_code.discount / 100)
        return base_price - self.promo_code.discount