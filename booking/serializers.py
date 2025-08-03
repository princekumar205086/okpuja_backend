from rest_framework import serializers
from .models import Booking, BookingAttachment, BookingStatus
from cart.serializers import CartSerializer
from accounts.serializers import UserBasicSerializer
from accounts.serializers import AddressSerializer
from accounts.models import Address, User
from cart.models import Cart

class BookingAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAttachment
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class BookingSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    cart = CartSerializer(read_only=True)
    address = AddressSerializer(read_only=True)
    assigned_to = UserBasicSerializer(read_only=True)
    attachments = BookingAttachmentSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    payment_details = serializers.SerializerMethodField()
    can_be_rescheduled = serializers.BooleanField(read_only=True)
    can_be_assigned = serializers.BooleanField(read_only=True)

    def get_payment_details(self, obj):
        """Get payment details for this booking"""
        return obj.payment_details

    class Meta:
        model = Booking
        fields = [
            'id', 'book_id', 'user', 'cart', 'selected_date', 
            'selected_time', 'address', 'assigned_to', 'status', 'total_amount',
            'payment_details', 'cancellation_reason', 'failure_reason', 'rejection_reason',
            'created_at', 'updated_at', 'attachments', 'can_be_rescheduled', 'can_be_assigned'
        ]
        read_only_fields = [
            'book_id', 'user', 'cart', 'created_at', 
            'updated_at', 'total_amount', 'payment_details'
        ]

class BookingCreateSerializer(serializers.ModelSerializer):
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='address',
        write_only=True
    )
    cart_id = serializers.PrimaryKeyRelatedField(
        queryset=Cart.objects.all(),
        source='cart',
        write_only=True
    )

    class Meta:
        model = Booking
        fields = [
            'cart_id', 'address_id', 'selected_date', 
            'selected_time', 'status'
        ]

    def validate(self, data):
        cart = data['cart']
        if cart.user != self.context['request'].user:
            raise serializers.ValidationError("Cart does not belong to this user")
        
        if cart.bookings.exists():
            raise serializers.ValidationError("This cart has already been booked")
        
        return data

class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['status', 'cancellation_reason', 'rejection_reason', 'failure_reason']

    def validate(self, data):
        status = data.get('status')
        
        if status == BookingStatus.CANCELLED and not data.get('cancellation_reason'):
            raise serializers.ValidationError("Cancellation reason is required")
        
        if status == BookingStatus.REJECTED and not data.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required")
        
        if status == BookingStatus.FAILED and not data.get('failure_reason'):
            raise serializers.ValidationError("Failure reason is required")
        
        return data

class BookingRescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling a booking"""
    selected_date = serializers.DateField(
        help_text="New date for the booking"
    )
    selected_time = serializers.TimeField(
        help_text="New time for the booking"
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Reason for rescheduling (optional)"
    )

    def validate(self, data):
        # Validate that the new date is not in the past
        from django.utils import timezone
        from datetime import datetime, time as dt_time
        
        new_date = data['selected_date']
        new_time = data['selected_time']
        
        # Combine date and time for comparison
        new_datetime = timezone.make_aware(
            datetime.combine(new_date, new_time)
        )
        
        if new_datetime <= timezone.now():
            raise serializers.ValidationError(
                "Cannot reschedule to a past date and time"
            )
        
        return data

class BookingAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning booking to an employee/priest"""
    assigned_to_id = serializers.IntegerField(
        help_text="ID of the employee/priest to assign"
    )
    notes = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Optional notes about the assignment"
    )

    def validate_assigned_to_id(self, value):
        """Validate that the user exists and is an employee"""
        from accounts.models import User
        try:
            user = User.objects.get(id=value)
            if user.role not in [User.Role.EMPLOYEE, User.Role.ADMIN]:
                raise serializers.ValidationError("User must be an employee or admin")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
    notes = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Assignment notes (optional)"
    )

    def validate_assigned_to_id(self, value):
        try:
            user = User.objects.get(id=value)
            if user.role not in [User.Role.ADMIN, User.Role.EMPLOYEE]:
                raise serializers.ValidationError(
                    "Can only assign to admin or employee users"
                )
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

class AdminBookingListSerializer(serializers.ModelSerializer):
    """Extended serializer for admin with additional fields"""
    user = UserBasicSerializer(read_only=True)
    assigned_to = UserBasicSerializer(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    service_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'book_id', 'user', 'assigned_to', 'selected_date', 
            'selected_time', 'status', 'total_amount', 'service_name',
            'created_at', 'updated_at'
        ]
    
    def get_service_name(self, obj):
        if obj.cart.service_type == 'PUJA' and obj.cart.puja_service:
            return obj.cart.puja_service.name
        elif obj.cart.service_type == 'ASTROLOGY' and obj.cart.astrology_service:
            return obj.cart.astrology_service.name
        return "Unknown Service"