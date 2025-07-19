from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import PujaCategory, PujaService, Package, PujaBooking

class PackageInline(admin.TabularInline):
    model = Package
    extra = 1
    fields = ['language', 'package_type', 'price', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PujaCategory)
class PujaCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PujaService)
class PujaServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'type', 'is_active', 'image_preview')
    list_filter = ('category', 'type', 'is_active')
    search_fields = ('title', 'description')
    inlines = [PackageInline]
    readonly_fields = ('image_preview', 'created_at', 'updated_at')

    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            try:
                return mark_safe(
                    f'<img src="{obj.image}" width="50" height="50" '
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
            'fields': ('title', 'category', 'type', 'duration_minutes', 'is_active')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Images', {
            'fields': ('image', 'image_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('puja_service', 'language', 'package_type', 'price', 'is_active')
    list_filter = ('puja_service', 'language', 'package_type', 'is_active')
    search_fields = ('description',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PujaBooking)
class PujaBookingAdmin(admin.ModelAdmin):
    list_display = ('puja_service', 'user', 'booking_date', 'status')
    list_filter = ('status', 'puja_service', 'booking_date')
    search_fields = ('contact_name', 'contact_number', 'address')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Booking Info', {
            'fields': ('puja_service', 'package', 'user', 'status')
        }),
        ('Schedule', {
            'fields': ('booking_date', 'start_time', 'end_time')
        }),
        ('Contact Details', {
            'fields': ('contact_name', 'contact_number', 'contact_email', 'address')
        }),
        ('Additional Info', {
            'fields': ('special_instructions', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )