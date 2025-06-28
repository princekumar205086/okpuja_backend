from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User, UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        if instance.is_superuser:
            instance.role = User.Role.ADMIN
            instance.save()

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        subject = 'Welcome to OKPUJA'
        message = f"""
        Thank you for registering with OKPUJA!
        Your account is pending verification.
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False,
        )