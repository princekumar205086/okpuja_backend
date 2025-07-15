from django.contrib import admin
from django.utils.html import format_html
from .models import Booking, BookingAttachment

class BookingAttachmentInline(admin.TabularInline):
    model = BookingAttachment
    extra = 0
    readonly_fields = ['uploaded_at']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'book_id', 'user', 'get_service_name', 'assigned_to', 'status', 
        'selected_date', 'total_amount', 'created_at'
    )
    list_filter = ('status', 'assigned_to', 'selected_date', 'created_at')
    search_fields = ('book_id', 'user__email', 'user__username', 'assigned_to__email')
    readonly_fields = ('book_id', 'created_at', 'updated_at', 'total_amount')
    inlines = [BookingAttachmentInline]
    actions = ['confirm_selected', 'cancel_selected', 'complete_selected']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('book_id', 'user', 'cart', 'status')
        }),
        ('Schedule & Assignment', {
            'fields': ('selected_date', 'selected_time', 'assigned_to', 'address')
        }),
        ('Reasons', {
            'fields': ('cancellation_reason', 'failure_reason', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'total_amount'),
            'classes': ('collapse',)
        })
    )

    def get_service_name(self, obj):
        if obj.cart.service_type == 'PUJA' and obj.cart.puja_service:
            return obj.cart.puja_service.title
        elif obj.cart.service_type == 'ASTROLOGY' and obj.cart.astrology_service:
            return obj.cart.astrology_service.title
        return '-'
    get_service_name.short_description = 'Service'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'cart', 'assigned_to', 'address'
        )

    def confirm_selected(self, request, queryset):
        updated = queryset.update(status='CONFIRMED')
        self.message_user(request, f'{updated} bookings marked as confirmed.')
    confirm_selected.short_description = "Mark selected as confirmed"

    def cancel_selected(self, request, queryset):
        updated = queryset.update(status='CANCELLED', cancellation_reason='Bulk cancellation by admin')
        self.message_user(request, f'{updated} bookings cancelled.')
    cancel_selected.short_description = "Mark selected as cancelled"

    def complete_selected(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} bookings marked as completed.')
    complete_selected.short_description = "Mark selected as completed"

@admin.register(BookingAttachment)
class BookingAttachmentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('booking__book_id', 'caption')
    readonly_fields = ('uploaded_at',)