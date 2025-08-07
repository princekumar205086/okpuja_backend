from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserProfile, Address, PanCard


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['account_status'] = user.account_status
        token['email_verified'] = user.otp_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data.update({
            'id': self.user.id,
            'email': self.user.email,
            'role': self.user.role,
            'account_status': self.user.account_status,
            'email_verified': self.user.otp_verified
        })

        if not self.user.is_active:
            raise serializers.ValidationError(
                "Account is inactive. Please contact support."
            )

        if not self.user.otp_verified:
            raise serializers.ValidationError(
                "Account not verified. Please verify your email first."
            )

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'phone',
            'role', 'account_status', 'is_active', 'date_joined'
        ]
        read_only_fields = ['account_status', 'date_joined', 'role', 'is_active']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=[('USER', 'User'), ('EMPLOYEE', 'Employee/Priest')], default='USER',
                                   required=False)
    employee_registration_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['email', 'phone', 'password', 'password2', 'role', 'employee_registration_code']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Check for existing email
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                "email": "A user with this email address already exists."
            })
        
        # Check for existing phone number if provided
        phone = attrs.get('phone')
        if phone and User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({
                "phone": "A user with this phone number already exists."
            })

        role = attrs.get('role', 'USER')
        if role == 'EMPLOYEE':
            code = attrs.get('employee_registration_code')
            from django.conf import settings
            expected_code = getattr(settings, 'EMPLOYEE_REGISTRATION_CODE', None)
            if not code or not expected_code or code != expected_code:
                raise serializers.ValidationError(
                    {"employee_registration_code": "Invalid or missing employee registration code."})
        return attrs

    def create(self, validated_data):
        from django.db import IntegrityError
        
        role = validated_data.pop('role', 'USER')
        validated_data.pop('employee_registration_code', None)

        try:
            # Use the custom manager's create_user method
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                phone=validated_data.get('phone', ''),
                role=role
            )
            user.generate_otp()
            return user
        except IntegrityError as e:
            # Handle unique constraint violations
            error_message = str(e)
            if 'accounts_user.phone' in error_message:
                raise serializers.ValidationError({
                    "phone": "A user with this phone number already exists."
                })
            elif 'accounts_user.email' in error_message:
                raise serializers.ValidationError({
                    "email": "A user with this email address already exists."
                })
            else:
                # Generic integrity error
                raise serializers.ValidationError({
                    "non_field_errors": "Registration failed due to a data conflict. Please check your information."
                })


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    profile_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'dob',
            'profile_picture', 'profile_thumbnail',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_profile_picture(self, obj):
        return obj.profile_picture_url if obj.profile_picture_url else None

    def get_profile_thumbnail(self, obj):
        return obj.profile_thumbnail_url if obj.profile_thumbnail_url else None


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country',
            'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(required=True, validators=[validate_password])


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    via = serializers.ChoiceField(choices=['email', 'sms'], default='email')


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6)


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone']


class PanCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanCard
        fields = '__all__'
        read_only_fields = ('user', 'is_verified')
class PanCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanCard
        fields = '__all__'
        read_only_fields = ('user', 'is_verified')
class PanCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanCard
        fields = '__all__'
        read_only_fields = ('user', 'is_verified')
