"""
Enterprise-level admin serializers for Puja system
Specialized serializers for admin operations with enhanced data
"""
from rest_framework import serializers
from django.db.models import Count, Sum, Avg, Q
from puja.models import PujaService, PujaBooking, Package, PujaCategory


class AdminPujaServiceSerializer(serializers.ModelSerializer):
    """Enhanced puja service serializer for admin operations"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    booking_count = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    package_count = serializers.SerializerMethodField()
    active_packages = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = PujaService
        fields = [
            'id', 'title', 'description', 'image', 'category', 'category_name',
            'type', 'type_display', 'is_active', 'created_at', 'updated_at',
            'booking_count', 'total_revenue', 'package_count', 'active_packages',
            'duration', 'what_includes', 'benefits', 'procedure'
        ]
    
    def get_booking_count(self, obj):
        """Get total booking count for this service"""
        return obj.bookings.count()
    
    def get_total_revenue(self, obj):
        """Get total revenue from this service"""
        revenue = obj.packages.filter(
            bookings__status__in=['CONFIRMED', 'COMPLETED']
        ).aggregate(
            total=Sum('bookings__package__price')
        )['total']
        return float(revenue or 0)
    
    def get_package_count(self, obj):
        """Get total package count for this service"""
        return obj.packages.count()
    
    def get_active_packages(self, obj):
        """Get active packages for this service"""
        return obj.packages.filter(is_active=True).count()


class AdminPujaBookingSerializer(serializers.ModelSerializer):
    """Enhanced puja booking serializer for admin operations"""
    service_title = serializers.CharField(source='puja_service.title', read_only=True)
    service_type = serializers.CharField(source='puja_service.get_type_display', read_only=True)
    category_name = serializers.CharField(source='puja_service.category.name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    package_price = serializers.DecimalField(source='package.price', max_digits=10, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    booking_age = serializers.SerializerMethodField()
    time_until_service = serializers.SerializerMethodField()
    
    class Meta:
        model = PujaBooking
        fields = [
            'id', 'puja_service', 'service_title', 'service_type', 'category_name',
            'package', 'package_name', 'package_price', 'user', 'user_email',
            'contact_name', 'contact_email', 'contact_number', 'address',
            'booking_date', 'start_time', 'end_time', 'status', 'status_display',
            'special_requests', 'cancellation_reason', 'created_at', 'updated_at',
            'booking_age', 'time_until_service'
        ]
    
    def get_booking_age(self, obj):
        """Calculate how long ago booking was created"""
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hours ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    def get_time_until_service(self, obj):
        """Calculate time until service"""
        from django.utils import timezone
        from datetime import datetime
        
        if not obj.booking_date:
            return None
            
        service_datetime = datetime.combine(obj.booking_date, obj.start_time or datetime.min.time())
        service_datetime = timezone.make_aware(service_datetime)
        
        delta = service_datetime - timezone.now()
        
        if delta.days < 0:
            return "Past"
        elif delta.days > 0:
            return f"In {delta.days} days"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"In {hours} hours"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"In {minutes} minutes"
        else:
            return "Starting soon"


class AdminPujaBookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating puja bookings by admin"""
    
    class Meta:
        model = PujaBooking
        fields = [
            'status', 'booking_date', 'start_time', 'end_time',
            'special_requests', 'cancellation_reason', 'address'
        ]
    
    def validate(self, attrs):
        """Validate booking update data"""
        if attrs.get('status') == 'CANCELLED' and not attrs.get('cancellation_reason'):
            raise serializers.ValidationError({
                'cancellation_reason': 'Cancellation reason is required when cancelling booking'
            })
        
        # Validate date/time combinations
        booking_date = attrs.get('booking_date')
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time'
            })
        
        # Check for date in past for new bookings
        if booking_date:
            from django.utils import timezone
            if booking_date < timezone.now().date() and attrs.get('status') != 'COMPLETED':
                raise serializers.ValidationError({
                    'booking_date': 'Booking date cannot be in the past unless marking as completed'
                })
        
        return attrs


class AdminPujaBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on puja bookings"""
    booking_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of booking IDs to perform action on"
    )
    action = serializers.ChoiceField(
        choices=[
            ('confirm_bookings', 'Confirm Bookings'),
            ('cancel_bookings', 'Cancel Bookings'),
            ('complete_bookings', 'Complete Bookings'),
            ('send_reminders', 'Send Reminders'),
            ('update_status', 'Update Status')
        ],
        help_text="Action to perform on selected bookings"
    )
    params = serializers.DictField(
        required=False,
        help_text="Additional parameters for the action"
    )
    
    def validate_params(self, value):
        """Validate action parameters"""
        action = self.initial_data.get('action')
        
        if action == 'cancel_bookings' and not value.get('reason'):
            raise serializers.ValidationError("Cancellation reason is required")
        
        if action == 'update_status' and not value.get('status'):
            raise serializers.ValidationError("New status is required")
        
        return value


class AdminPujaDashboardSerializer(serializers.Serializer):
    """Serializer for puja dashboard data"""
    total_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    completed_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_booking_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    active_services = serializers.IntegerField()
    total_packages = serializers.IntegerField()


class AdminPujaReportSerializer(serializers.Serializer):
    """Serializer for puja reports"""
    report_type = serializers.ChoiceField(
        choices=[
            ('revenue', 'Revenue Report'),
            ('bookings', 'Bookings Report'),
            ('services', 'Services Report'),
            ('categories', 'Categories Report'),
            ('summary', 'Summary Report')
        ]
    )
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    def validate(self, attrs):
        """Validate report parameters"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return attrs


class AdminPujaPackageSerializer(serializers.ModelSerializer):
    """Enhanced package serializer for admin operations"""
    service_title = serializers.CharField(source='puja_service.title', read_only=True)
    booking_count = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    
    class Meta:
        model = Package
        fields = [
            'id', 'name', 'price', 'description', 'puja_service', 'service_title',
            'is_active', 'created_at', 'updated_at', 'booking_count', 'total_revenue'
        ]
    
    def get_booking_count(self, obj):
        """Get total bookings for this package"""
        return obj.bookings.count()
    
    def get_total_revenue(self, obj):
        """Get total revenue from this package"""
        revenue = obj.bookings.filter(
            status__in=['CONFIRMED', 'COMPLETED']
        ).aggregate(
            total=Sum('package__price')
        )['total']
        return float(revenue or 0)


class AdminPujaCategorySerializer(serializers.ModelSerializer):
    """Enhanced category serializer for admin operations"""
    service_count = serializers.SerializerMethodField()
    total_bookings = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    
    class Meta:
        model = PujaCategory
        fields = [
            'id', 'name', 'description', 'image', 'is_active',
            'created_at', 'updated_at', 'service_count', 'total_bookings', 'total_revenue'
        ]
    
    def get_service_count(self, obj):
        """Get total services in this category"""
        return obj.services.filter(is_active=True).count()
    
    def get_total_bookings(self, obj):
        """Get total bookings for this category"""
        return PujaBooking.objects.filter(puja_service__category=obj).count()
    
    def get_total_revenue(self, obj):
        """Get total revenue from this category"""
        revenue = PujaBooking.objects.filter(
            puja_service__category=obj,
            status__in=['CONFIRMED', 'COMPLETED']
        ).aggregate(
            total=Sum('package__price')
        )['total']
        return float(revenue or 0)


class AdminPujaNotificationSerializer(serializers.Serializer):
    """Serializer for manual notifications"""
    booking_id = serializers.IntegerField()
    message_type = serializers.ChoiceField(
        choices=[
            ('reminder', 'Reminder'),
            ('update', 'Update'),
            ('custom', 'Custom Message'),
            ('follow_up', 'Follow-up')
        ]
    )
    custom_message = serializers.CharField(required=False, allow_blank=True)
    include_booking_details = serializers.BooleanField(default=True)
    
    def validate(self, attrs):
        """Validate notification data"""
        message_type = attrs.get('message_type')
        custom_message = attrs.get('custom_message')
        
        if message_type == 'custom' and not custom_message:
            raise serializers.ValidationError({
                'custom_message': 'Custom message is required for custom message type'
            })
        
        return attrs
