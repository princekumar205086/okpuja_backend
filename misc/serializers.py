from rest_framework import serializers
from .models import Event, JobOpening, ContactUs

class EventSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    original_image_url = serializers.SerializerMethodField()
    days_until = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description',
            'thumbnail_url', 'banner_url', 'original_image_url',
            'event_date', 'start_time', 'end_time', 'location',
            'registration_link', 'status', 'is_featured',
            'days_until', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return self.context['request'].build_absolute_uri(obj.thumbnail.url)
        return None

    def get_banner_url(self, obj):
        if obj.banner:
            return self.context['request'].build_absolute_uri(obj.banner.url)
        return None

    def get_original_image_url(self, obj):
        if obj.original_image:
            return self.context['request'].build_absolute_uri(obj.original_image.url)
        return None

    def get_days_until(self, obj):
        from django.utils import timezone
        if obj.event_date:
            delta = obj.event_date - timezone.now().date()
            return delta.days
        return None

class JobOpeningSerializer(serializers.ModelSerializer):
    is_open = serializers.BooleanField(read_only=True)
    days_until_deadline = serializers.SerializerMethodField()
    
    class Meta:
        model = JobOpening
        fields = [
            'id', 'title', 'slug', 'description',
            'responsibilities', 'requirements',
            'job_type', 'location', 'salary_range',
            'application_deadline', 'application_link',
            'is_active', 'is_open', 'days_until_deadline',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_days_until_deadline(self, obj):
        from django.utils import timezone
        if obj.application_deadline:
            delta = obj.application_deadline - timezone.now()
            return delta.days
        return None

class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = [
            'id', 'name', 'email', 'phone',
            'subject', 'message', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

class ContactUsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = [
            'name', 'email', 'phone',
            'subject', 'message'
        ]
        
    def create(self, validated_data):
        request = self.context['request']
        return ContactUs.objects.create(
            **validated_data,
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

class ContactUsAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = [
            'id', 'name', 'email', 'phone',
            'subject', 'message', 'status',
            'ip_address', 'user_agent',
            'created_at', 'updated_at', 'replied_at'
        ]
        read_only_fields = fields