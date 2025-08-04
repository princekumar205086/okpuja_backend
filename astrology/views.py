from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import uuid
import logging

from .models import AstrologyService, AstrologyBooking
from .serializers import (
    AstrologyServiceSerializer,
    AstrologyBookingSerializer,
    CreateAstrologyBookingSerializer,
    AstrologyBookingWithPaymentSerializer
)
from core.permissions import IsActiveUser
from payments.services import PaymentService

logger = logging.getLogger(__name__)

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

class AstrologyBookingWithPaymentView(APIView):
    """Create astrology booking with payment integration"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create astrology booking with payment integration",
        operation_summary="Book Astrology Service with Payment",
        tags=['Astrology', 'Payments'],
        request_body=AstrologyBookingWithPaymentSerializer,
        responses={
            201: openapi.Response(
                description="Booking created and payment initiated successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Booking created and payment initiated successfully",
                        "data": {
                            "booking": {
                                "id": 123,
                                "service": {
                                    "id": 1,
                                    "title": "Gemstone Consultation",
                                    "price": "1999.00"
                                },
                                "preferred_date": "2025-08-10",
                                "preferred_time": "10:00:00",
                                "status": "PENDING"
                            },
                            "payment": {
                                "payment_url": "https://mercury-uat.phonepe.com/transact/uat_v2?token=...",
                                "merchant_order_id": "ASTRO_ORDER_123456",
                                "amount": 199900,
                                "amount_in_rupees": "1999.00"
                            }
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request - Invalid data",
                examples={
                    "application/json": {
                        "success": False,
                        "errors": {
                            "preferred_date": ["Preferred date cannot be in the past."],
                            "contact_email": ["Enter a valid email address."]
                        }
                    }
                }
            ),
            401: openapi.Response(
                description="Authentication required"
            )
        }
    )
    def post(self, request):
        """Create astrology booking with payment"""
        try:
            # Validate request data
            serializer = AstrologyBookingWithPaymentSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            service = validated_data['service']
            
            with transaction.atomic():
                # Create booking (initially with PENDING status)
                booking_data = {
                    'user': request.user,
                    'service': service,
                    'language': validated_data['language'],
                    'preferred_date': validated_data['preferred_date'],
                    'preferred_time': validated_data['preferred_time'],
                    'birth_place': validated_data['birth_place'],
                    'birth_date': validated_data['birth_date'],
                    'birth_time': validated_data['birth_time'],
                    'gender': validated_data['gender'],
                    'questions': validated_data.get('questions', ''),
                    'contact_email': validated_data['contact_email'],
                    'contact_phone': validated_data['contact_phone'],
                    'status': 'PENDING'  # Will be updated to CONFIRMED after successful payment
                }
                
                booking = AstrologyBooking.objects.create(**booking_data)
                
                # Generate unique merchant order ID
                merchant_order_id = f"ASTRO_ORDER_{booking.id}_{uuid.uuid4().hex[:8].upper()}"
                
                # Prepare payment data
                payment_data = {
                    'amount': int(service.price * 100),  # Convert to paisa
                    'description': f"Payment for {service.title} - Astrology Booking #{booking.id}",
                    'redirect_url': validated_data['redirect_url'],
                    'metadata': {
                        'booking_type': 'astrology',
                        'booking_id': booking.id,
                        'service_id': service.id,
                        'service_title': service.title
                    }
                }
                
                # Create payment order using PaymentService
                payment_service = PaymentService()
                payment_result = payment_service.create_payment_order(
                    user=request.user,
                    **payment_data
                )
                
                if not payment_result['success']:
                    # If payment creation fails, delete the booking
                    booking.delete()
                    return Response({
                        'success': False,
                        'error': 'Failed to create payment order',
                        'details': payment_result.get('error', 'Unknown error')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Update booking with payment reference
                booking.metadata = {
                    'merchant_order_id': merchant_order_id,
                    'payment_order_id': str(payment_result['payment_order'].id)
                }
                booking.save()
                
                # Prepare response data
                booking_serializer = AstrologyBookingSerializer(booking)
                
                response_data = {
                    'success': True,
                    'message': 'Booking created and payment initiated successfully',
                    'data': {
                        'booking': booking_serializer.data,
                        'payment': {
                            'payment_url': payment_result['payment_url'],
                            'merchant_order_id': merchant_order_id,
                            'amount': payment_result['payment_order'].amount,
                            'amount_in_rupees': f"{payment_result['payment_order'].amount_in_rupees:.2f}"
                        }
                    }
                }
                
                logger.info(f"Astrology booking created successfully: {booking.id} with payment order: {merchant_order_id}")
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error creating astrology booking with payment: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if request.user.is_staff else 'Please try again later'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)