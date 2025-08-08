from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import IsAdminUser, IsActiveUser
from .models import PujaCategory, PujaService, Package, PujaBooking
from .serializers import (
    PujaCategorySerializer, PujaServiceSerializer,
    PackageSerializer, PujaBookingSerializer,
    CreatePujaBookingSerializer, PujaBookingRescheduleSerializer
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
    from rest_framework.parsers import MultiPartParser, FormParser
    parser_classes = [MultiPartParser, FormParser]

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

class PujaBookingRescheduleView(APIView):
    """Reschedule a puja booking"""
    permission_classes = [IsActiveUser]
    
    def post(self, request, pk):
        """Reschedule puja booking"""
        try:
            # Get booking
            if request.user.is_staff:
                booking = PujaBooking.objects.get(pk=pk)
            else:
                booking = PujaBooking.objects.get(pk=pk, user=request.user)
            
            # Check permissions: user can reschedule their own booking, or staff can reschedule any booking
            if not (booking.user == request.user or request.user.is_staff):
                return Response(
                    {'error': 'You do not have permission to reschedule this booking'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate input data
            serializer = PujaBookingRescheduleSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    # Reschedule the booking
                    result = booking.reschedule(
                        serializer.validated_data['new_date'],
                        serializer.validated_data['new_time'],
                        rescheduled_by=request.user
                    )
                    
                    # Get updated booking data
                    booking_serializer = PujaBookingSerializer(booking)
                    
                    return Response({
                        'message': 'Puja booking rescheduled successfully',
                        'booking': booking_serializer.data,
                        'old_date': str(result['old_date']),
                        'old_time': str(result['old_time'])
                    }, status=status.HTTP_200_OK)
                    
                except Exception as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except PujaBooking.DoesNotExist:
            return Response(
                {'error': 'Puja booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )