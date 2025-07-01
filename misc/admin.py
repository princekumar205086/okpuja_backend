from django.contrib import admin
from .models import GalleryCategory, GalleryItem, GalleryView
from imagekit.admin import AdminThumbnail

@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'position', 'item_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('position', 'status')
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'

class GalleryViewInline(admin.TabularInline):
    model = GalleryView
    extra = 0
    readonly_fields = ('user', 'ip_address', 'user_agent', 'created_at')
    can_delete = False

@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = (
        'admin_thumbnail', 
        'title', 
        'category', 
        'status', 
        'is_featured', 
        'popularity',
        'created_at'
    )
    list_filter = ('category', 'status', 'is_featured', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'popularity',
        'thumbnail_preview',
        'medium_preview',
        'large_preview',
        'web_preview'
    )
    list_editable = ('status', 'is_featured')
    inlines = [GalleryViewInline]
    
    fieldsets = (
        (None, {
            'fields': ('category', 'title', 'description')
        }),
        ('Image', {
            'fields': (
                'original_image', 
                'thumbnail_preview',
                'medium_preview',
                'large_preview',
                'web_preview'
            )
        }),
        ('Metadata', {
            'fields': ('taken_at',)
        }),
        ('Settings', {
            'fields': ('status', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('popularity', 'created_at', 'updated_at')
        }),
    )
    
    admin_thumbnail = AdminThumbnail(image_field='thumbnail')
    admin_thumbnail.short_description = 'Thumbnail'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return "-"
    thumbnail_preview.short_description = "Thumbnail URL"
    
    def medium_preview(self, obj):
        if obj.medium:
            return obj.medium.url
        return "-"
    medium_preview.short_description = "Medium URL"
    
    def large_preview(self, obj):
        if obj.large:
            return obj.large.url
        return "-"
    large_preview.short_description = "Large URL"
    
    def web_preview(self, obj):
        if obj.web_optimized:
            return obj.web_optimized.url
        return "-"
    web_preview.short_description = "Web URL"

@admin.register(GalleryView)
class GalleryViewAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('item__title', 'user__email', 'ip_address')
    readonly_fields = ('item', 'user', 'ip_address', 'user_agent', 'created_at')
    
    def has_add_permission(self, request):
        return False