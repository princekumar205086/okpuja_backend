from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
import uuid
import os

User = settings.AUTH_USER_MODEL

def blog_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('blog', str(instance.user.id), filename)

class PublicationStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published'
    ARCHIVED = 'ARCHIVED', 'Archived'

class BlogCategory(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blog_categories',
        verbose_name='Author'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Category Name'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='URL Slug',
        help_text='A URL-friendly version of the category name'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Description'
    )
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Meta Title'
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Meta Keywords'
    )
    meta_description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Meta Description'
    )
    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        verbose_name='Status'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Blog Category'
        verbose_name_plural = 'Blog Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})

class BlogTag(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Tag Name'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='URL Slug'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Description'
    )
    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED,
        verbose_name='Status'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Blog Tag'
        verbose_name_plural = 'Blog Tags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag_detail', kwargs={'slug': self.slug})

class BlogPost(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_posts',
        verbose_name='Author'
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        related_name='posts',
        null=True,
        blank=True,
        verbose_name='Category'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Post Title'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='URL Slug',
        help_text='A URL-friendly version of the post title'
    )
    excerpt = models.TextField(
        blank=True,
        null=True,
        verbose_name='Excerpt',
        help_text='A short summary of the post'
    )
    content = models.TextField(
        verbose_name='Content'
    )
    featured_image = models.ImageField(
        upload_to=blog_image_upload_path,
        verbose_name='Featured Image',
        blank=True,
        null=True
    )
    featured_image_thumbnail = ImageSpecField(
        source='featured_image',
        processors=[ResizeToFill(800, 450)],
        format='JPEG',
        options={'quality': 80}
    )
    youtube_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='YouTube URL'
    )
    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        verbose_name='Status'
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Featured Post'
    )
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name='View Count'
    )
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Meta Title'
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Meta Keywords'
    )
    meta_description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Meta Description'
    )
    tags = models.ManyToManyField(
        BlogTag,
        related_name='posts',
        blank=True,
        verbose_name='Tags'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Published At'
    )

    class Meta:
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['published_at']),
            models.Index(fields=['view_count']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set published_at when status changes to PUBLISHED
        if self.status == PublicationStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

class BlogComment(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Post'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_comments',
        verbose_name='User'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Parent Comment'
    )
    content = models.TextField(
        verbose_name='Comment'
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name='Approved'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        verbose_name = 'Blog Comment'
        verbose_name_plural = 'Blog Comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        return f"Comment by {self.user.email} on {self.post.title}"

class BlogLike(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Post'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_likes',
        verbose_name='User'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        verbose_name = 'Blog Like'
        verbose_name_plural = 'Blog Likes'
        unique_together = ('post', 'user')
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Like by {self.user.email} on {self.post.title}"

class BlogView(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Post'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_views',
        verbose_name='User'
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='IP Address',
        null=True,
        blank=True
    )
    user_agent = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='User Agent'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        verbose_name = 'Blog View'
        verbose_name_plural = 'Blog Views'
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        viewer = self.user.email if self.user else self.ip_address
        return f"View by {viewer} on {self.post.title}"