from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'post_count', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['name', 'description', 'meta_keywords']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'user', 'description', 'status')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_keywords', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def post_count(self, obj):
        count = obj.posts.filter(status='PUBLISHED').count()
        url = reverse('admin:blog_blogpost_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} posts</a>', url, count)
    post_count.short_description = 'Published Posts'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            posts_count=Count('posts', filter=Q(posts__status='PUBLISHED'))
        )
        return queryset

@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'post_count', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['cleanup_unused_tags']
    
    def post_count(self, obj):
        count = obj.posts.filter(status='PUBLISHED').count()
        url = reverse('admin:blog_blogpost_changelist') + f'?tags__id__exact={obj.id}'
        return format_html('<a href="{}">{} posts</a>', url, count)
    post_count.short_description = 'Used in Posts'
    
    def cleanup_unused_tags(self, request, queryset):
        """Remove tags that are not used in any published posts"""
        unused_tags = queryset.annotate(
            post_count=Count('posts', filter=Q(posts__status='PUBLISHED'))
        ).filter(post_count=0)
        
        count = unused_tags.count()
        unused_tags.delete()
        
        self.message_user(request, f'Deleted {count} unused tags.')
    cleanup_unused_tags.short_description = "Remove unused tags"

class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    extra = 0
    readonly_fields = ('user', 'content', 'created_at')
    can_delete = False
    max_num = 5  # Show only recent 5 comments

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'category', 'status', 'is_featured', 
        'view_count', 'like_count', 'comment_count', 'seo_score', 'published_at'
    ]
    list_filter = [
        'status', 'is_featured', 'category', 'tags', 'created_at', 
        'published_at', 'user'
    ]
    search_fields = ['title', 'content', 'meta_keywords', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['status', 'is_featured']
    filter_horizontal = ['tags']
    date_hierarchy = 'published_at'
    actions = [
        'mark_as_featured', 'unmark_as_featured', 'publish_posts', 
        'archive_posts', 'generate_seo_data'
    ]
    inlines = [BlogCommentInline]
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'user', 'category', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image', 'youtube_url'),
            'classes': ('collapse',)
        }),
        ('SEO & Metadata', {
            'fields': ('meta_title', 'meta_keywords', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Publication Settings', {
            'fields': ('status', 'is_featured', 'tags', 'published_at')
        }),
        ('Analytics', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    
    def like_count(self, obj):
        count = obj.likes.count()
        return format_html('<span style="color: #e74c3c;">❤️ {}</span>', count)
    like_count.short_description = 'Likes'
    
    def comment_count(self, obj):
        count = obj.comments.filter(is_approved=True).count()
        url = reverse('admin:blog_blogcomment_changelist') + f'?post__id__exact={obj.id}'
        return format_html('<a href="{}" style="color: #3498db;">💬 {}</a>', url, count)
    comment_count.short_description = 'Comments'
    
    def seo_score(self, obj):
        """Calculate and display SEO score"""
        score = 0
        
        # Meta title (20 points)
        if obj.meta_title:
            score += 20
        
        # Meta description (20 points)
        if obj.meta_description:
            score += 20
        
        # Featured image (15 points)
        if obj.featured_image:
            score += 15
        
        # Content length (15 points)
        if len(obj.content) >= 300:
            score += 15
        
        # Tags (10 points)
        if obj.tags.exists():
            score += 10
        
        # Category (10 points)
        if obj.category:
            score += 10
        
        # Excerpt (10 points)
        if obj.excerpt:
            score += 10
        
        # Color coding
        if score >= 80:
            color = '#27ae60'  # Green
        elif score >= 60:
            color = '#f39c12'  # Orange
        else:
            color = '#e74c3c'  # Red
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/100</span>', 
            color, score
        )
    seo_score.short_description = 'SEO Score'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'category').prefetch_related('tags', 'likes', 'comments')
        return queryset
    
    # Admin actions
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} posts marked as featured.')
    mark_as_featured.short_description = "Mark selected posts as featured"
    
    def unmark_as_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f'{queryset.count()} posts unmarked as featured.')
    unmark_as_featured.short_description = "Unmark selected posts as featured"
    
    def publish_posts(self, request, queryset):
        now = timezone.now()
        updated = queryset.filter(status='DRAFT').update(
            status='PUBLISHED',
            published_at=now
        )
        self.message_user(request, f'{updated} posts published.')
    publish_posts.short_description = "Publish selected draft posts"
    
    def archive_posts(self, request, queryset):
        updated = queryset.update(status='ARCHIVED')
        self.message_user(request, f'{updated} posts archived.')
    archive_posts.short_description = "Archive selected posts"
    
    def generate_seo_data(self, request, queryset):
        """Auto-generate SEO data for posts missing it"""
        updated_count = 0
        for post in queryset:
            if not post.meta_title:
                post.meta_title = f"{post.title} | OkPuja Spiritual Guide"
                updated_count += 1
            
            if not post.meta_description and post.excerpt:
                post.meta_description = post.excerpt[:160]
                updated_count += 1
            
            if not post.meta_keywords and post.tags.exists():
                keywords = ', '.join([tag.name for tag in post.tags.all()[:5]])
                post.meta_keywords = f"{keywords}, hindu spirituality, okpuja"
                updated_count += 1
            
            post.save()
        
        self.message_user(request, f'Generated SEO data for {updated_count} fields.')
    generate_seo_data.short_description = "Generate missing SEO data"

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'user', 'content_preview', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at', 'post__category']
    search_fields = ['content', 'user__email', 'post__title']
    list_editable = ['is_approved']
    actions = ['approve_comments', 'disapprove_comments', 'delete_spam_comments']
    raw_id_fields = ['post', 'user', 'parent']
    
    def post_title(self, obj):
        return obj.post.title[:50] + '...' if len(obj.post.title) > 50 else obj.post.title
    post_title.short_description = 'Post'
    
    def content_preview(self, obj):
        preview = obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
        return format_html('<span title="{}">{}</span>', obj.content, preview)
    content_preview.short_description = 'Comment'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments disapproved.')
    disapprove_comments.short_description = "Disapprove selected comments"
    
    def delete_spam_comments(self, request, queryset):
        """Delete comments that look like spam"""
        spam_comments = queryset.filter(
            is_approved=False,
            created_at__lt=timezone.now() - timedelta(days=30)
        )
        count = spam_comments.count()
        spam_comments.delete()
        self.message_user(request, f'Deleted {count} potential spam comments.')
    delete_spam_comments.short_description = "Delete old unapproved comments"

@admin.register(BlogLike)
class BlogLikeAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'user', 'created_at']
    list_filter = ['created_at', 'post__category']
    search_fields = ['post__title', 'user__email']
    raw_id_fields = ['post', 'user']
    
    def post_title(self, obj):
        return obj.post.title[:50] + '...' if len(obj.post.title) > 50 else obj.post.title
    post_title.short_description = 'Post'

@admin.register(BlogView)
class BlogViewAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'user', 'ip_address', 'user_agent_preview', 'created_at']
    list_filter = ['created_at', 'post__category']
    search_fields = ['post__title', 'user__email', 'ip_address']
    raw_id_fields = ['post', 'user']
    date_hierarchy = 'created_at'
    
    def post_title(self, obj):
        return obj.post.title[:40] + '...' if len(obj.post.title) > 40 else obj.post.title
    post_title.short_description = 'Post'
    
    def user_agent_preview(self, obj):
        if obj.user_agent:
            preview = obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
            return format_html('<span title="{}">{}</span>', obj.user_agent, preview)
        return '-'
    user_agent_preview.short_description = 'User Agent'
    
    def has_add_permission(self, request):
        # Prevent manual addition of views
        return False