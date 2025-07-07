from django.conf import settings
from django.core.mail import send_mail
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import (
    IsAdminUser,
    IsOwner,
    IsActiveUser  # Assuming this permission exists
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
        user = serializer.save()
        self._send_verification(user)

    def _send_verification(self, user):
        # Send OTP via email
        send_mail(
            'Verify Your Email for OKPUJA',
            f'Welcome to OKPUJA! Your verification code is: {user.otp}. This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
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
