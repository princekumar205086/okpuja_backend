"""
Clean Serializers for Payments App
"""

from rest_framework import serializers
from .models import PaymentOrder, PaymentRefund, PaymentWebhook


class PaymentOrderSerializer(serializers.ModelSerializer):
    """Payment Order Serializer"""
    
    amount_in_rupees = serializers.ReadOnlyField()
    
    class Meta:
        model = PaymentOrder
        fields = [
            'id', 'merchant_order_id', 'amount', 'amount_in_rupees',
            'currency', 'status', 'payment_method', 'description',
            'phonepe_payment_url', 'redirect_url', 'created_at',
            'updated_at', 'expires_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'merchant_order_id', 'status', 'payment_method',
            'phonepe_payment_url', 'created_at', 'updated_at',
            'expires_at', 'completed_at'
        ]


class CreatePaymentOrderSerializer(serializers.ModelSerializer):
    """Serializer for creating payment orders"""
    
    class Meta:
        model = PaymentOrder
        fields = [
            'amount', 'currency', 'description', 'redirect_url', 'metadata'
        ]
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


class PaymentRefundSerializer(serializers.ModelSerializer):
    """Payment Refund Serializer"""
    
    amount_in_rupees = serializers.ReadOnlyField()
    
    class Meta:
        model = PaymentRefund
        fields = [
            'id', 'merchant_refund_id', 'amount', 'amount_in_rupees',
            'status', 'reason', 'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'merchant_refund_id', 'status', 'created_at',
            'updated_at', 'processed_at'
        ]


class CreateRefundSerializer(serializers.ModelSerializer):
    """Serializer for creating refunds"""
    
    class Meta:
        model = PaymentRefund
        fields = ['amount', 'reason']
    
    def validate_amount(self, value):
        """Validate refund amount"""
        if value <= 0:
            raise serializers.ValidationError("Refund amount must be greater than 0")
        return value


class PaymentWebhookSerializer(serializers.ModelSerializer):
    """Payment Webhook Serializer"""
    
    class Meta:
        model = PaymentWebhook
        fields = [
            'id', 'event_type', 'merchant_order_id', 'raw_data',
            'processed', 'received_at', 'processed_at'
        ]
        read_only_fields = ['id', 'processed', 'received_at', 'processed_at']


class PaymentStatusSerializer(serializers.Serializer):
    """Serializer for payment status response"""
    
    merchant_order_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.IntegerField()
    payment_method = serializers.CharField(required=False)
    phonepe_transaction_id = serializers.CharField(required=False)
    completed_at = serializers.DateTimeField(required=False)
    failure_reason = serializers.CharField(required=False)
