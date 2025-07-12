from rest_framework import serializers
from .models import AstrologyService, AstrologyBooking
from accounts.serializers import UserSerializer

class AstrologyServiceSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False)
    image_url = serializers.URLField(read_only=True)
    image_thumbnail_url = serializers.URLField(read_only=True)
    image_card_url = serializers.URLField(read_only=True)

    class Meta:
        model = AstrologyService
        fields = [
            'id', 'title', 'service_type', 'description', 'image', 'image_url',
            'image_thumbnail_url', 'image_card_url', 'price', 'duration_minutes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'image_url', 'image_thumbnail_url', 'image_card_url']

    def validate(self, data):
        # Ensure required fields are present
        required_fields = ['title', 'service_type', 'description', 'price', 'duration_minutes']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({field: f"{field} is required."})
        # Validate image only on create
        if self.instance is None and not data.get('image'):
            raise serializers.ValidationError({'image': 'Image is required for service creation.'})
        return data

    def create(self, validated_data):
        # Extract image from validated_data
        image_file = validated_data.pop('image', None)
        
        # Create instance without image
        instance = AstrologyService.objects.create(**validated_data)
        
        # Handle image upload if provided
        if image_file:
            try:
                instance.save_service_image(image_file)
            except Exception as e:
                # Delete the created instance if image upload fails
                instance.delete()
                raise serializers.ValidationError({'image': f'Image upload failed: {str(e)}'})
        
        return instance

    def update(self, instance, validated_data):
        # Extract image from validated_data
        image_file = validated_data.pop('image', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle image upload if provided
        if image_file:
            try:
                instance.save_service_image(image_file)
            except Exception as e:
                raise serializers.ValidationError({'image': f'Image upload failed: {str(e)}'})
        
        instance.save()
        return instance

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