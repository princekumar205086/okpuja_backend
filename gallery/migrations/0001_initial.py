# Generated by Django 5.2 on 2025-07-06 23:38

import django.db.models.deletion
import gallery.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GalleryCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True, verbose_name='title')),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True, verbose_name='slug')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('ARCHIVED', 'Archived')], default='PUBLISHED', max_length=20, verbose_name='status')),
                ('position', models.PositiveSmallIntegerField(default=0, help_text='Position in category listings', verbose_name='position')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
            ],
            options={
                'verbose_name': 'gallery category',
                'verbose_name_plural': 'gallery categories',
                'ordering': ['position', 'title'],
                'indexes': [models.Index(fields=['slug'], name='gallery_gal_slug_68cbd7_idx'), models.Index(fields=['status'], name='gallery_gal_status_148d61_idx'), models.Index(fields=['position'], name='gallery_gal_positio_8c51f6_idx')],
            },
        ),
        migrations.CreateModel(
            name='GalleryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('original_image', models.ImageField(upload_to=gallery.models.gallery_image_upload_path, verbose_name='original image')),
                ('popularity', models.PositiveIntegerField(default=0, help_text='Number of views/likes', verbose_name='popularity')),
                ('is_featured', models.BooleanField(default=False, help_text='Show in featured sections', verbose_name='featured item')),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('ARCHIVED', 'Archived')], default='PUBLISHED', max_length=20, verbose_name='status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('taken_at', models.DateTimeField(blank=True, help_text='Date when the photo was taken', null=True, verbose_name='taken at')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='gallery.gallerycategory', verbose_name='category')),
            ],
            options={
                'verbose_name': 'gallery item',
                'verbose_name_plural': 'gallery items',
                'ordering': ['-is_featured', '-popularity', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GalleryView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='gallery.galleryitem')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'gallery view',
                'verbose_name_plural': 'gallery views',
            },
        ),
        migrations.AddIndex(
            model_name='galleryitem',
            index=models.Index(fields=['category'], name='gallery_gal_categor_735807_idx'),
        ),
        migrations.AddIndex(
            model_name='galleryitem',
            index=models.Index(fields=['status'], name='gallery_gal_status_a5b12c_idx'),
        ),
        migrations.AddIndex(
            model_name='galleryitem',
            index=models.Index(fields=['is_featured'], name='gallery_gal_is_feat_d2223a_idx'),
        ),
        migrations.AddIndex(
            model_name='galleryitem',
            index=models.Index(fields=['popularity'], name='gallery_gal_popular_3cb14d_idx'),
        ),
        migrations.AddIndex(
            model_name='galleryview',
            index=models.Index(fields=['item'], name='gallery_gal_item_id_9bbe7e_idx'),
        ),
        migrations.AddIndex(
            model_name='galleryview',
            index=models.Index(fields=['user'], name='gallery_gal_user_id_24d46e_idx'),
        ),
        migrations.AddIndex(
            model_name='galleryview',
            index=models.Index(fields=['ip_address'], name='gallery_gal_ip_addr_e63cd8_idx'),
        ),
        migrations.AddIndex(
            model_name='galleryview',
            index=models.Index(fields=['created_at'], name='gallery_gal_created_a006d6_idx'),
        ),
    ]
