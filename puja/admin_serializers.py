"""
Admin-specific serializers for Puja system
Enhanced serializers with detailed information for admin operations
"""
from rest_framework import serializers
from .models import PujaCategory, PujaService, Package, PujaBooking
from accounts.serializers import UserSerializer


class AdminPujaCategorySerializer(serializers.ModelSerializer):
    """Enhanced category serializer for admin operations"""
    service_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PujaCategory
        fields = ['id', 'name', 'created_at', 'updated_at', 'service_count']
        read_only_fields = ['created_at', 'updated_at']


class AdminPujaServiceSerializer(serializers.ModelSerializer):
    """Enhanced service serializer for admin operations"""
    category = AdminPujaCategorySerializer(read_only=True)
    booking_count = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    package_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PujaService
        fields = [
            'id', 'title', 'image', 'description', 'category', 'type',
            'duration_minutes', 'is_active', 'created_at', 'updated_at',
            'booking_count', 'total_revenue', 'package_count'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AdminPackageSerializer(serializers.ModelSerializer):
    """Enhanced package serializer for admin operations"""
    puja_service = AdminPujaServiceSerializer(read_only=True)
    booking_count = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Package
        fields = [
            'id', 'puja_service', 'location', 'language', 'package_type',
            'price', 'description', 'includes_materials', 'priest_count',
            'is_active', 'created_at', 'updated_at', 'booking_count', 'total_revenue'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AdminPujaBookingSerializer(serializers.ModelSerializer):
    """Enhanced booking serializer for admin operations"""
    puja_service = AdminPujaServiceSerializer(read_only=True)
    package = AdminPackageSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    customer_name = serializers.SerializerMethodField()
    booking_value = serializers.SerializerMethodField()
    days_until_puja = serializers.SerializerMethodField()
    priest_assignment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = PujaBooking
        fields = [
            'id', 'user', 'puja_service', 'package', 'booking_date',
            'start_time', 'end_time', 'status', 'contact_name',
            'contact_number', 'contact_email', 'address',
            'special_instructions', 'cancellation_reason',
            'created_at', 'updated_at', 'customer_name',
            'booking_value', 'days_until_puja', 'priest_assignment_status'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_customer_name(self, obj):
        """Get customer display name"""
        if obj.contact_name:
            return obj.contact_name
        elif obj.user:
            return obj.user.username or obj.user.email
        return obj.contact_email
    
    def get_booking_value(self, obj):
        """Get booking monetary value"""
        if obj.package:
            return str(obj.package.price)
        return "0.00"
    
    def get_days_until_puja(self, obj):
        """Calculate days until puja"""
        from datetime import date
        today = date.today()
        if obj.booking_date >= today:
            return (obj.booking_date - today).days
        else:
            return -(today - obj.booking_date).days  # Negative for past dates
    
    def get_priest_assignment_status(self, obj):
        """Get priest assignment status"""
        if obj.package and obj.package.priest_count > 0:
            return f"{obj.package.priest_count} priest(s) required"
        return "No priests required"


class AdminPujaBookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating puja bookings in admin panel"""
    
    class Meta:
        model = PujaBooking
        fields = [
            'status', 'booking_date', 'start_time', 'end_time',
            'contact_name', 'contact_number', 'contact_email',
            'address', 'special_instructions', 'cancellation_reason'
        ]
    
    def validate(self, data):
        """Validate admin booking updates"""
        from datetime import date, time
        
        # Validate booking_date if provided
        if 'booking_date' in data and data['booking_date'] < date.today():
            raise serializers.ValidationError({
                'booking_date': 'Cannot schedule puja in the past'
            })
        
        # Validate time format
        if 'start_time' in data and not isinstance(data['start_time'], time):
            raise serializers.ValidationError({
                'start_time': 'Invalid time format'
            })
        
        if 'end_time' in data and not isinstance(data['end_time'], time):
            raise serializers.ValidationError({
                'end_time': 'Invalid time format'
            })
        
        # Validate end_time is after start_time
        if ('start_time' in data and 'end_time' in data and 
            data['end_time'] <= data['start_time']):
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time'
            })
        
        return data


class AdminPujaBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on puja bookings"""
    booking_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of puja booking IDs"
    )
    action = serializers.ChoiceField(
        choices=[
            ('update_status', 'Update Status'),
            ('send_reminders', 'Send Reminders'),
            ('mark_completed', 'Mark Completed'),
            ('assign_priests', 'Assign Priests'),
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
        
        if action == 'assign_priests' and 'priest_ids' not in params:
            raise serializers.ValidationError({
                'params': 'priest_ids parameter is required for assign_priests action'
            })
        
        # Validate booking IDs exist
        booking_ids = data['booking_ids']
        existing_count = PujaBooking.objects.filter(id__in=booking_ids).count()
        if existing_count != len(booking_ids):
            raise serializers.ValidationError({
                'booking_ids': 'Some booking IDs do not exist'
            })
        
        return data


class AdminPujaDashboardSerializer(serializers.Serializer):
    """Serializer for puja dashboard data"""
    overview = serializers.DictField()
    recent_bookings = AdminPujaBookingSerializer(many=True)
    service_performance = serializers.ListField()
    package_analytics = serializers.ListField()


class AdminPujaNotificationSerializer(serializers.Serializer):
    """Serializer for sending manual puja notifications"""
    booking_id = serializers.IntegerField(
        help_text="Puja booking ID"
    )
    message_type = serializers.ChoiceField(
        choices=[
            ('reminder', 'Puja Reminder'),
            ('update', 'Puja Update'),
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
        if not PujaBooking.objects.filter(id=value).exists():
            raise serializers.ValidationError("Puja booking not found")
        return value


class AdminPujaReportSerializer(serializers.Serializer):
    """Serializer for puja report parameters"""
    report_type = serializers.ChoiceField(
        choices=[
            ('summary', 'Summary Report'),
            ('revenue', 'Revenue Report'),
            ('bookings', 'Booking Report'),
            ('services', 'Service Performance Report'),
            ('packages', 'Package Performance Report')
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


class AdminPujaServiceAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for puja service analytics"""
    total_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_booking_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    booking_trend = serializers.ListField(required=False)
    popular_packages = serializers.ListField(required=False)
    
    class Meta:
        model = PujaService
        fields = [
            'id', 'title', 'type', 'duration_minutes', 'is_active',
            'total_bookings', 'total_revenue', 'average_booking_value',
            'booking_trend', 'popular_packages'
        ]


class AdminPujaCustomerAnalyticsSerializer(serializers.Serializer):
    """Serializer for puja customer analytics"""
    total_customers = serializers.IntegerField()
    repeat_customers = serializers.IntegerField()
    new_customers_this_month = serializers.IntegerField()
    top_customers = serializers.ListField()
    location_wise_distribution = serializers.DictField()


class AdminPujaPackageAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for package performance analytics"""
    booking_count = serializers.IntegerField()
    revenue_generated = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, required=False)
    
    class Meta:
        model = Package
        fields = [
            'id', 'location', 'language', 'package_type', 'price',
            'includes_materials', 'priest_count', 'is_active',
            'booking_count', 'revenue_generated', 'average_rating'
        ]
