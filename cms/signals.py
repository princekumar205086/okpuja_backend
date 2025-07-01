from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TermsOfService, PrivacyPolicy, CancellationRefundPolicy

@receiver(pre_save, sender=TermsOfService)
@receiver(pre_save, sender=PrivacyPolicy)
@receiver(pre_save, sender=CancellationRefundPolicy)
def handle_cms_page_save(sender, instance, **kwargs):
    # Set published_at when status changes to PUBLISHED
    if instance.pk:
        original = sender.objects.get(pk=instance.pk)
        if original.status != 'PUBLISHED' and instance.status == 'PUBLISHED':
            instance.published_at = timezone.now()
    elif instance.status == 'PUBLISHED':
        instance.published_at = timezone.now()
    
    # Auto-increment version if content changed significantly
    if instance.pk and 'content' in instance.get_dirty_fields():
        latest_version = sender.objects.filter(
            slug=instance.slug
        ).order_by('-version').first()
        if latest_version:
            instance.version = latest_version.version + 1
            instance.is_current = True
            sender.objects.filter(
                slug=instance.slug
            ).update(is_current=False)