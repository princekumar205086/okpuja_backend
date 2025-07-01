from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import GalleryCategory

@receiver(pre_save, sender=GalleryCategory)
def create_category_slug(sender, instance, **kwargs):
    if not instance.slug:
        from django.utils.text import slugify
        instance.slug = slugify(instance.title)