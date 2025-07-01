from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser

from .models import Booking, BookingAttachment
from .serializers import (
    BookingSerializer,
    BookingCreateSerializer,
    BookingStatusUpdateSerializer,
    BookingAttachmentSerializer
)
from core.tasks import send_booking_confirmation

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related(
        'user', 'cart', 'address'
    ).prefetch_related(
        'attachments'
    ).order_by('-created_at')
    
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    search_fields = ['book_id', 'user__email']
    parser_classes = [MultiPartParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        if self.action in ['update_status', 'partial_update_status']:
            return BookingStatusUpdateSerializer
        return BookingSerializer

    def get_queryset(self):
        # For drf_yasg or unauthenticated requests, return all or empty queryset
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        with transaction.atomic():
            booking = serializer.save(user=self.request.user)
            # Mark cart as inactive after booking
            booking.cart.status = 'INACTIVE'
            booking.cart.save()
            # Send confirmation
            send_booking_confirmation.delay(booking.id)

    @action(detail=True, methods=['post', 'patch'], url_path='status')
    def update_status(self, request, pk=None):
        booking = self.get_object()
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(
            booking, 
            data=request.data, 
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            booking = serializer.save()
        
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=['post'])
    def upload_attachment(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingAttachmentSerializer(
            data=request.data,
            context={'booking': booking}
        )
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save()
        
        return Response(
            BookingAttachmentSerializer(attachment).data,
            status=status.HTTP_201_CREATED
        )

class AdminBookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related(
        'user', 'cart', 'address'
    ).prefetch_related(
        'attachments'
    ).order_by('-created_at')
    
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'user']
    search_fields = ['book_id', 'user__email']
    parser_classes = [MultiPartParser]

    def get_serializer_class(self):
        if self.action in ['update_status', 'partial_update_status']:
            return BookingStatusUpdateSerializer
        return BookingSerializer

    @action(detail=True, methods=['post', 'patch'], url_path='status')
    def update_status(self, request, pk=None):
        booking = self.get_object()
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(
            booking, 
            data=request.data, 
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            booking = serializer.save()
        
        return Response(self.get_serializer(booking).data)