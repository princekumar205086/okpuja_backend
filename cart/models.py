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
        
        # Single cart logic: deactivate other active carts for this user
        if self.status == self.StatusChoices.ACTIVE:
            Cart.objects.filter(
                user=self.user, 
                status=self.StatusChoices.ACTIVE
            ).exclude(pk=self.pk).update(status=self.StatusChoices.INACTIVE)
        
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
    
    def can_be_deleted(self):
        """Check if cart can be safely deleted"""
        # Cart can be deleted if:
        # 1. No payments exist, OR
        # 2. All payments are FAILED/CANCELLED, OR
        # 3. Cart is CONVERTED and has successful booking, OR
        # 4. Pending payments are older than 30 minutes (auto-cleanup)
        from payment.models import Payment, PaymentStatus
        from django.utils import timezone
        from datetime import timedelta
        
        payments = Payment.objects.filter(cart=self)
        if not payments.exists():
            return True
            
        # Check if all payments are failed/cancelled
        failed_statuses = [PaymentStatus.FAILED, PaymentStatus.CANCELLED]
        if all(p.status in failed_statuses for p in payments):
            return True
            
        # Check if cart is converted with successful booking
        if self.status == self.StatusChoices.CONVERTED:
            successful_payments = payments.filter(status=PaymentStatus.SUCCESS)
            if successful_payments.exists() and successful_payments.first().booking:
                return True
        
        # Check for pending payments older than 30 minutes
        pending_payments = payments.filter(status=PaymentStatus.PENDING)
        if pending_payments.exists():
            cutoff_time = timezone.now() - timedelta(minutes=30)
            old_pending_payments = pending_payments.filter(created_at__lt=cutoff_time)
            
            # If all pending payments are old, cart can be deleted
            if old_pending_payments.count() == pending_payments.count():
                return True
                
        return False
    
    def get_deletion_info(self):
        """Get detailed information about why cart cannot be deleted and when it can be"""
        from payment.models import Payment, PaymentStatus
        from django.utils import timezone
        from datetime import timedelta
        
        payments = Payment.objects.filter(cart=self)
        if not payments.exists():
            return {"can_delete": True, "reason": "No payments associated"}
            
        # Check for pending payments
        pending_payments = payments.filter(status=PaymentStatus.PENDING)
        if pending_payments.exists():
            cutoff_time = timezone.now() - timedelta(minutes=30)
            newest_payment = pending_payments.order_by('-created_at').first()
            
            if newest_payment.created_at < cutoff_time:
                return {
                    "can_delete": True, 
                    "reason": "Pending payments are older than 30 minutes"
                }
            else:
                # Calculate remaining wait time
                wait_until = newest_payment.created_at + timedelta(minutes=30)
                remaining_minutes = int((wait_until - timezone.now()).total_seconds() / 60)
                remaining_minutes = max(0, remaining_minutes)  # Don't show negative time
                
                return {
                    "can_delete": False,
                    "reason": "pending_payment_wait",
                    "message": f"Cart has pending payment(s). Please wait {remaining_minutes} more minute(s) before deletion or complete the payment.",
                    "wait_time_minutes": remaining_minutes,
                    "retry_after": wait_until.isoformat(),
                    "payment_count": pending_payments.count(),
                    "latest_payment_age_minutes": int((timezone.now() - newest_payment.created_at).total_seconds() / 60)
                }
        
        # Other reasons cart cannot be deleted
        if self.status == self.StatusChoices.CONVERTED:
            return {
                "can_delete": False,
                "reason": "Cart is already converted to booking"
            }
            
        return {
            "can_delete": self.can_be_deleted(),
            "reason": "Cart has active payments"
        }
    
    def auto_cleanup_old_payments(self):
        """Auto-cleanup pending payments older than 30 minutes"""
        from payment.models import Payment, PaymentStatus
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(minutes=30)
        old_pending_payments = Payment.objects.filter(
            cart=self,
            status=PaymentStatus.PENDING,
            created_at__lt=cutoff_time
        )
        
        if old_pending_payments.exists():
            # Mark old pending payments as cancelled
            updated_count = old_pending_payments.update(
                status=PaymentStatus.CANCELLED,
                updated_at=timezone.now()
            )
            
            return {
                "cleaned_up": True,
                "payments_cancelled": updated_count,
                "message": f"Auto-cancelled {updated_count} pending payment(s) older than 30 minutes"
            }
        
        return {"cleaned_up": False, "payments_cancelled": 0}
    
    def clear_if_converted(self):
        """Clear cart data if it's converted to booking"""
        if self.status == self.StatusChoices.CONVERTED and self.can_be_deleted():
            # Set cart reference to null in payments before deletion
            Payment.objects.filter(cart=self).update(cart=None)
            self.delete()
            return True
        return False