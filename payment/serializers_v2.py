"""
Payment Serializers for PhonePe V2 Integration
Clean and simplified serializers following DRF best practices
"""
from rest_framework import serializers
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from .models import Payment, Refund, PaymentStatus, PaymentMethod
from accounts.serializers import UserBasicSerializer
from cart.serializers import CartSerializer

class PaymentMethodSerializer(serializers.Serializer):
    """Serializer for available payment methods"""
    code = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    icon = serializers.CharField(required=False)
    min_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    max_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100000.00'))

class PaymentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating payment from cart
    Following PhonePe V2 Standard Checkout flow
    """
    cart_id = serializers.IntegerField(
        help_text="ID of the cart to process payment for"
    )

    def validate_cart_id(self, value):
        """Validate cart exists and belongs to user"""
        from cart.models import Cart
        
        user = self.context['request'].user
        
        try:
            cart = Cart.objects.get(id=value, user=user, status='ACTIVE')
            if cart.total_price <= 0:
                raise serializers.ValidationError("Cart is empty or has invalid total")
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive cart")
        
        return value

class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for payment list view"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'merchant_transaction_id',
            'amount', 'currency', 'method', 'status',
            'created_at', 'user'
        ]

class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed payment view"""
    user = UserBasicSerializer(read_only=True)
    cart = CartSerializer(read_only=True)
    gateway_response = serializers.JSONField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'merchant_transaction_id',
            'amount', 'currency', 'method', 'status',
            'gateway_response', 'phonepe_payment_id',
            'created_at', 'updated_at',
            'user', 'cart', 'booking'
        ]

class PaymentInitiationResponseSerializer(serializers.Serializer):
    """Response serializer for payment initiation"""
    success = serializers.BooleanField()
    payment_id = serializers.IntegerField()
    merchant_transaction_id = serializers.CharField()
    transaction_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    payment_url = serializers.URLField()
    status = serializers.CharField()

class PaymentStatusResponseSerializer(serializers.Serializer):
    """Response serializer for payment status"""
    success = serializers.BooleanField()
    payment_id = serializers.IntegerField()
    status = serializers.CharField()
    merchant_transaction_id = serializers.CharField()
    verification_data = serializers.JSONField()

class PaymentWebhookSerializer(serializers.Serializer):
    """Serializer for webhook data"""
    response = serializers.CharField(required=False)
    merchantTransactionId = serializers.CharField(required=False)
    
    def validate(self, data):
        """Validate webhook has required data"""
        if not data.get('response') and not data.get('merchantTransactionId'):
            raise serializers.ValidationError("Invalid webhook data")
        return data

class RefundRequestSerializer(serializers.Serializer):
    """Serializer for refund request"""
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Refund amount (if not provided, full refund will be processed)"
    )
    reason = serializers.CharField(
        max_length=500, 
        required=False,
        help_text="Reason for refund"
    )

class RefundDetailSerializer(serializers.ModelSerializer):
    """Serializer for refund details"""
    payment = PaymentListSerializer(read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'refund_id', 'amount', 'status',
            'reason', 'gateway_response',
            'created_at', 'updated_at', 'payment'
        ]

class RefundResponseSerializer(serializers.Serializer):
    """Response serializer for refund operations"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    refund_id = serializers.CharField(required=False)
    payment_id = serializers.IntegerField()

# Admin serializers
class AdminPaymentSerializer(PaymentDetailSerializer):
    """Admin serializer with additional fields"""
    
    class Meta(PaymentDetailSerializer.Meta):
        fields = PaymentDetailSerializer.Meta.fields + [
            'gateway_transaction_id', 'failure_reason'
        ]

class AdminRefundSerializer(RefundDetailSerializer):
    """Admin serializer for refunds"""
    
    class Meta(RefundDetailSerializer.Meta):
        fields = RefundDetailSerializer.Meta.fields + [
            'processed_by', 'internal_notes'
        ]
