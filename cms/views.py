from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import (
    TermsOfService, 
    PrivacyPolicy, 
    CancellationRefundPolicy,
    UserConsent
)
from .serializers import (
    TermsOfServiceSerializer,
    PrivacyPolicySerializer,
    CancellationRefundPolicySerializer,
    UserConsentSerializer,
    CreateUserConsentSerializer
)
from accounts.permissions import IsAdminOrReadOnly

class CurrentTermsOfServiceView(generics.RetrieveAPIView):
    serializer_class = TermsOfServiceSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return get_object_or_404(
            TermsOfService.objects.filter(
                is_current=True,
                status='PUBLISHED'
            )
        )

class TermsOfServiceListView(generics.ListAPIView):
    serializer_class = TermsOfServiceSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return TermsOfService.objects.all().order_by('-version')

class TermsOfServiceCreateView(generics.CreateAPIView):
    serializer_class = TermsOfServiceSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

class TermsOfServiceDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = TermsOfServiceSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class CurrentPrivacyPolicyView(generics.RetrieveAPIView):
    serializer_class = PrivacyPolicySerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return get_object_or_404(
            PrivacyPolicy.objects.filter(
                is_current=True,
                status='PUBLISHED'
            )
        )

class PrivacyPolicyListView(generics.ListAPIView):
    serializer_class = PrivacyPolicySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return PrivacyPolicy.objects.all().order_by('-version')

class PrivacyPolicyCreateView(generics.CreateAPIView):
    serializer_class = PrivacyPolicySerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

class PrivacyPolicyDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PrivacyPolicySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class CurrentCancellationPolicyView(generics.RetrieveAPIView):
    serializer_class = CancellationRefundPolicySerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return get_object_or_404(
            CancellationRefundPolicy.objects.filter(
                is_current=True,
                status='PUBLISHED'
            )
        )

class CancellationPolicyListView(generics.ListAPIView):
    serializer_class = CancellationRefundPolicySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return CancellationRefundPolicy.objects.all().order_by('-version')

class CancellationPolicyCreateView(generics.CreateAPIView):
    serializer_class = CancellationRefundPolicySerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

class CancellationPolicyDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CancellationRefundPolicySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class UserConsentView(generics.CreateAPIView):
    serializer_class = CreateUserConsentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # Return the full consent record
        consent = UserConsent.objects.get(pk=serializer.instance.pk)
        consent_serializer = UserConsentSerializer(
            consent,
            context=self.get_serializer_context()
        )
        
        return Response(
            consent_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class UserConsentHistoryView(generics.ListAPIView):
    serializer_class = UserConsentSerializer