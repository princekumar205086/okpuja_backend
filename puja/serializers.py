from rest_framework import serializers
from puja.models import PujaCategory, PujaService, Package, PujaBooking

class PujaCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PujaCategory
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

from accounts.models import upload_to_imagekit

class PujaServiceSerializer(serializers.ModelSerializer):
    category = PujaCategorySerializer(read_only=True)
    image_thumbnail = serializers.ImageField(read_only=True)
    image_card = serializers.ImageField(read_only=True)

    class Meta:
        model = PujaService
        fields = [
            'id', 'title', 'image', 'image_thumbnail', 'image_card',
            'description', 'category', 'type', 'duration_minutes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        image_file = request.FILES.get('image') if request else None
        if image_file:
            image_url = upload_to_imagekit(image_file, image_file.name, folder="puja/services")
            validated_data['image'] = image_url
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        image_file = request.FILES.get('image') if request else None
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