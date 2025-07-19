from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import AstrologyService, AstrologyBooking

@admin.register(AstrologyService)
class AstrologyServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'service_type', 'price', 'is_active', 'image_preview')
    list_filter = ('service_type', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = ('image_preview', 'created_at', 'updated_at')

    def image_preview(self, obj):
        """Display image preview in admin"""
        # Use thumbnail if available, fallback to main image
        image_url = obj.image_thumbnail_url or obj.image_url
        if image_url:
            try:
                return mark_safe(
                    f'<img src="{image_url}" width="50" height="50" '
                    f'style="object-fit: cover; border-radius: 4px;" '
                    f'onerror="this.style.display=\'none\'; this.nextSibling.style.display=\'inline\';" />'
                    f'<span style="display:none; color: #666;">Invalid Image URL</span>'
                )
            except Exception:
                return "Invalid Image URL"
        return "No Image"
    image_preview.short_description = "Image Preview"

    fieldsets = (
        (None, {
            'fields': ('title', 'service_type', 'price', 'duration_minutes', 'is_active')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Images', {
            'fields': ('image_url', 'image_thumbnail_url', 'image_card_url', 'image_preview')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AstrologyBooking)
class AstrologyBookingAdmin(admin.ModelAdmin):
    list_display = ('service', 'contact_email', 'preferred_date', 'status')
    list_filter = ('status', 'service', 'preferred_date')
    search_fields = ('contact_email', 'contact_phone', 'birth_place')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Booking Info', {
            'fields': ('user', 'service', 'status')
        }),
        ('Schedule', {
            'fields': ('preferred_date', 'preferred_time')
        }),
        ('Birth Details', {
            'fields': ('birth_place', 'birth_date', 'birth_time', 'gender')
        }),
        ('Contact Info', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Additional Info', {
            'fields': ('questions',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )