from rest_framework import serializers
from puja.models import PujaCategory, PujaService, Package, PujaBooking

class PujaCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PujaCategory
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

from accounts.models import upload_to_imagekit

class PujaServiceSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=PujaCategory.objects.all(), write_only=True
    )
    category_detail = PujaCategorySerializer(source='category', read_only=True)
    image = serializers.FileField(write_only=True, required=False)
    image_url = serializers.CharField(source='image', read_only=True)

    class Meta:
        model = PujaService
        fields = [
            'id', 'title', 'image', 'image_url',
            'description', 'category', 'category_detail', 'type', 'duration_minutes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        image_file = self.context['request'].FILES.get('image')
        if image_file:
            image_url = upload_to_imagekit(image_file, image_file.name, folder="puja/services")
            validated_data['image'] = image_url
        else:
            validated_data['image'] = ''
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = self.context['request'].FILES.get('image')
        if image_file:
            image_url = upload_to_imagekit(image_file, image_file.name, folder="puja/services")
            validated_data['image'] = image_url
        return super().update(instance, validated_data)

class PackageSerializer(serializers.ModelSerializer):
    puja_service = PujaServiceSerializer(read_only=True)

    class Meta:
        model = Package
        fields = [
            'id', 'puja_service', 'location', 'language', 'package_type',
            'price', 'description', 'includes_materials', 'priest_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class PujaBookingSerializer(serializers.ModelSerializer):
    puja_service = PujaServiceSerializer(read_only=True)
    package = PackageSerializer(read_only=True)

    class Meta:
        model = PujaBooking
        fields = [
            'id', 'user', 'puja_service', 'package', 'booking_date',
            'start_time', 'end_time', 'status', 'contact_name',
            'contact_number', 'contact_email', 'address',
            'special_instructions', 'cancellation_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'status']

class CreatePujaBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PujaBooking
        fields = [
            'puja_service', 'package', 'booking_date', 'start_time',
            'contact_name', 'contact_number', 'contact_email',
            'address', 'special_instructions'
        ]

    def validate(self, data):
        # Add custom validation logic here
        return data