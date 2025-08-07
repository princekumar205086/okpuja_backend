"""
Enterprise-level admin serializers for Booking system
Specialized serializers for admin operations with enhanced data
"""
from rest_framework import serializers
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth import get_user_model
from booking.models import Booking, BookingAttachment, BookingStatus
from cart.models import Cart
from accounts.models import Address

User = get_user_model()


class AdminBookingSerializer(serializers.ModelSerializer):
    """Enhanced booking serializer for admin operations"""
    user_name = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_phone = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_amount = serializers.SerializerMethodField()
    cart_items_count = serializers.SerializerMethodField()
    address_full = serializers.SerializerMethodField()
    booking_age = serializers.SerializerMethodField()
    time_until_service = serializers.SerializerMethodField()
    payment_info = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'book_id', 'user', 'user_name', 'user_email', 'user_phone',
            'cart', 'cart_items_count', 'payment_order_id', 'selected_date', 
            'selected_time', 'address', 'address_full', 'status', 'status_display',
            'assigned_to', 'assigned_to_name', 'cancellation_reason', 
            'failure_reason', 'rejection_reason', 'created_at', 'updated_at',
            'total_amount', 'booking_age', 'time_until_service', 'payment_info',
            'is_overdue'
        ]
    
    def get_user_name(self, obj):
        """Get user's full name or email"""
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.email
    
    def get_user_phone(self, obj):
        """Get user's phone number if available"""
        return getattr(obj.user, 'phone_number', None) or 'N/A'
    
    def get_assigned_to_name(self, obj):
        """Get assigned employee's name"""
        if obj.assigned_to:
            if obj.assigned_to.first_name or obj.assigned_to.last_name:
                return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip()
            return obj.assigned_to.email
        return None
    
    def get_total_amount(self, obj):
        """Get total booking amount"""
        return float(obj.total_amount)
    
    def get_cart_items_count(self, obj):
        """Get number of items in cart"""
        if obj.cart:
            return obj.cart.items.count()
        return 0
    
    def get_address_full(self, obj):
        """Get full address string"""
        if obj.address:
            return obj.address.full_address
        return None
    
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
        
        if not obj.selected_date:
            return None
            
        service_datetime = datetime.combine(obj.selected_date, obj.selected_time or datetime.min.time())
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
    
    def get_payment_info(self, obj):
        """Get payment information"""
        payment_details = obj.payment_details
        return {
            'payment_id': payment_details['payment_id'],
            'status': payment_details['status'],
            'method': payment_details['payment_method'],
            'transaction_id': payment_details['transaction_id']
        }
    
    def get_is_overdue(self, obj):
        """Check if booking is overdue"""
        from django.utils import timezone
        return (
            obj.selected_date < timezone.now().date() and 
            obj.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]
        )


class AdminBookingDetailSerializer(AdminBookingSerializer):
    """Detailed booking serializer with additional information"""
    cart_details = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    payment_details_full = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    assigned_to_details = serializers.SerializerMethodField()
    history_notes = serializers.SerializerMethodField()
    
    class Meta(AdminBookingSerializer.Meta):
        fields = AdminBookingSerializer.Meta.fields + [
            'cart_details', 'address_details', 'attachments', 
            'payment_details_full', 'user_details', 'assigned_to_details',
            'history_notes'
        ]
    
    def get_cart_details(self, obj):
        """Get detailed cart information"""
        if not obj.cart:
            return None
        
        cart_data = {
            'cart_id': obj.cart.cart_id,
            'total_price': float(obj.cart.total_price),
            'discounted_price': float(obj.cart.discounted_price) if obj.cart.discounted_price else None,
            'items_count': obj.cart.items.count(),
            'items': []
        }
        
        # Get cart items details
        for item in obj.cart.items.all():
            item_data = {
                'id': item.id,
                'quantity': item.quantity,
                'item_type': item.content_type.model if item.content_type else 'Unknown'
            }
            
            # Get actual item details based on content type
            if item.content_object:
                if hasattr(item.content_object, 'title'):
                    item_data['name'] = item.content_object.title
                elif hasattr(item.content_object, 'name'):
                    item_data['name'] = item.content_object.name
                else:
                    item_data['name'] = str(item.content_object)
                
                if hasattr(item.content_object, 'price'):
                    item_data['price'] = float(item.content_object.price)
            
            cart_data['items'].append(item_data)
        
        return cart_data
    
    def get_address_details(self, obj):
        """Get detailed address information"""
        if not obj.address:
            return None
        
        return {
            'id': obj.address.id,
            'full_address': obj.address.full_address,
            'street': getattr(obj.address, 'street', ''),
            'city': getattr(obj.address, 'city', ''),
            'state': getattr(obj.address, 'state', ''),
            'pincode': getattr(obj.address, 'pincode', ''),
            'is_default': getattr(obj.address, 'is_default', False)
        }
    
    def get_attachments(self, obj):
        """Get booking attachments"""
        attachments = obj.attachments.all()
        return [{
            'id': attachment.id,
            'image_url': attachment.image.url if attachment.image else None,
            'caption': attachment.caption,
            'uploaded_at': attachment.uploaded_at
        } for attachment in attachments]
    
    def get_payment_details_full(self, obj):
        """Get comprehensive payment details"""
        return obj.payment_details
    
    def get_user_details(self, obj):
        """Get detailed user information"""
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'date_joined': obj.user.date_joined,
            'is_active': obj.user.is_active,
            'phone_number': getattr(obj.user, 'phone_number', None),
            'total_bookings': obj.user.bookings.count(),
            'completed_bookings': obj.user.bookings.filter(status=BookingStatus.COMPLETED).count()
        }
    
    def get_assigned_to_details(self, obj):
        """Get detailed information about assigned employee"""
        if not obj.assigned_to:
            return None
        
        return {
            'id': obj.assigned_to.id,
            'email': obj.assigned_to.email,
            'first_name': obj.assigned_to.first_name,
            'last_name': obj.assigned_to.last_name,
            'is_staff': obj.assigned_to.is_staff,
            'total_assignments': obj.assigned_to.assigned_bookings.count(),
            'completed_assignments': obj.assigned_to.assigned_bookings.filter(
                status=BookingStatus.COMPLETED
            ).count()
        }
    
    def get_history_notes(self, obj):
        """Get booking history and notes"""
        # This would typically come from a separate BookingHistory model
        # For now, return basic status information
        return [
            {
                'timestamp': obj.created_at,
                'action': 'Booking Created',
                'status': obj.status,
                'note': 'Booking was created'
            }
        ]


class AdminBookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating bookings by admin"""
    
    class Meta:
        model = Booking
        fields = [
            'status', 'selected_date', 'selected_time', 'assigned_to',
            'cancellation_reason', 'failure_reason', 'rejection_reason',
            'address'
        ]
    
    def validate(self, attrs):
        """Validate booking update data"""
        status = attrs.get('status')
        
        if status == BookingStatus.CANCELLED and not attrs.get('cancellation_reason'):
            raise serializers.ValidationError({
                'cancellation_reason': 'Cancellation reason is required when cancelling booking'
            })
        
        if status == BookingStatus.REJECTED and not attrs.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting booking'
            })
        
        if status == BookingStatus.FAILED and not attrs.get('failure_reason'):
            raise serializers.ValidationError({
                'failure_reason': 'Failure reason is required when marking booking as failed'
            })
        
        # Validate date/time combinations
        selected_date = attrs.get('selected_date')
        selected_time = attrs.get('selected_time')
        
        # Check for date in past for new bookings
        if selected_date:
            from django.utils import timezone
            if selected_date < timezone.now().date() and status not in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
                raise serializers.ValidationError({
                    'selected_date': 'Service date cannot be in the past unless marking as completed or cancelled'
                })
        
        return attrs


class AdminBookingBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on bookings"""
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
            ('assign_bookings', 'Assign Bookings'),
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
        
        if action == 'assign_bookings' and not value.get('employee_id'):
            raise serializers.ValidationError("Employee ID is required for assignment")
        
        return value


class AdminBookingDashboardSerializer(serializers.Serializer):
    """Serializer for booking dashboard data"""
    total_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    completed_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    rejected_bookings = serializers.IntegerField()
    failed_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_booking_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    assigned_bookings = serializers.IntegerField()
    unassigned_bookings = serializers.IntegerField()
    active_employees = serializers.IntegerField()


class AdminBookingReportSerializer(serializers.Serializer):
    """Serializer for booking reports"""
    report_type = serializers.ChoiceField(
        choices=[
            ('revenue', 'Revenue Report'),
            ('performance', 'Performance Report'),
            ('assignments', 'Assignment Report'),
            ('status', 'Status Report'),
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


class AdminBookingAssignmentSerializer(serializers.Serializer):
    """Serializer for booking assignments"""
    booking_id = serializers.IntegerField()
    employee_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_employee_id(self, value):
        """Validate that employee exists and is staff"""
        try:
            employee = User.objects.get(id=value)
            if not employee.is_staff:
                raise serializers.ValidationError("Selected user is not a staff member")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Employee not found")
    
    def validate_booking_id(self, value):
        """Validate that booking exists and can be assigned"""
        try:
            booking = Booking.objects.get(id=value)
            if not booking.can_be_assigned():
                raise serializers.ValidationError("This booking cannot be assigned")
            return value
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")


class AdminBookingNotificationSerializer(serializers.Serializer):
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


class AdminBookingAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for booking attachments"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BookingAttachment
        fields = ['id', 'image', 'image_url', 'caption', 'uploaded_at']
    
    def get_image_url(self, obj):
        """Get full image URL"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class AdminEmployeeSerializer(serializers.ModelSerializer):
    """Serializer for employee information in admin context"""
    full_name = serializers.SerializerMethodField()
    total_assignments = serializers.SerializerMethodField()
    completed_assignments = serializers.SerializerMethodField()
    active_assignments = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_staff', 'is_active', 'date_joined',
            'total_assignments', 'completed_assignments', 'active_assignments',
            'completion_rate'
        ]
    
    def get_full_name(self, obj):
        """Get employee's full name"""
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.email
    
    def get_total_assignments(self, obj):
        """Get total number of assignments"""
        return obj.assigned_bookings.count()
    
    def get_completed_assignments(self, obj):
        """Get number of completed assignments"""
        return obj.assigned_bookings.filter(status=BookingStatus.COMPLETED).count()
    
    def get_active_assignments(self, obj):
        """Get number of active assignments"""
        return obj.assigned_bookings.filter(
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
        ).count()
    
    def get_completion_rate(self, obj):
        """Calculate completion rate percentage"""
        total = self.get_total_assignments(obj)
        completed = self.get_completed_assignments(obj)
        if total > 0:
            return round((completed / total * 100), 2)
        return 0
