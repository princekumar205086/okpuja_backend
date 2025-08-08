from rest_framework import serializers
from puja.models import PujaCategory, PujaService, Package, PujaBooking

#just pushed to check git history
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
        request = self.context.get('request')
        image_file = request.FILES.get('image') if request else None
        if image_file:
            try:
                # Read file content into bytes (similar to accounts app)
                if hasattr(image_file, 'read'):
                    image_file.seek(0)
                    file_bytes = image_file.read()
                else:
                    with open(image_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using bytes
                from PIL import Image
                from io import BytesIO
                import os
                import uuid
                
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'image': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'service.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                    raise serializers.ValidationError({'image': 'Unsupported image format. Please upload JPG, JPEG, PNG, or GIF.'})
                
                filename = f"service_{uuid.uuid4()}{ext}"
                
                # Upload using bytes (same as accounts app)
                image_url = upload_to_imagekit(file_bytes, filename, folder="puja/services")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'image': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['image'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'image': f'Error processing image: {str(e)}'})
        else:
            validated_data.pop('image', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        image_file = request.FILES.get('image') if request else None
        if image_file:
            try:
                # Read file content into bytes (similar to accounts app)
                if hasattr(image_file, 'read'):
                    image_file.seek(0)
                    file_bytes = image_file.read()
                else:
                    with open(image_file, 'rb') as f:
                        file_bytes = f.read()
                
                # Validate image using bytes
                from PIL import Image
                from io import BytesIO
                import os
                import uuid
                
                try:
                    Image.open(BytesIO(file_bytes)).verify()
                except Exception as e:
                    raise serializers.ValidationError({'image': f'Invalid image file: {str(e)}'})
                
                # Generate unique filename
                original_filename = getattr(image_file, 'name', 'service.jpg')
                ext = os.path.splitext(original_filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                    raise serializers.ValidationError({'image': 'Unsupported image format. Please upload JPG, JPEG, PNG, or GIF.'})
                
                filename = f"service_{uuid.uuid4()}{ext}"
                
                # Upload using bytes (same as accounts app)
                image_url = upload_to_imagekit(file_bytes, filename, folder="puja/services")
                
                if not image_url or not isinstance(image_url, str) or not image_url.startswith('http'):
                    raise serializers.ValidationError({'image': 'Image upload to ImageKit failed. Please try again.'})
                
                validated_data['image'] = image_url
                
            except serializers.ValidationError:
                raise
            except Exception as e:
                raise serializers.ValidationError({'image': f'Error processing image: {str(e)}'})
        else:
            validated_data.pop('image', None)
        return super().update(instance, validated_data)

class PackageSerializer(serializers.ModelSerializer):
    puja_service = serializers.PrimaryKeyRelatedField(queryset=PujaService.objects.all(), write_only=True)
    puja_service_detail = PujaServiceSerializer(source='puja_service', read_only=True)

    class Meta:
        model = Package
        fields = [
            'id', 'puja_service', 'puja_service_detail', 'location', 'language', 'package_type',
            'price', 'description', 'includes_materials', 'priest_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'puja_service_detail']

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
        """
        Add custom validation logic for puja booking
        """
        from django.utils import timezone
        from datetime import datetime, time
        
        # Validate booking date is not in the past
        booking_date = data.get('booking_date')
        if booking_date and booking_date < timezone.now().date():
            raise serializers.ValidationError({'booking_date': 'Booking date cannot be in the past.'})
        
        # Validate start time format and logic
        start_time = data.get('start_time')
        if start_time:
            # Ensure start time is during reasonable hours (6 AM to 9 PM)
            if start_time < time(6, 0) or start_time > time(21, 0):
                raise serializers.ValidationError({'start_time': 'Booking time must be between 6:00 AM and 9:00 PM.'})
        
        # Validate that package belongs to the selected puja service
        puja_service = data.get('puja_service')
        package = data.get('package')
        if puja_service and package:
            if package.puja_service != puja_service:
                raise serializers.ValidationError({'package': 'Selected package does not belong to the chosen puja service.'})
        
        # Validate contact number format (basic validation)
        contact_number = data.get('contact_number')
        if contact_number:
            import re
            pattern = r'^(\+91[\-\s]?)?[0]?(91)?[6789]\d{9}$'
            if not re.match(pattern, contact_number):
                raise serializers.ValidationError({'contact_number': 'Enter a valid Indian phone number.'})
        
        return data

class PujaBookingRescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling puja bookings"""
    new_date = serializers.DateField()
    new_time = serializers.TimeField()
    reason = serializers.CharField(max_length=500, required=False)
    
    def validate_new_date(self, value):
        """Ensure new date is not in the past"""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("Cannot reschedule to a past date")
        return value