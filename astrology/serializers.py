from rest_framework import serializers
from .models import AstrologyService, AstrologyBooking
from accounts.serializers import UserSerializer

class AstrologyServiceSerializer(serializers.ModelSerializer):
    image_thumbnail = serializers.ImageField(read_only=True)
    image_card = serializers.ImageField(read_only=True)

    class Meta:
        model = AstrologyService
        fields = [
            'id', 'title', 'service_type', 'description', 'image', 
            'image_thumbnail', 'image_card', 'price', 'duration_minutes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class AstrologyBookingSerializer(serializers.ModelSerializer):
    service = AstrologyServiceSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = AstrologyBooking
        fields = [
            'id', 'user', 'service', 'language', 'preferred_date',
            'preferred_time', 'birth_place', 'birth_date', 'birth_time',
            'gender', 'questions', 'status', 'contact_email', 'contact_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'status']

class CreateAstrologyBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstrologyBooking
        fields = [
            'service', 'language', 'preferred_date', 'preferred_time',
            'birth_place', 'birth_date', 'birth_time', 'gender', 'questions',
            'contact_email', 'contact_phone'
        ]

    def validate(self, data):
        # Add custom validation logic here
        return data