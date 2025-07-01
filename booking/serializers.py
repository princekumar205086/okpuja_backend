from rest_framework import serializers
from .models import Booking, BookingAttachment
from cart.serializers import CartSerializer
from accounts.serializers import UserBasicSerializer
from accounts.serializers import AddressSerializer
from accounts.models import Address 
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
    attachments = BookingAttachmentSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            'id', 'book_id', 'user', 'cart', 'selected_date', 
            'selected_time', 'address', 'status', 'total_amount',
            'cancellation_reason', 'failure_reason', 'rejection_reason',
            'created_at', 'updated_at', 'attachments'
        ]
        read_only_fields = [
            'book_id', 'user', 'cart', 'created_at', 
            'updated_at', 'total_amount'
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