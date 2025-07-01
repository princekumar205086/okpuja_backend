from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import AstrologyService, AstrologyBooking
from .serializers import (
    AstrologyServiceSerializer,
    AstrologyBookingSerializer,
    CreateAstrologyBookingSerializer
)
from core.permissions import IsActiveUser

class AstrologyServiceListView(generics.ListAPIView):
    serializer_class = AstrologyServiceSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['service_type', 'is_active']
    search_fields = ['title', 'description']

    def get_queryset(self):
        return AstrologyService.objects.filter(is_active=True)

class AstrologyBookingListView(generics.ListAPIView):
    serializer_class = AstrologyBookingSerializer
    permission_classes = [IsActiveUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service', 'status', 'preferred_date']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AstrologyBooking.objects.none()
        if self.request.user.is_staff:
            return AstrologyBooking.objects.all()
        return AstrologyBooking.objects.filter(user=self.request.user)

class AstrologyBookingCreateView(generics.CreateAPIView):
    queryset = AstrologyBooking.objects.all()
    serializer_class = CreateAstrologyBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AstrologyBookingDetailView(generics.RetrieveAPIView):
    serializer_class = AstrologyBookingSerializer
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AstrologyBooking.objects.none()
        if self.request.user.is_staff:
            return AstrologyBooking.objects.all()
        return AstrologyBooking.objects.filter(user=self.request.user)

class AstrologyBookingUpdateView(generics.UpdateAPIView):
    serializer_class = CreateAstrologyBookingSerializer
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AstrologyBooking.objects.none()
        if self.request.user.is_staff:
            return AstrologyBooking.objects.all()
        return AstrologyBooking.objects.filter(user=self.request.user)

class AstrologyBookingDeleteView(generics.DestroyAPIView):
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AstrologyBooking.objects.none()
        if self.request.user.is_staff:
            return AstrologyBooking.objects.all()
        return AstrologyBooking.objects.filter(user=self.request.user)