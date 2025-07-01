from django.contrib import admin
from .models import AstrologyService, AstrologyBooking
from imagekit.admin import AdminThumbnail

@admin.register(AstrologyService)
class AstrologyServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'service_type', 'price', 'is_active', 'image_preview')
    list_filter = ('service_type', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    image_preview = AdminThumbnail(image_field='image_thumbnail')

    fieldsets = (
        (None, {
            'fields': ('title', 'service_type', 'price', 'duration_minutes', 'is_active')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Images', {
            'fields': ('image', 'image_preview')
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