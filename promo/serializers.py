from rest_framework import serializers
from .models import PromoCode, PromoCodeUsage

class PromoCodeUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCodeUsage
        fields = ['id', 'discount_amount', 'original_amount', 'used_at']

class PromoCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)
    validity_message = serializers.CharField(read_only=True)
    usages = PromoCodeUsageSerializer(many=True, read_only=True)

    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'description', 'discount', 'discount_type',
            'min_order_amount', 'max_discount_amount', 'start_date',
            'expiry_date', 'usage_limit', 'used_count', 'code_type',
            'is_active', 'is_valid', 'validity_message', 'created_at',
            'updated_at', 'usages'
        ]
        read_only_fields = ['created_at', 'updated_at', 'used_count', 'usages']

class PromoCodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = [
            'code', 'description', 'discount', 'discount_type',
            'min_order_amount', 'max_discount_amount', 'start_date',
            'expiry_date', 'usage_limit', 'code_type', 'is_active'
        ]

    def validate(self, data):
        if data['discount_type'] == PromoCode.DISCOUNT_TYPES.PERCENT and data['discount'] > 100:
            raise serializers.ValidationError("Percentage discount cannot exceed 100%")
        return data

class ValidatePromoCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    user_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate(self, attrs):
        try:
            promo_code = PromoCode.objects.get(code=attrs['code'])
        except PromoCode.DoesNotExist:
            raise serializers.ValidationError("Invalid promo code")

        is_valid, message = promo_code.is_valid_for_user()
        if not is_valid:
            raise serializers.ValidationError(message)

        attrs['promo_code'] = promo_code
        return attrs

class BulkCreatePromoCodeSerializer(serializers.Serializer):
    prefix = serializers.CharField(max_length=20)
    count = serializers.IntegerField(min_value=1, max_value=100)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_type = serializers.ChoiceField(choices=PromoCode.DISCOUNT_TYPES)
    expiry_date = serializers.DateTimeField()
    usage_limit = serializers.IntegerField(default=1)

    def create(self, validated_data):
        from django.utils.crypto import get_random_string
        created = []
        
        for _ in range(validated_data['count']):
            code = f"{validated_data['prefix']}{get_random_string(8).upper()}"
            promo = PromoCode.objects.create(
                code=code,
                discount=validated_data['discount'],
                discount_type=validated_data['discount_type'],
                expiry_date=validated_data['expiry_date'],
                usage_limit=validated_data['usage_limit'],
                created_by=self.context['request'].user
            )
            created.append(promo)
        
        return created