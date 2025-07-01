from django.contrib import admin
from .models import Booking, BookingAttachment

class BookingAttachmentInline(admin.TabularInline):
    model = BookingAttachment
    extra = 0
    readonly_fields = ['uploaded_at']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'book_id', 'user', 'get_service_name', 'status', 
        'selected_date', 'total_amount', 'created_at'
    )
    list_filter = ('status', 'selected_date', 'created_at')
    search_fields = ('book_id', 'user__email', 'user__username')
    readonly_fields = ('book_id', 'created_at', 'updated_at', 'total_amount')
    inlines = [BookingAttachmentInline]
    actions = ['confirm_selected', 'cancel_selected', 'complete_selected']

    def get_service_name(self, obj):
        return obj.cart.service.title if obj.cart.service else '-'
    get_service_name.short_description = 'Service'

    def confirm_selected(self, request, queryset):
        queryset.update(status='CONFIRMED')
    confirm_selected.short_description = "Mark selected as confirmed"

    def cancel_selected(self, request, queryset):
        queryset.update(status='CANCELLED', cancellation_reason='Bulk cancellation')
    cancel_selected.short_description = "Mark selected as cancelled"

    def complete_selected(self, request, queryset):
        queryset.update(status='COMPLETED')
    complete_selected.short_description = "Mark selected as completed"

@admin.register(BookingAttachment)
class BookingAttachmentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('booking__book_id', 'caption')
    readonly_fields = ('uploaded_at',)