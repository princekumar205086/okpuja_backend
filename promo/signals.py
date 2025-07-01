# promo/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import PromoCode, PromoCodeUsage
from cart.models import Cart
from payment.models import Order

@receiver(pre_save, sender=PromoCode)
def validate_promo_code(sender, instance, **kwargs):
    """Validate promo code before saving"""
    instance.clean()

@receiver(post_save, sender=PromoCodeUsage)
def update_promo_code_usage_count(sender, instance, created, **kwargs):
    """Update the promo code's used count when a usage is recorded"""
    if created:
        instance.promo_code.increment_usage()

def record_promo_code_usage(promo_code, user=None, cart=None, order=None, original_amount=0):
    """Helper function to record promo code usage"""
    discount_amount = original_amount - promo_code.apply_discount(original_amount)
    PromoCodeUsage.objects.create(
        promo_code=promo_code,
        user=user,
        cart=cart,
        order=order,
        original_amount=original_amount,
        discount_amount=discount_amount
    )

# Connect to cart and order signals if needed
# Example:
# @receiver(post_save, sender=Order)
# def handle_order_promo_code(sender, instance, created, **kwargs):
#     if created and instance.promo_code:
#         record_promo_code_usage(...)