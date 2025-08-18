from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.permissions import (
    IsAdminUser,
    IsOwner,
    IsActiveUser  
)
from .models import User, UserProfile, Address, SMSLog, PanCard
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    AddressSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PanCardSerializer
)
from .sms import send_sms  # Assuming you have an sms utility file


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework import serializers as drf_serializers
        
        try:
            user = serializer.save()
            self._send_verification(user)
        except IntegrityError as e:
            # Handle any IntegrityError that might slip through serializer validation
            error_message = str(e)
            if 'accounts_user.phone' in error_message:
                raise drf_serializers.ValidationError({
                    "phone": "A user with this phone number already exists."
                })
            elif 'accounts_user.email' in error_message:
                raise drf_serializers.ValidationError({
                    "email": "A user with this email address already exists."
                })
            else:
                raise drf_serializers.ValidationError({
                    "non_field_errors": "Registration failed due to a data conflict. Please check your information."
                })

    def _send_verification(self, user):
        # Send professional OTP email
        from django.template.loader import render_to_string
        
        html_message = render_to_string('emails/otp_verification.html', {
            'otp_code': user.otp,
            'expiry_minutes': settings.OTP_EXPIRE_MINUTES,
            'current_year': timezone.now().year
        })
        
        from django.core.mail import EmailMessage
        email = EmailMessage(
            '🔐 Verify Your Email - OkPuja Account Activation',
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.content_subtype = "html"
        email.send()
        # Send OTP via SMS if phone number is provided
        if user.phone:
            message = f"Your OKPUJA verification code is {user.otp}. This code is valid for {settings.OTP_EXPIRE_MINUTES} minutes. Do not share this code."
            sms_status = send_sms(user.phone, message)
            SMSLog.objects.create(
                phone=user.phone,
                message=message,
                status=sms_status
            )


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsOwner()]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.profile
        except UserProfile.DoesNotExist:
            # Create profile with safe defaults
            return UserProfile.objects.create(
                user=self.request.user,
                first_name='',
                last_name=''
            )


class AddressListView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)


class UserRoleCheckView(APIView):
    permission_classes = [IsActiveUser]

    def get(self, request):
        return Response({
            'is_admin': request.user.role == User.Role.ADMIN,
            'is_employee': request.user.role == User.Role.EMPLOYEE,
            'is_public_user': request.user.role == User.Role.USER
        })


class PasswordResetRequestView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            otp = user.generate_otp()

            # Send OTP via email
            send_mail(
                'Password Reset OTP',
                f'Your password reset code is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            if user.phone:
                message = f"Your OKPUJA password reset code is: {otp}"
                sms_status = send_sms(user.phone, message)
                SMSLog.objects.create(
                    phone=user.phone,
                    message=message,
                    status=sms_status
                )

            return Response({'detail': 'OTP sent successfully.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User with this email does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )


class PasswordResetConfirmView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            if user.verify_otp(serializer.validated_data['otp']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
            return Response(
                {'detail': 'Invalid or expired OTP.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'User with this email does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )


class OTPRequestView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = OTPRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            otp = user.generate_otp()

            if serializer.validated_data['via'] == 'sms' and user.phone:
                message = f"Your OKPUJA verification code is: {otp}"
                sms_status = send_sms(user.phone, message)
                SMSLog.objects.create(
                    phone=user.phone,
                    message=message,
                    status=sms_status
                )
            else:
                send_mail(
                    'Your Verification Code',
                    f'Your verification code is: {otp}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

            return Response({'detail': 'OTP sent successfully.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User with this email does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )


class OTPVerifyView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = OTPVerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            if user.verify_otp(serializer.validated_data['otp']):
                user.account_status = User.AccountStatus.ACTIVE
                user.is_active = True
                # Ensure otp_verified is set to True
                user.otp_verified = True
                user.save(update_fields=['account_status', 'is_active', 'otp_verified'])
                return Response({'detail': 'OTP verified successfully.'}, status=status.HTTP_200_OK)
            return Response(
                {'detail': 'Invalid or expired OTP.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'User with this email does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )


class PanCardDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PanCardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        pancard, _ = PanCard.objects.get_or_create(user=self.request.user)
        return pancard


class UserProfilePictureUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = request.user.profile
        image_file = request.FILES.get('profile_picture')
        if not image_file:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        profile.save_profile_picture(image_file)
        return Response({'profile_picture_url': profile.profile_picture_url, 'profile_thumbnail_url': profile.profile_thumbnail_url})


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LogoutSerializer,
        responses={
            205: openapi.Response('Logout successful'),
            400: openapi.Response('Bad request')
        }
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
