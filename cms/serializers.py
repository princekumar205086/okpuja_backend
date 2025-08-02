from rest_framework import serializers
from .models import (
    TermsOfService, 
    PrivacyPolicy, 
    CancellationRefundPolicy,
    UserConsent
)
from accounts.serializers import UserSerializer

class CMSPageSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        fields = [
            'id', 'title', 'slug', 'content',
            'meta_title', 'meta_description', 'meta_keywords',
            'status', 'version', 'is_current',
            'created_by', 'updated_by',
            'created_at', 'updated_at', 'published_at',
            'attachment_url'
        ]
        read_only_fields = [
            'id', 'slug', 'version', 'is_current',
            'created_by', 'updated_by',
            'created_at', 'updated_at', 'published_at',
            'attachment_url'
        ]

    def get_attachment_url(self, obj):
        if obj.attachment:
            return self.context['request'].build_absolute_uri(obj.attachment.url)
        return None

class TermsOfServiceSerializer(CMSPageSerializer):
    class Meta(CMSPageSerializer.Meta):
        model = TermsOfService
        fields = CMSPageSerializer.Meta.fields + ['requires_consent']

class PrivacyPolicySerializer(CMSPageSerializer):
    class Meta(CMSPageSerializer.Meta):
        model = PrivacyPolicy
        fields = CMSPageSerializer.Meta.fields + ['requires_consent']

class CancellationRefundPolicySerializer(CMSPageSerializer):
    class Meta(CMSPageSerializer.Meta):
        model = CancellationRefundPolicy
        fields = CMSPageSerializer.Meta.fields + [
            'refund_period_days', 'cancellation_fee_percentage'
        ]

class UserConsentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    terms = TermsOfServiceSerializer(read_only=True)
    privacy_policy = PrivacyPolicySerializer(read_only=True)

    class Meta:
        model = UserConsent
        fields = [
            'id', 'user', 'terms', 'privacy_policy',
            'user_agent', 'consented_at'
        ]
        read_only_fields = fields

class CreateUserConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserConsent
        fields = ['terms', 'privacy_policy']
        extra_kwargs = {
            'terms': {'required': True},
            'privacy_policy': {'required': True},
        }

    def validate(self, data):
        terms = data['terms']
        privacy_policy = data['privacy_policy']
        
        if not terms.is_current:
            raise serializers.ValidationError(
                "Terms of Service version is not current"
            )
        
        if not privacy_policy.is_current:
            raise serializers.ValidationError(
                "Privacy Policy version is not current"
            )
        
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        return UserConsent.objects.create(
            user=request.user,
            terms=validated_data['terms'],
            privacy_policy=validated_data['privacy_policy'],
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip