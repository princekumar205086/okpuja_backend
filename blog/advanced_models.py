"""
Enhanced Blog Analytics and Performance Models
Provides detailed analytics and performance tracking for blog content
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
import json

from .models import BlogPost, BlogCategory, User

class BlogAnalytics(models.Model):
    """Store daily analytics data for blog performance"""
    date = models.DateField(verbose_name='Analytics Date')
    total_views = models.PositiveIntegerField(default=0, verbose_name='Total Views')
    unique_visitors = models.PositiveIntegerField(default=0, verbose_name='Unique Visitors')
    total_likes = models.PositiveIntegerField(default=0, verbose_name='Total Likes')
    total_comments = models.PositiveIntegerField(default=0, verbose_name='Total Comments')
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Bounce Rate %')
    avg_time_on_page = models.DurationField(null=True, blank=True, verbose_name='Average Time on Page')
    
    # Traffic sources
    direct_traffic = models.PositiveIntegerField(default=0, verbose_name='Direct Traffic')
    search_traffic = models.PositiveIntegerField(default=0, verbose_name='Search Traffic')
    social_traffic = models.PositiveIntegerField(default=0, verbose_name='Social Traffic')
    referral_traffic = models.PositiveIntegerField(default=0, verbose_name='Referral Traffic')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Blog Analytics'
        verbose_name_plural = 'Blog Analytics'
        unique_together = ('date',)
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['total_views']),
        ]
    
    def __str__(self):
        return f"Analytics for {self.date}"

class BlogPostPerformance(models.Model):
    """Track individual post performance metrics"""
    post = models.OneToOneField(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='performance',
        verbose_name='Blog Post'
    )
    
    # Engagement metrics
    avg_reading_time = models.DurationField(null=True, blank=True, verbose_name='Average Reading Time')
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Completion Rate %')
    scroll_depth_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Average Scroll Depth %')
    
    # SEO metrics
    search_impressions = models.PositiveIntegerField(default=0, verbose_name='Search Impressions')
    search_clicks = models.PositiveIntegerField(default=0, verbose_name='Search Clicks')
    click_through_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='CTR %')
    avg_position = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Average Search Position')
    
    # Social metrics
    social_shares = models.PositiveIntegerField(default=0, verbose_name='Social Shares')
    social_mentions = models.PositiveIntegerField(default=0, verbose_name='Social Mentions')
    
    # Quality score (calculated)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Quality Score')
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Post Performance'
        verbose_name_plural = 'Post Performance'
        ordering = ['-quality_score']
    
    def __str__(self):
        return f"Performance for {self.post.title}"
    
    def calculate_quality_score(self):
        """Calculate quality score based on various metrics"""
        score = 0
        
        # Engagement factor (40% of score)
        if self.post.view_count > 0:
            like_ratio = (self.post.likes.count() / self.post.view_count) * 100
            comment_ratio = (self.post.comments.filter(is_approved=True).count() / self.post.view_count) * 100
            engagement_score = min(40, (like_ratio + comment_ratio) * 2)
            score += engagement_score
        
        # SEO factor (30% of score)
        if self.search_impressions > 0:
            ctr_score = min(30, self.click_through_rate * 3)
            score += ctr_score
        
        # Content quality factor (20% of score)
        content_score = 0
        if self.post.meta_title:
            content_score += 5
        if self.post.meta_description:
            content_score += 5
        if self.post.featured_image:
            content_score += 5
        if len(self.post.content) > 300:
            content_score += 5
        score += content_score
        
        # Social factor (10% of score)
        social_score = min(10, self.social_shares * 0.5)
        score += social_score
        
        self.quality_score = round(score, 2)
        return self.quality_score

class BlogSearchQuery(models.Model):
    """Track internal blog search queries"""
    query = models.CharField(max_length=255, verbose_name='Search Query')
    results_count = models.PositiveIntegerField(default=0, verbose_name='Results Count')
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_searches',
        verbose_name='User'
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='IP Address',
        null=True,
        blank=True,
        protocol='both',
        unpack_ipv4=False
    )
    clicked_result = models.ForeignKey(
        BlogPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_clicks',
        verbose_name='Clicked Result'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Search Query'
        verbose_name_plural = 'Search Queries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['created_at']),
            models.Index(fields=['results_count']),
        ]
    
    def __str__(self):
        return f"Search: {self.query} ({self.results_count} results)"

class BlogNotification(models.Model):
    """Notification system for blog events"""
    NOTIFICATION_TYPES = (
        ('NEW_COMMENT', 'New Comment'),
        ('COMMENT_REPLY', 'Comment Reply'),
        ('POST_LIKED', 'Post Liked'),
        ('NEW_FOLLOWER', 'New Follower'),
        ('POST_FEATURED', 'Post Featured'),
        ('POST_TRENDING', 'Post Trending'),
    )
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_notifications',
        verbose_name='Recipient'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_blog_notifications',
        verbose_name='Sender',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='Type'
    )
    title = models.CharField(max_length=255, verbose_name='Title')
    message = models.TextField(verbose_name='Message')
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    is_read = models.BooleanField(default=False, verbose_name='Read')
    is_sent = models.BooleanField(default=False, verbose_name='Sent')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Blog Notification'
        verbose_name_plural = 'Blog Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} for {self.recipient.email}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

class BlogSubscription(models.Model):
    """Blog subscription for email notifications"""
    SUBSCRIPTION_TYPES = (
        ('ALL_POSTS', 'All New Posts'),
        ('CATEGORY', 'Specific Category'),
        ('AUTHOR', 'Specific Author'),
        ('WEEKLY_DIGEST', 'Weekly Digest'),
        ('MONTHLY_DIGEST', 'Monthly Digest'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_subscriptions',
        verbose_name='User'
    )
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TYPES,
        verbose_name='Subscription Type'
    )
    
    # Optional specific target
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subscribers',
        verbose_name='Category'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subscribers',
        verbose_name='Author'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='Active')
    email_frequency = models.CharField(
        max_length=20,
        choices=(
            ('IMMEDIATE', 'Immediate'),
            ('DAILY', 'Daily Digest'),
            ('WEEKLY', 'Weekly Digest'),
        ),
        default='IMMEDIATE',
        verbose_name='Email Frequency'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Blog Subscription'
        verbose_name_plural = 'Blog Subscriptions'
        unique_together = ('user', 'subscription_type', 'category', 'author')
        ordering = ['-created_at']
    
    def __str__(self):
        target = ""
        if self.category:
            target = f" for {self.category.name}"
        elif self.author:
            target = f" for {self.author.get_full_name()}"
        return f"{self.user.email} - {self.get_subscription_type_display()}{target}"

class BlogContentSuggestion(models.Model):
    """AI-powered content suggestions for blog posts"""
    SUGGESTION_TYPES = (
        ('TITLE', 'Title Suggestion'),
        ('META_DESCRIPTION', 'Meta Description'),
        ('TAGS', 'Tag Suggestions'),
        ('RELATED_TOPICS', 'Related Topics'),
        ('SEO_IMPROVEMENT', 'SEO Improvement'),
        ('CONTENT_EXPANSION', 'Content Expansion'),
    )
    
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='suggestions',
        verbose_name='Blog Post'
    )
    suggestion_type = models.CharField(
        max_length=20,
        choices=SUGGESTION_TYPES,
        verbose_name='Suggestion Type'
    )
    current_value = models.TextField(blank=True, verbose_name='Current Value')
    suggested_value = models.TextField(verbose_name='Suggested Value')
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Confidence Score'
    )
    reason = models.TextField(blank=True, verbose_name='Suggestion Reason')
    
    is_applied = models.BooleanField(default=False, verbose_name='Applied')
    is_dismissed = models.BooleanField(default=False, verbose_name='Dismissed')
    applied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applied_suggestions',
        verbose_name='Applied By'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Content Suggestion'
        verbose_name_plural = 'Content Suggestions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'suggestion_type']),
            models.Index(fields=['is_applied']),
            models.Index(fields=['confidence_score']),
        ]
    
    def __str__(self):
        return f"{self.get_suggestion_type_display()} for {self.post.title}"
    
    def apply_suggestion(self, user):
        """Apply the suggestion to the post"""
        if self.suggestion_type == 'TITLE':
            self.post.title = self.suggested_value
        elif self.suggestion_type == 'META_DESCRIPTION':
            self.post.meta_description = self.suggested_value
        # Add more suggestion type handlers as needed
        
        self.post.save()
        self.is_applied = True
        self.applied_by = user
        self.applied_at = timezone.now()
        self.save(update_fields=['is_applied', 'applied_by', 'applied_at'])

class BlogABTest(models.Model):
    """A/B testing for blog content"""
    name = models.CharField(max_length=255, verbose_name='Test Name')
    description = models.TextField(blank=True, verbose_name='Description')
    
    # Test configuration
    test_type = models.CharField(
        max_length=20,
        choices=(
            ('TITLE', 'Title Test'),
            ('FEATURED_IMAGE', 'Featured Image Test'),
            ('CTA', 'Call to Action Test'),
            ('LAYOUT', 'Layout Test'),
        ),
        verbose_name='Test Type'
    )
    
    # Posts being tested
    control_post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='control_tests',
        verbose_name='Control Post'
    )
    variant_post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='variant_tests',
        verbose_name='Variant Post'
    )
    
    # Test settings
    traffic_split = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.00,
        verbose_name='Traffic Split % (for variant)'
    )
    start_date = models.DateTimeField(verbose_name='Start Date')
    end_date = models.DateTimeField(null=True, blank=True, verbose_name='End Date')
    
    # Results
    control_views = models.PositiveIntegerField(default=0)
    variant_views = models.PositiveIntegerField(default=0)
    control_conversions = models.PositiveIntegerField(default=0)
    variant_conversions = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True, verbose_name='Active')
    winner = models.CharField(
        max_length=20,
        choices=(
            ('CONTROL', 'Control'),
            ('VARIANT', 'Variant'),
            ('NO_WINNER', 'No Significant Difference'),
        ),
        null=True,
        blank=True,
        verbose_name='Winner'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'A/B Test'
        verbose_name_plural = 'A/B Tests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"A/B Test: {self.name}"
    
    def calculate_conversion_rate(self, variant='control'):
        """Calculate conversion rate for control or variant"""
        if variant == 'control':
            if self.control_views > 0:
                return (self.control_conversions / self.control_views) * 100
        else:
            if self.variant_views > 0:
                return (self.variant_conversions / self.variant_views) * 100
        return 0
    
    def determine_winner(self):
        """Determine the winner based on statistical significance"""
        control_rate = self.calculate_conversion_rate('control')
        variant_rate = self.calculate_conversion_rate('variant')
        
        # Simple implementation - in production, use proper statistical tests
        if variant_rate > control_rate * 1.1:  # 10% improvement threshold
            self.winner = 'VARIANT'
        elif control_rate > variant_rate * 1.1:
            self.winner = 'CONTROL'
        else:
            self.winner = 'NO_WINNER'
        
        self.save(update_fields=['winner'])
