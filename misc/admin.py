from django.contrib import admin
from .models import Event, JobOpening, ContactUs
from imagekit.admin import AdminThumbnail

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'admin_thumbnail', 
        'title', 
        'event_date', 
        'location',
        'status', 
        'is_featured',
        'created_at'
    )
    list_filter = ('status', 'is_featured', 'event_date')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = (
        'created_at', 
        'updated_at',
        'thumbnail_preview',
        'banner_preview'
    )
    list_editable = ('status', 'is_featured')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description')
        }),
        ('Image', {
            'fields': (
                'original_image', 
                'thumbnail_preview',
                'banner_preview'
            )
        }),
        ('Details', {
            'fields': (
                'event_date', 'start_time', 'end_time', 
                'location', 'registration_link'
            )
        }),
        ('Settings', {
            'fields': ('status', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    admin_thumbnail = AdminThumbnail(image_field='thumbnail')
    admin_thumbnail.short_description = 'Thumbnail'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return "-"
    thumbnail_preview.short_description = "Thumbnail URL"
    
    def banner_preview(self, obj):
        if obj.banner:
            return obj.banner.url
        return "-"
    banner_preview.short_description = "Banner URL"

@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'job_type',
        'location',
        'application_deadline',
        'is_active',
        'created_at'
    )
    list_filter = ('job_type', 'is_active', 'application_deadline')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description')
        }),
        ('Details', {
            'fields': (
                'responsibilities', 'requirements',
                'job_type', 'location', 'salary_range'
            )
        }),
        ('Application', {
            'fields': ('application_deadline', 'application_link')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Don't allow changing application deadline after creation
        if obj:
            return self.readonly_fields + ('application_deadline',)
        return self.readonly_fields

@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'email', 
        'subject', 
        'status',
        'created_at',
        'replied_at'
    )
    list_filter = ('status', 'subject', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = (
        'name', 'email', 'phone', 
        'subject', 'message', 'ip_address',
        'user_agent', 'created_at', 'updated_at',
        'replied_at'
    )
    actions = ['mark_as_replied', 'mark_as_closed']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'phone', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'replied_at')
        }),
    )
    
    def mark_as_replied(self, request, queryset):
        for contact in queryset:
            contact.mark_as_replied()
        self.message_user(request, "Selected contacts marked as replied")
    mark_as_replied.short_description = "Mark as replied"
    
    def mark_as_closed(self, request, queryset):
        for contact in queryset:
            contact.mark_as_closed()
        self.message_user(request, "Selected contacts marked as closed")
    mark_as_closed.short_description = "Mark as closed"
    
    def has_add_permission(self, request):
        return False