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
    AstrologyBookingWithPaymentSerializer,
    AstrologyBookingRescheduleSerializer
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
        
        # Security: Only admin can see all bookings, users see their own
        if self.request.user.is_staff or getattr(self.request.user, 'role', '') == 'ADMIN':
            return AstrologyBooking.objects.all()
        else:
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

class AstrologyBookingRescheduleView(APIView):
    """Reschedule an astrology booking"""
    
    permission_classes = [IsActiveUser]
    
    @swagger_auto_schema(
        operation_description="Reschedule an astrology booking",
        operation_summary="Reschedule Astrology Booking",
        tags=['Astrology'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['preferred_date', 'preferred_time'],
            properties={
                'preferred_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description='New preferred date (YYYY-MM-DD)'
                ),
                'preferred_time': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='New preferred time (HH:MM:SS)'
                ),
                'reason': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Optional reason for rescheduling'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Booking rescheduled successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'booking': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'old_date': openapi.Schema(type=openapi.TYPE_STRING),
                        'old_time': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Bad request"),
            403: openapi.Response(description="Permission denied"),
            404: openapi.Response(description="Booking not found"),
        }
    )
    def patch(self, request, pk):
        """Reschedule astrology booking"""
        from .serializers import AstrologyBookingRescheduleSerializer
        
        try:
            # Get booking
            if request.user.is_staff:
                booking = AstrologyBooking.objects.get(pk=pk)
            else:
                booking = AstrologyBooking.objects.get(pk=pk, user=request.user)
            
            # Check permissions: user can reschedule their own booking, or admin/staff can reschedule any booking
            if not (booking.user == request.user or request.user.is_staff):
                return Response(
                    {'error': 'You do not have permission to reschedule this booking'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate input data
            serializer = AstrologyBookingRescheduleSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    # Reschedule the booking
                    booking.reschedule(
                        serializer.validated_data['preferred_date'],
                        serializer.validated_data['preferred_time'],
                        rescheduled_by=request.user
                    )
                    
                    # Get updated booking data
                    booking_serializer = AstrologyBookingSerializer(booking)
                    
                    return Response({
                        'message': 'Astrology booking rescheduled successfully',
                        'booking': booking_serializer.data,
                        'old_date': str(serializer.validated_data.get('old_date', '')),
                        'old_time': str(serializer.validated_data.get('old_time', ''))
                    }, status=status.HTTP_200_OK)
                    
                except Exception as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except AstrologyBooking.DoesNotExist:
            return Response(
                {'error': 'Astrology booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

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
        """Create astrology booking with payment - Only create booking after successful payment"""
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
            
            # Store all booking data in payment metadata (NOT creating booking yet)
            booking_data = {
                'booking_type': 'astrology',
                'service_id': service.id,
                'service_title': service.title,
                'service_price': float(service.price),
                'user_id': request.user.id,
                'language': validated_data['language'],
                'preferred_date': validated_data['preferred_date'].isoformat(),
                'preferred_time': validated_data['preferred_time'].strftime('%H:%M:%S'),
                'birth_place': validated_data['birth_place'],
                'birth_date': validated_data['birth_date'].isoformat(),
                'birth_time': validated_data['birth_time'].strftime('%H:%M:%S'),
                'gender': validated_data['gender'],
                'questions': validated_data.get('questions', ''),
                'contact_email': validated_data['contact_email'],
                'contact_phone': validated_data['contact_phone'],
                # Store original frontend URL for proper redirects
                'frontend_redirect_url': validated_data['redirect_url']
            }
            
            # Create payment order using PaymentService with professional timeout
            payment_service = PaymentService()
            
            # Use the payment redirect handler URL instead of direct frontend URL
            # The redirect handler will then redirect to the correct frontend page
            payment_redirect_url = f"{request.scheme}://{request.get_host()}/api/payments/redirect/"
            
            # Enhanced booking data with professional timeout settings
            booking_data['payment_timeout_minutes'] = 5  # Professional 5-minute timeout
            booking_data['max_retry_attempts'] = 3
            booking_data['created_timestamp'] = timezone.now().isoformat()
            
            payment_result = payment_service.create_payment_order(
                user=request.user,
                amount=int(service.price * 100),  # Convert to paisa
                redirect_url=payment_redirect_url,  # Use redirect handler
                description=f"Payment for {service.title} - Astrology Consultation",
                metadata=booking_data
            )
            
            if not payment_result['success']:
                return Response({
                    'success': False,
                    'error': 'Failed to create payment order',
                    'details': payment_result.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get the merchant order ID from the payment order
            payment_order = payment_result['payment_order']
            merchant_order_id = payment_order.merchant_order_id
            
            # Prepare response data with professional timeout info
            response_data = {
                'success': True,
                'message': 'Payment initiated successfully with 5-minute timeout. Booking will be created after successful payment.',
                'data': {
                    'payment': {
                        'payment_url': payment_result['payment_url'],
                        'merchant_order_id': merchant_order_id,
                        'amount': payment_order.amount,
                        'amount_in_rupees': f"{payment_order.amount_in_rupees:.2f}",
                        'expires_in_minutes': payment_result.get('expires_in_minutes', 5),
                        'expires_at': payment_result.get('expires_at')
                    },
                    'service': AstrologyServiceSerializer(service).data,
                    'timeout_info': {
                        'expires_in_minutes': payment_result.get('expires_in_minutes', 5),
                        'max_retry_attempts': 3,
                        'message': 'Payment session is valid for 5 minutes'
                    },
                    'redirect_urls': {
                        'success': f"{validated_data['redirect_url'].rstrip('/')}/astro-booking-success?astro_book_id=PLACEHOLDER",
                        'failure': f"{validated_data['redirect_url'].rstrip('/')}/astro-booking-failed?merchant_order_id={merchant_order_id}"
                    }
                }
            }
            
            logger.info(f"Astrology payment initiated successfully: {merchant_order_id} for service: {service.title}")
            
            return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error creating astrology payment: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if request.user.is_staff else 'Please try again later'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AstrologyBookingConfirmationView(APIView):
    """Get astrology booking details by astro_book_id for confirmation page"""
    
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated access for confirmation
    
    @swagger_auto_schema(
        operation_description="Get astrology booking details by astro_book_id",
        operation_summary="Get Astrology Booking Confirmation",
        tags=['Astrology'],
        manual_parameters=[
            openapi.Parameter('astro_book_id', openapi.IN_QUERY, description="Astrology booking ID", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Response(
                description="Booking details retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "booking": {
                                "astro_book_id": "ASTRO_BOOK_20250805_A1B2C3D4",
                                "service": {
                                    "title": "Gemstone Consultation",
                                    "price": "1999.00"
                                },
                                "preferred_date": "2025-08-10",
                                "preferred_time": "10:00:00",
                                "status": "CONFIRMED",
                                "contact_email": "user@example.com"
                            }
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request - Missing astro_book_id"
            ),
            404: openapi.Response(
                description="Booking not found"
            )
        }
    )
    def get(self, request):
        """Get booking details by astro_book_id"""
        try:
            astro_book_id = request.query_params.get('astro_book_id')
            
            if not astro_book_id:
                return Response({
                    'success': False,
                    'error': 'astro_book_id parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                booking = AstrologyBooking.objects.get(astro_book_id=astro_book_id)
            except AstrologyBooking.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Booking not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Serialize booking data
            booking_serializer = AstrologyBookingSerializer(booking)
            
            response_data = {
                'success': True,
                'data': {
                    'booking': booking_serializer.data
                }
            }
            
            logger.info(f"Booking confirmation details retrieved for: {astro_book_id}")
            
            return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error retrieving booking confirmation: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'details': str(e) if hasattr(request, 'user') and request.user.is_staff else 'Please try again later'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)