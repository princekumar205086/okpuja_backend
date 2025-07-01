from rest_framework import serializers
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import json
from .models import Payment, Refund, PaymentStatus, PaymentMethod
from booking.serializers import BookingSerializer
from accounts.serializers import UserBasicSerializer

class PaymentMethodSerializer(serializers.Serializer):
    """
    Serializer for available payment methods with additional metadata
    """
    code = serializers.CharField()
    name = serializers.CharField()
    icon = serializers.CharField(required=False, help_text="URL to payment method icon")
    description = serializers.CharField(required=False)
    min_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        required=False,
        default=Decimal('10.00')
    )
    max_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        required=False,
        default=Decimal('100000.00')
    )

    class Meta:
        fields = ['code', 'name', 'icon', 'description', 'min_amount', 'max_amount']


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new payment transactions
    Includes validation for booking ownership and amount matching
    """
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Payment amount in INR"
    )

    class Meta:
        model = Payment
        fields = [
            'booking', 
            'amount', 
            'currency', 
            'method',
            'callback_url',
            'redirect_url'
        ]
        extra_kwargs = {
            'booking': {
                'required': True,
                'help_text': "ID of the booking being paid for"
            },
            'amount': {
                'required': True,
                'help_text': "Payment amount (must match booking total)"
            },
            'currency': {
                'required': False,
                'default': 'INR',
                'help_text': "Currency code (default: INR)"
            },
            'method': {
                'required': False,
                'default': PaymentMethod.PHONEPE,
                'help_text': f"Payment method (default: {PaymentMethod.PHONEPE})"
            },
            'callback_url': {
                'required': False,
                'help_text': "Custom callback URL for payment webhook"
            },
            'redirect_url': {
                'required': False,
                'help_text': "Custom redirect URL after payment completion"
            }
        }

    def validate(self, data):
        """
        Validate payment creation:
        1. Booking belongs to requesting user
        2. Amount matches booking total
        3. No existing successful payment for booking
        """
        booking = data['booking']
        amount = data['amount']
        request = self.context.get('request')

        if booking.user != request.user:
            raise serializers.ValidationError(
                {"booking": "Booking does not belong to this user"}
            )

        if amount != booking.total_amount:
            raise serializers.ValidationError(
                {"amount": f"Payment amount must be exactly {booking.total_amount}"}
            )

        if booking.payments.filter(status=PaymentStatus.SUCCESS).exists():
            raise serializers.ValidationError(
                {"booking": "This booking already has a successful payment"}
            )

        return data


class PaymentDetailSerializer(serializers.ModelSerializer):
    """
    Detailed payment serializer with expanded relationships and computed fields
    Used for retrieving single payment records
    """
    booking = BookingSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
        help_text="Human-readable payment status"
    )
    method_display = serializers.CharField(
        source='get_method_display',
        read_only=True,
        help_text="Human-readable payment method"
    )
    is_refundable = serializers.SerializerMethodField(
        help_text="Indicates if payment can be refunded"
    )
    payment_url = serializers.SerializerMethodField(
        help_text="URL to redirect user to complete payment"
    )
    gateway_response_pretty = serializers.SerializerMethodField(
        help_text="Formatted gateway response for debugging"
    )

    class Meta:
        model = Payment
        fields = [
            'id',
            'transaction_id',
            'merchant_transaction_id',
            'booking',
            'amount',
            'currency',
            'method',
            'method_display',
            'status',
            'status_display',
            'phonepe_payment_id',
            'payment_url',
            'callback_url',
            'redirect_url',
            'is_refundable',
            'gateway_response',
            'gateway_response_pretty',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'transaction_id',
            'merchant_transaction_id',
            'status',
            'phonepe_payment_id',
            'gateway_response',
            'created_at',
            'updated_at'
        ]

    def get_is_refundable(self, obj):
        """Determine if payment can be refunded"""
        return (
            obj.status == PaymentStatus.SUCCESS and
            obj.method != PaymentMethod.COD
        )

    def get_payment_url(self, obj):
        """Generate payment URL for frontend redirection"""
        if obj.method == PaymentMethod.PHONEPE and obj.gateway_response:
            return obj.gateway_response.get('data', {}).get('instrumentResponse', {}).get('redirectInfo', {}).get('url')
        return None

    def get_gateway_response_pretty(self, obj):
        """Format gateway response for debugging"""
        if obj.gateway_response:
            return json.dumps(obj.gateway_response, indent=2)
        return None


class PaymentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for payment lists
    Optimized for listing multiple payments with minimal data
    """
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    method_display = serializers.CharField(
        source='get_method_display',
        read_only=True
    )
    booking_id = serializers.CharField(
        source='booking.book_id',
        read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id',
            'transaction_id',
            'booking_id',
            'amount',
            'currency',
            'method',
            'method_display',
            'status',
            'status_display',
            'created_at'
        ]


class PaymentStatusSerializer(serializers.Serializer):
    """
    Serializer for validating payment status updates from gateways
    Used in webhook processing
    """
    merchantId = serializers.CharField(max_length=100)
    merchantTransactionId = serializers.CharField(max_length=100)
    transactionId = serializers.CharField(max_length=100, required=False)
    amount = serializers.IntegerField(
        help_text="Amount in paise (1 INR = 100 paise)"
    )
    state = serializers.CharField(max_length=20)
    responseCode = serializers.CharField(max_length=10, required=False)
    paymentInstrument = serializers.DictField(required=False)

    def validate(self, data):
        """Validate payment status data"""
        valid_states = ['COMPLETED', 'FAILED', 'PENDING']
        if data['state'] not in valid_states:
            raise serializers.ValidationError({
                "state": f"Must be one of: {', '.join(valid_states)}"
            })
        return data


class PaymentWebhookSerializer(serializers.Serializer):
    """
    Serializer for PhonePe webhook payload
    Includes signature verification
    """
    response = PaymentStatusSerializer()
    merchantId = serializers.CharField(max_length=100)
    merchantTransactionId = serializers.CharField(max_length=100)
    callbackUrl = serializers.URLField(required=False)
    redirectUrl = serializers.URLField(required=False)
    signature = serializers.CharField(max_length=200)


class RefundRequestSerializer(serializers.Serializer):
    """
    Serializer for initiating refund requests
    Includes validation for refund amount
    """
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount to refund (cannot exceed original payment)"
    )
    reason = serializers.CharField(
        max_length=255,
        help_text="Reason for refund"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional notes about the refund"
    )

    def validate_amount(self, value):
        """Validate refund amount doesn't exceed payment amount"""
        payment = self.context['payment']
        if value > payment.amount:
            raise serializers.ValidationError(
                "Refund amount cannot exceed original payment amount"
            )
        return value


class RefundDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for refund records
    Includes related payment information
    """
    payment = PaymentListSerializer(read_only=True)
    processed_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = Refund
        fields = [
            'id',
            'refund_id',
            'payment',
            'amount',
            'reason',
            'notes',
            'status',
            'gateway_response',
            'processed_by',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'refund_id',
            'payment',
            'status',
            'gateway_response',
            'processed_by',
            'created_at'
        ]


class PaymentInitiationResponseSerializer(serializers.Serializer):
    """
    Standardized response format for payment initiation
    """
    success = serializers.BooleanField()
    payment_id = serializers.CharField()
    merchant_transaction_id = serializers.CharField()
    transaction_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    payment_url = serializers.URLField()
    status = serializers.CharField()
    timestamp = serializers.DateTimeField(default=timezone.now)


class PaymentStatusResponseSerializer(serializers.Serializer):
    """
    Standardized response format for payment status checks
    """
    success = serializers.BooleanField()
    code = serializers.CharField()
    message = serializers.CharField()
    transaction_id = serializers.CharField()
    merchant_transaction_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField()
    payment_method = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField(default=timezone.now)


class RefundResponseSerializer(serializers.Serializer):
    """
    Standardized response format for refund operations
    """
    success = serializers.BooleanField()
    refund_id = serializers.CharField()
    payment_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    timestamp = serializers.DateTimeField(default=timezone.now)


# Admin-specific serializers
class AdminPaymentSerializer(PaymentDetailSerializer):
    """
    Extended payment serializer for admin views
    Includes additional debugging information
    """
    user = serializers.SerializerMethodField()

    class Meta(PaymentDetailSerializer.Meta):
        fields = PaymentDetailSerializer.Meta.fields + ['user']

    def get_user(self, obj):
        """Include basic user information"""
        return UserBasicSerializer(obj.booking.user).data


class AdminRefundSerializer(RefundDetailSerializer):
    """
    Extended refund serializer for admin views
    Includes additional processing information
    """
    class Meta(RefundDetailSerializer.Meta):
        fields = RefundDetailSerializer.Meta.fields + ['processed_by']