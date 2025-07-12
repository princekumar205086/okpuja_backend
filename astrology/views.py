from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
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


class AstrologyServiceCreateView(generics.CreateAPIView):
    queryset = AstrologyService.objects.all()
    serializer_class = AstrologyServiceSerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]


class AstrologyServiceDetailView(generics.RetrieveAPIView):
    queryset = AstrologyService.objects.all()
    serializer_class = AstrologyServiceSerializer
    permission_classes = [permissions.AllowAny]


class AstrologyServiceUpdateView(generics.UpdateAPIView):
    queryset = AstrologyService.objects.all()
    serializer_class = AstrologyServiceSerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]


class AstrologyServiceDeleteView(generics.DestroyAPIView):
    queryset = AstrologyService.objects.all()
    serializer_class = AstrologyServiceSerializer
    permission_classes = [permissions.IsAdminUser]

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

class AstrologyServiceImageUploadView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, pk):
        try:
            service = AstrologyService.objects.get(pk=pk)
            image_file = request.FILES.get('image')
            
            if not image_file:
                return Response(
                    {'error': 'No image file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service.save_service_image(image_file)
            
            return Response({
                'message': 'Image uploaded successfully',
                'image_url': service.image_url,
                'image_thumbnail_url': service.image_thumbnail_url,
                'image_card_url': service.image_card_url
            })
            
        except AstrologyService.DoesNotExist:
            return Response(
                {'error': 'Service not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Image upload failed: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )