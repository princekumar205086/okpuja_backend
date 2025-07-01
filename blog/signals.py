from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import BlogPost

@receiver(pre_save, sender=BlogPost)
def update_published_at(sender, instance, **kwargs):
    if instance.pk:
        original = BlogPost.objects.get(pk=instance.pk)
        if original.status != 'PUBLISHED' and instance.status == 'PUBLISHED':
            instance.published_at = timezone.now()
    elif instance.status == 'PUBLISHED':
        instance.published_at = timezone.now()