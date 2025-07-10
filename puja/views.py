from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import IsAdminUser, IsActiveUser
from .models import PujaCategory, PujaService, Package, PujaBooking
from .serializers import (
    PujaCategorySerializer, PujaServiceSerializer,
    PackageSerializer, PujaBookingSerializer,
    CreatePujaBookingSerializer
)
from .filters import PujaServiceFilter, PackageFilter

class PujaCategoryListView(generics.ListAPIView):
    queryset = PujaCategory.objects.all()
    serializer_class = PujaCategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class PujaCategoryCreateView(generics.CreateAPIView):
    queryset = PujaCategory.objects.all()
    serializer_class = PujaCategorySerializer
    permission_classes = [IsAdminUser]

class PujaServiceListView(generics.ListAPIView):
    serializer_class = PujaServiceSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = PujaServiceFilter
    search_fields = ['title', 'description']

    def get_queryset(self):
        return PujaService.objects.filter(is_active=True)

class PackageListView(generics.ListAPIView):
    serializer_class = PackageSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PackageFilter

    def get_queryset(self):
        return Package.objects.filter(is_active=True)

class PujaBookingListView(generics.ListAPIView):
    serializer_class = PujaBookingSerializer
    permission_classes = [IsActiveUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['puja_service', 'status', 'booking_date']

    def get_queryset(self):
        # Short-circuit for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return PujaBooking.objects.none()
        
        if self.request.user.is_staff:
            return PujaBooking.objects.all()
        return PujaBooking.objects.filter(user=self.request.user)

class PujaBookingCreateView(generics.CreateAPIView):
    queryset = PujaBooking.objects.all()
    serializer_class = CreatePujaBookingSerializer
    permission_classes = [IsActiveUser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PujaBookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PujaBooking.objects.all()
    serializer_class = PujaBookingSerializer
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        # Short-circuit for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return PujaBooking.objects.none()

        if self.request.user.is_staff:
            return PujaBooking.objects.all()
        return PujaBooking.objects.filter(user=self.request.user)

class PujaCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PujaCategory.objects.all()
    serializer_class = PujaCategorySerializer
    permission_classes = [IsAdminUser]

class PujaServiceCreateView(generics.CreateAPIView):
    queryset = PujaService.objects.all()
    serializer_class = PujaServiceSerializer
    permission_classes = [IsAdminUser]

class PujaServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PujaService.objects.all()
    serializer_class = PujaServiceSerializer
    permission_classes = [IsAdminUser]

class PackageCreateView(generics.CreateAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAdminUser]

class PackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAdminUser]