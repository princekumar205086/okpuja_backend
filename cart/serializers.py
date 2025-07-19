# cart/serializers.py
from rest_framework import serializers
from .models import Cart
from puja.models import PujaService, Package
from astrology.models import AstrologyService
from promo.models import PromoCode
from puja.serializers import PujaServiceSerializer, PackageSerializer
from astrology.serializers import AstrologyServiceSerializer
from promo.serializers import PromoCodeSerializer

class CartSerializer(serializers.ModelSerializer):
    puja_service = PujaServiceSerializer(read_only=True)
    package = PackageSerializer(read_only=True)
    astrology_service = AstrologyServiceSerializer(read_only=True)
    promo_code = PromoCodeSerializer(read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    can_delete = serializers.BooleanField(
        source='can_be_deleted',
        read_only=True,
        help_text="Indicates if cart can be safely deleted"
    )
    
    class Meta:
        model = Cart
        fields = [
            'id', 'cart_id', 'user', 'service_type', 
            'puja_service', 'package', 'astrology_service',
            'selected_date', 'selected_time', 'promo_code',
            'status', 'created_at', 'updated_at', 'total_price', 'can_delete'
        ]
        read_only_fields = ['user', 'cart_id', 'status', 'created_at', 'updated_at']

class CartCreateSerializer(serializers.ModelSerializer):
    puja_service = serializers.PrimaryKeyRelatedField(
        queryset=PujaService.objects.all(),
        required=False,
        allow_null=True
    )
    package_id = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all(),
        source='package',
        required=False,
        write_only=True
    )
    astrology_service_id = serializers.PrimaryKeyRelatedField(
        queryset=AstrologyService.objects.all(),
        source='astrology_service',
        required=False,
        write_only=True
    )
    promo_code = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Cart
        fields = [
            'service_type', 'puja_service', 'puja_service_id', 'package_id',
            'astrology_service_id', 'selected_date', 'selected_time',
            'promo_code'
        ]

    def validate(self, attrs):
        service_type = attrs.get('service_type')
        
        if service_type == 'PUJA':
            if not attrs.get('puja_service') or not attrs.get('package'):
                raise serializers.ValidationError(
                    "Both puja_service and package are required for PUJA service type"
                )
            if attrs.get('astrology_service'):
                raise serializers.ValidationError(
                    "astrology_service should not be provided for PUJA service type"
                )
        elif service_type == 'ASTROLOGY':
            if not attrs.get('astrology_service'):
                raise serializers.ValidationError(
                    "astrology_service is required for ASTROLOGY service type"
                )
            if attrs.get('puja_service') or attrs.get('package'):
                raise serializers.ValidationError(
                    "puja_service and package should not be provided for ASTROLOGY service type"
                )
        
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        
        # Handle promo code
        promo_code = validated_data.pop('promo_code', None)
        if promo_code:
            try:
                promo = PromoCode.objects.get(code=promo_code, is_active=True)
                validated_data['promo_code'] = promo
            except PromoCode.DoesNotExist:
                pass
        
        # Generate unique cart ID
        validated_data['cart_id'] = self.generate_cart_id()
        
        return super().create(validated_data)

    def generate_cart_id(self):
        import uuid
        return str(uuid.uuid4())