from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    UserListView,
    UserDetailView,
    UserProfileView,
    AddressListView,
    AddressDetailView,
    UserRoleCheckView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    OTPRequestView,
    OTPVerifyView,
    PanCardDetailView
)

urlpatterns = [
    # Authentication
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),

    # User Management
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Address Management
    path('addresses/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),

    # Password Reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # OTP
    path('otp/request/', OTPRequestView.as_view(), name='otp_request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp_verify'),

    # Utilities
    path('check-role/', UserRoleCheckView.as_view(), name='user-role-check'),

    # PAN Card
    path('pancard/', PanCardDetailView.as_view(), name='pancard-detail'),
]
