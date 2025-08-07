"""
Admin-specific serializers for Astrology system
Enhanced serializers with detailed information for admin operations
"""
from rest_framework import serializers
from .models import AstrologyService, AstrologyBooking
from accounts.serializers import UserSerializer


class AdminAstrologyServiceSerializer(serializers.ModelSerializer):
    """Enhanced service serializer for admin operations"""
    booking_count = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    image = serializers.ImageField(write_only=True, required=False)
    
    class Meta:
        model = AstrologyService
        fields = [
            'id', 'title', 'service_type', 'description', 'image', 'image_url',
            'image_thumbnail_url', 'image_card_url', 'price', 'duration_minutes',
            'is_active', 'created_at', 'updated_at', 'booking_count', 'total_revenue'
        ]
        read_only_fields = ['created_at', 'updated_at', 'image_url', 'image_thumbnail_url', 'image_card_url']


class AdminAstrologyBookingSerializer(serializers.ModelSerializer):
    """Enhanced booking serializer for admin operations"""
    service = AdminAstrologyServiceSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    customer_name = serializers.SerializerMethodField()
    session_status = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    days_until_session = serializers.SerializerMethodField()
    
    class Meta:
        model = AstrologyBooking
        fields = [
            'id', 'astro_book_id', 'payment_id', 'user', 'service', 'language',
            'preferred_date', 'preferred_time', 'birth_place', 'birth_date',
            'birth_time', 'gender', 'questions', 'status', 'contact_email',
            'contact_phone', 'google_meet_link', 'session_notes',
            'is_session_scheduled', 'metadata', 'created_at', 'updated_at',
            'customer_name', 'session_status', 'payment_status', 'days_until_session'
        ]
        read_only_fields = ['astro_book_id', 'payment_id', 'created_at', 'updated_at']
    
    def get_customer_name(self, obj):
        """Get customer display name"""
        if obj.user:
            # Use username if available, otherwise fall back to email
            return obj.user.username or obj.user.email
        return obj.contact_email
    
    def get_session_status(self, obj):
        """Get session scheduling status"""
        if obj.google_meet_link:
            if obj.is_session_scheduled:
                return "Scheduled & Link Sent"
            else:
                return "Link Added (Not Sent)"
        elif obj.is_session_scheduled:
            return "Marked Scheduled (No Link)"
        else:
            return "Not Scheduled"
    
    def get_payment_status(self, obj):
        """Get payment status information"""
        if obj.payment_id:
            return "Paid"
        else:
            return "Unpaid/Unknown"
    
    def get_days_until_session(self, obj):
        """Calculate days until session"""
        from datetime import date
        today = date.today()
        if obj.preferred_date >= today:
            return (obj.preferred_date - today).days
        else:
            return -(today - obj.preferred_date).days  # Negative for past dates


class AdminBookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating bookings in admin panel"""
    
    class Meta:
        model = AstrologyBooking
        ref_name = 'AstrologyAdminBookingUpdate'
        fields = [
            'status', 'preferred_date', 'preferred_time', 'language',
            'google_meet_link', 'session_notes', 'is_session_scheduled',
            'birth_place', 'birth_date', 'birth_time', 'gender',
            'questions', 'contact_email', 'contact_phone'
        ]
    
    def validate(self, data):
        """Validate admin booking updates"""
        from datetime import date, time
        
        # Validate preferred_date if provided
        if 'preferred_date' in data and data['preferred_date'] < date.today():
            raise serializers.ValidationError({
                'preferred_date': 'Cannot schedule session in the past'
            })
        
        # Validate time format
        if 'preferred_time' in data and not isinstance(data['preferred_time'], time):
            raise serializers.ValidationError({
                'preferred_time': 'Invalid time format'
            })
        
        # Validate birth_date if provided
        if 'birth_date' in data and data['birth_date'] > date.today():
            raise serializers.ValidationError({
                'birth_date': 'Birth date cannot be in the future'
            })
        
        # If Google Meet link is provided, mark as scheduled
        if 'google_meet_link' in data and data['google_meet_link']:
            data['is_session_scheduled'] = True
        
        return data


class AdminSessionScheduleSerializer(serializers.Serializer):
    """Serializer for scheduling sessions"""
    booking_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of astro_book_id values"
    )
    google_meet_link = serializers.URLField(
        help_text="Google Meet link for the session"
    )
    session_notes = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Additional notes about the session"
    )
    send_notification = serializers.BooleanField(
        default=True,
        help_text="Whether to send notification to customers"
    )
    
    def validate_booking_ids(self, value):
        """Validate that all booking IDs exist"""
        existing_bookings = AstrologyBooking.objects.filter(
            astro_book_id__in=value
        ).values_list('astro_book_id', flat=True)
        
        invalid_ids = set(value) - set(existing_bookings)
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid booking IDs: {', '.join(invalid_ids)}"
            )
        
        return value


class AdminBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on bookings"""
    booking_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of booking IDs"
    )
    action = serializers.ChoiceField(
        choices=[
            ('update_status', 'Update Status'),
            ('schedule_sessions', 'Schedule Sessions'),
            ('send_reminders', 'Send Reminders'),
            ('mark_completed', 'Mark Completed'),
            ('send_follow_up', 'Send Follow-up')
        ],
        help_text="Action to perform on selected bookings"
    )
    params = serializers.DictField(
        required=False,
        help_text="Additional parameters for the action"
    )
    
    def validate(self, data):
        """Validate bulk action parameters"""
        action = data['action']
        params = data.get('params', {})
        
        # Validate parameters based on action
        if action == 'update_status' and 'status' not in params:
            raise serializers.ValidationError({
                'params': 'Status parameter is required for update_status action'
            })
        
        if action == 'schedule_sessions' and 'google_meet_link' not in params:
            raise serializers.ValidationError({
                'params': 'google_meet_link parameter is required for schedule_sessions action'
            })
        
        # Validate booking IDs exist
        booking_ids = data['booking_ids']
        existing_count = AstrologyBooking.objects.filter(id__in=booking_ids).count()
        if existing_count != len(booking_ids):
            raise serializers.ValidationError({
                'booking_ids': 'Some booking IDs do not exist'
            })
        
        return data


class AdminDashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    overview = serializers.DictField()
    recent_bookings = AdminAstrologyBookingSerializer(many=True)
    pending_sessions = AdminAstrologyBookingSerializer(many=True)
    upcoming_sessions = AdminAstrologyBookingSerializer(many=True)
    service_performance = serializers.ListField()


class AdminNotificationSerializer(serializers.Serializer):
    """Serializer for sending manual notifications"""
    booking_id = serializers.CharField(
        help_text="Booking ID (astro_book_id)"
    )
    message_type = serializers.ChoiceField(
        choices=[
            ('reminder', 'Session Reminder'),
            ('update', 'Booking Update'),
            ('custom', 'Custom Message'),
            ('follow_up', 'Follow-up Message')
        ],
        help_text="Type of notification to send"
    )
    custom_message = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Custom message content"
    )
    include_booking_details = serializers.BooleanField(
        default=True,
        help_text="Whether to include booking details in the notification"
    )
    
    def validate_booking_id(self, value):
        """Validate booking ID exists"""
        if not AstrologyBooking.objects.filter(astro_book_id=value).exists():
            raise serializers.ValidationError("Booking not found")
        return value


class AdminReportSerializer(serializers.Serializer):
    """Serializer for report parameters"""
    report_type = serializers.ChoiceField(
        choices=[
            ('summary', 'Summary Report'),
            ('revenue', 'Revenue Report'),
            ('bookings', 'Booking Report'),
            ('services', 'Service Performance Report')
        ],
        default='summary'
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        return data


class AdminServiceAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for service analytics"""
    total_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, required=False)
    booking_trend = serializers.ListField(required=False)
    
    class Meta:
        model = AstrologyService
        fields = [
            'id', 'title', 'service_type', 'price', 'duration_minutes',
            'is_active', 'total_bookings', 'total_revenue', 'average_rating',
            'booking_trend'
        ]


class AdminCustomerAnalyticsSerializer(serializers.Serializer):
    """Serializer for customer analytics"""
    total_customers = serializers.IntegerField()
    repeat_customers = serializers.IntegerField()
    new_customers_this_month = serializers.IntegerField()
    top_customers = serializers.ListField()
    customer_demographics = serializers.DictField()


class AdminBookingTrendSerializer(serializers.Serializer):
    """Serializer for booking trends"""
    daily_bookings = serializers.ListField()
    monthly_bookings = serializers.ListField()
    service_wise_trends = serializers.DictField()
    peak_hours = serializers.ListField()
    seasonal_trends = serializers.DictField()
