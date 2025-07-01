from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, Address

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

    class Meta:
        model = User
        fields = ['email', 'phone', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            phone=validated_data.get('phone', '')
        )
        user.set_password(validated_data['password'])
        user.generate_otp()
        # user.save() is called inside generate_otp
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'dob',
            'profile_picture', 'profile_thumbnail',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

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