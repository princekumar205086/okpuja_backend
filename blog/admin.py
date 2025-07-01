from django.contrib import admin
from .models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    extra = 0
    readonly_fields = ('user', 'content', 'created_at')
    can_delete = False

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'user', 'status', 'is_featured', 'view_count', 'published_at')
    list_filter = ('status', 'is_featured', 'category', 'tags', 'published_at')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('view_count', 'created_at', 'updated_at', 'published_at')
    filter_horizontal = ('tags',)
    inlines = [BlogCommentInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'slug', 'category', 'tags')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image', 'youtube_url')
        }),
        ('Metadata', {
            'fields': ('meta_title', 'meta_keywords', 'meta_description')
        }),
        ('Settings', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('Statistics', {
            'fields': ('view_count', 'created_at', 'updated_at')
        }),
    )

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__email', 'post__title', 'content')
    readonly_fields = ('user', 'post', 'content', 'created_at', 'updated_at')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"

@admin.register(BlogLike)
class BlogLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'post__title')
    readonly_fields = ('user', 'post', 'created_at')

@admin.register(BlogView)
class BlogViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__title', 'user__email', 'ip_address')
    readonly_fields = ('post', 'user', 'ip_address', 'user_agent', 'created_at')