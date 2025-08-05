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
    list_display = ('astro_book_id', 'service', 'contact_email', 'preferred_date', 'status', 'session_status', 'payment_status')
    list_filter = ('status', 'is_session_scheduled', 'service', 'preferred_date', 'created_at')
    search_fields = ('astro_book_id', 'contact_email', 'contact_phone', 'birth_place', 'payment_id')
    readonly_fields = ('astro_book_id', 'payment_id', 'created_at', 'updated_at', 'booking_summary')
    
    actions = ['send_session_links', 'mark_sessions_completed']
    
    def send_session_links(self, request, queryset):
        """Admin action to send session links to selected bookings"""
        count = 0
        for booking in queryset:
            if booking.google_meet_link:
                booking.send_session_link_notification()
                count += 1
        
        if count:
            self.message_user(request, f'Session links sent to {count} customers.')
        else:
            self.message_user(request, 'No bookings with Google Meet links found.', level='warning')
    send_session_links.short_description = "Send Google Meet links to customers"
    
    def mark_sessions_completed(self, request, queryset):
        """Admin action to mark sessions as completed"""
        count = queryset.update(status='COMPLETED')
        self.message_user(request, f'{count} sessions marked as completed.')
    mark_sessions_completed.short_description = "Mark sessions as completed"
    
    def session_status(self, obj):
        """Show session scheduling status"""
        if obj.is_session_scheduled and obj.google_meet_link:
            return mark_safe('<span style="color: green; font-weight: bold;">✅ Scheduled</span>')
        elif obj.google_meet_link:
            return mark_safe('<span style="color: orange; font-weight: bold;">📅 Link Added</span>')
        else:
            return mark_safe('<span style="color: red; font-weight: bold;">❌ Not Scheduled</span>')
    session_status.short_description = "Session Status"
    
    actions = ['send_session_link', 'mark_as_completed']
    
    def session_status(self, obj):
        """Display session scheduling status"""
        if obj.google_meet_link:
            return mark_safe('<span style="color: green;">✅ Link Sent</span>')
        elif obj.is_session_scheduled:
            return mark_safe('<span style="color: orange;">⏳ Scheduled</span>')
        else:
            return mark_safe('<span style="color: red;">❌ Not Scheduled</span>')
    session_status.short_description = "Session Status"
    
    def payment_status(self, obj):
        """Display payment status"""
        if obj.payment_id:
            return mark_safe('<span style="color: green;">✅ Paid</span>')
        else:
            return mark_safe('<span style="color: red;">❌ Not Paid</span>')
    payment_status.short_description = "Payment Status"
    
    def booking_summary(self, obj):
        """Display a summary of the booking"""
        summary = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.5;">
            <h3>Booking Summary</h3>
            <p><strong>Service:</strong> {obj.service.title}</p>
            <p><strong>Customer:</strong> {obj.contact_email} ({obj.contact_phone})</p>
            <p><strong>Date & Time:</strong> {obj.preferred_date} at {obj.preferred_time}</p>
            <p><strong>Duration:</strong> {obj.service.duration_minutes} minutes</p>
            <p><strong>Language:</strong> {obj.language}</p>
            <p><strong>Birth Details:</strong> {obj.birth_place}, {obj.birth_date} at {obj.birth_time}</p>
            <p><strong>Gender:</strong> {obj.get_gender_display()}</p>
        """
        
        if obj.questions:
            summary += f'<p><strong>Questions:</strong> {obj.questions}</p>'
            
        if obj.google_meet_link:
            summary += f'<p><strong>Google Meet:</strong> <a href="{obj.google_meet_link}" target="_blank">Join Session</a></p>'
            
        summary += '</div>'
        return mark_safe(summary)
    booking_summary.short_description = "Booking Summary"
    
    def send_session_link(self, request, queryset):
        """Admin action to send session link to customers"""
        sent_count = 0
        for booking in queryset:
            if booking.google_meet_link:
                try:
                    booking.send_session_link_notification()
                    sent_count += 1
                except Exception as e:
                    self.message_user(request, f"Failed to send link for {booking.astro_book_id}: {str(e)}", level='ERROR')
            else:
                self.message_user(request, f"No Google Meet link set for {booking.astro_book_id}", level='WARNING')
        
        if sent_count > 0:
            self.message_user(request, f"Successfully sent session links to {sent_count} customers")
    
    send_session_link.short_description = "Send Google Meet link to selected customers"
    
    def mark_as_completed(self, request, queryset):
        """Admin action to mark sessions as completed"""
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f"Marked {updated} sessions as completed")
    
    mark_as_completed.short_description = "Mark selected sessions as completed"
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('astro_book_id', 'service', 'status', 'payment_id')
        }),
        ('Customer Details', {
            'fields': ('user', 'contact_email', 'contact_phone', 'language')
        }),
        ('Session Scheduling', {
            'fields': ('preferred_date', 'preferred_time'),
            'classes': ('wide',)
        }),
        ('Google Meet Session', {
            'fields': ('google_meet_link', 'session_notes', 'is_session_scheduled'),
            'classes': ('wide',),
            'description': 'Add the Google Meet link here. Customer will automatically receive an email with the link.'
        }),
        ('Birth Details', {
            'fields': ('birth_place', 'birth_date', 'birth_time', 'gender'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('questions', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('booking_summary',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )