from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
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
    actions = ['confirm_selected', 'cancel_selected', 'complete_selected', 'safe_delete_selected', 'force_delete_selected']
    
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
        """Get service name with proper null checking"""
        try:
            if obj.cart and hasattr(obj.cart, 'service_type'):
                if obj.cart.service_type == 'PUJA' and obj.cart.puja_service:
                    return obj.cart.puja_service.title
                elif obj.cart.service_type == 'ASTROLOGY' and obj.cart.astrology_service:
                    return obj.cart.astrology_service.title
            return '-'
        except Exception:
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

    def safe_delete_selected(self, request, queryset):
        """Safely delete bookings by handling all FK relationships properly"""
        try:
            with transaction.atomic():
                deleted_count = 0
                deleted_ids = []
                
                for booking in queryset.select_related('cart', 'user', 'address', 'assigned_to'):
                    try:
                        booking_id = booking.book_id
                        
                        # First, delete any attachments to avoid FK constraints
                        BookingAttachment.objects.filter(booking=booking).delete()
                        
                        # Update cart if it exists to prevent any FK issues
                        if booking.cart:
                            try:
                                booking.cart.status = 'ABANDONED'
                                booking.cart.save()
                            except Exception:
                                # If cart update fails, set cart to None
                                booking.cart = None
                                booking.save()
                        
                        # Now delete the booking itself
                        booking.delete()
                        deleted_count += 1
                        deleted_ids.append(booking_id)
                        
                    except Exception as e:
                        # Log the specific booking that failed but continue with others
                        self.message_user(
                            request,
                            f'Failed to delete booking {booking.book_id}: {str(e)}',
                            messages.WARNING
                        )
                
                if deleted_count > 0:
                    self.message_user(
                        request, 
                        f'Successfully deleted {deleted_count} bookings: {", ".join(deleted_ids)}',
                        messages.SUCCESS
                    )
                else:
                    self.message_user(
                        request,
                        'No bookings were deleted due to errors.',
                        messages.ERROR
                    )
                    
        except Exception as e:
            self.message_user(
                request,
                f'Error in bulk deletion process: {str(e)}',
                messages.ERROR
            )
    safe_delete_selected.short_description = "Safely delete selected bookings"

    def force_delete_selected(self, request, queryset):
        """Force delete bookings using raw SQL to bypass FK constraints"""
        try:
            from django.db import connection
            
            booking_ids = list(queryset.values_list('book_id', flat=True))
            db_ids = list(queryset.values_list('id', flat=True))
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # First delete attachments
                    cursor.execute(
                        f"DELETE FROM booking_bookingattachment WHERE booking_id IN ({','.join(['%s'] * len(db_ids))})",
                        db_ids
                    )
                    
                    # Then delete bookings
                    cursor.execute(
                        f"DELETE FROM booking_booking WHERE id IN ({','.join(['%s'] * len(db_ids))})",
                        db_ids
                    )
            
            self.message_user(
                request,
                f'Force deleted {len(booking_ids)} bookings: {", ".join(booking_ids)}',
                messages.SUCCESS
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'Force deletion failed: {str(e)}',
                messages.ERROR
            )
    force_delete_selected.short_description = "Force delete selected bookings (bypasses FK constraints)"

@admin.register(BookingAttachment)
class BookingAttachmentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('booking__book_id', 'caption')
    readonly_fields = ('uploaded_at',)