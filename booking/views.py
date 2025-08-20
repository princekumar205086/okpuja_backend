from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import logging

from .models import Booking, BookingAttachment, BookingStatus
from .serializers import (
    BookingSerializer,
    BookingCreateSerializer,
    BookingStatusUpdateSerializer,
    BookingAttachmentSerializer,
    BookingRescheduleSerializer,
    BookingAssignmentSerializer,
    AdminBookingListSerializer
)
from core.tasks import send_booking_confirmation
from core.permissions import IsAdminUser, IsStaffUser
from accounts.models import User

logger = logging.getLogger(__name__)

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related(
        'user', 'cart', 'address', 'assigned_to'
    ).prefetch_related(
        'attachments'
    ).order_by('-created_at')
    
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'assigned_to']
    search_fields = ['book_id', 'user__email']
    parser_classes = [MultiPartParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        if self.action in ['update_status', 'partial_update_status']:
            return BookingStatusUpdateSerializer
        if self.action == 'reschedule':
            return BookingRescheduleSerializer
        return BookingSerializer

    def get_queryset(self):
        # For drf_yasg or unauthenticated requests, return all or empty queryset
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return self.queryset.none()
        
        # Regular users see their own bookings
        # Employees see bookings assigned to them + their own bookings
        queryset = self.queryset.filter(user=self.request.user)
        
        if self.request.user.role == User.Role.EMPLOYEE:
            # Include bookings assigned to this employee
            queryset = queryset | self.queryset.filter(assigned_to=self.request.user)
        
        return queryset.distinct()

    def perform_create(self, serializer):
        with transaction.atomic():
            booking = serializer.save(user=self.request.user)
            # Mark cart as inactive after booking
            booking.cart.status = 'INACTIVE'
            booking.cart.save()
            # Send confirmation
            send_booking_confirmation.delay(booking.id)

    @swagger_auto_schema(
        method='post',
        request_body=BookingStatusUpdateSerializer,
        responses={200: BookingSerializer}
    )
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

    @swagger_auto_schema(
        method='post',
        request_body=BookingRescheduleSerializer,
        responses={200: BookingSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reschedule(self, request, pk=None):
        """Reschedule a booking (Admin-only)"""
        booking = self.get_object()
        
        # Admin-only: permission enforced by decorator
        if not request.user.role == User.Role.ADMIN:
            return Response(
                {'error': 'You do not have permission to reschedule this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookingRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                booking.reschedule(
                    new_date=serializer.validated_data['selected_date'],
                    new_time=serializer.validated_data['selected_time'],
                    rescheduled_by=request.user
                )
                
            return Response({
                'message': 'Booking rescheduled successfully',
                'booking': BookingSerializer(booking).data
            })
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def upload_attachment(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingAttachmentSerializer(
            data=request.data,
            context={'booking': booking}
        )
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(booking=booking)
        
        return Response(
            BookingAttachmentSerializer(attachment).data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        method='get',
        operation_description="Get booking details by booking ID",
        operation_summary="Get Booking by ID",
        tags=['Booking'],
        manual_parameters=[
            openapi.Parameter('book_id', openapi.IN_PATH, description="Booking ID (e.g., BK-072D32E4)", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(
                description="Booking details retrieved successfully",
                schema=BookingSerializer
            ),
            404: openapi.Response(description="Booking not found")
        }
    )
    @action(detail=False, methods=['get'], url_path='by-id/(?P<book_id>[^/.]+)')
    def get_by_book_id(self, request, book_id=None):
        """Get booking details by book_id for confirmation page"""
        try:
            # Get booking by book_id and ensure user owns it
            booking = Booking.objects.select_related(
                'user', 'cart', 'address', 'assigned_to'
            ).prefetch_related(
                'attachments'
            ).get(book_id=book_id, user=request.user)
            
            serializer = self.get_serializer(booking)
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Booking.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Booking not found or you do not have permission to view it'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving booking: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='get',
        operation_description="Get user's latest booking",
        operation_summary="Get Latest Booking",
        tags=['Booking'],
        responses={
            200: openapi.Response(
                description="Latest booking retrieved successfully",
                schema=BookingSerializer
            ),
            404: openapi.Response(description="No bookings found")
        }
    )
    @action(detail=False, methods=['get'], url_path='latest')
    def get_latest(self, request):
        """Get user's latest booking - used as fallback when book_id is missing"""
        try:
            # Get user's latest booking
            booking = Booking.objects.select_related(
                'user', 'cart', 'address', 'assigned_to'
            ).prefetch_related(
                'attachments'
            ).filter(user=request.user).order_by('-created_at').first()
            
            if not booking:
                return Response({
                    'success': False,
                    'message': 'No bookings found for this user'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.get_serializer(booking)
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error retrieving latest booking: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        method='get',
        operation_description="Get booking details by cart ID",
        operation_summary="Get Booking by Cart ID",
        tags=['Booking'],
        manual_parameters=[
            openapi.Parameter('cart_id', openapi.IN_PATH, description="Cart ID (UUID)", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(
                description="Booking details retrieved successfully",
                schema=BookingSerializer
            ),
            404: openapi.Response(description="Booking not found for this cart")
        }
    )
    @action(detail=False, methods=['get'], url_path='by-cart/(?P<cart_id>[^/.]+)')
    def get_by_cart_id(self, request, cart_id=None):
        """Get booking details by cart_id - useful for payment redirect scenarios"""
        try:
            from cart.models import Cart
            from payments.models import PaymentOrder
            from payments.services import WebhookService
            
            # Get cart and ensure user owns it
            cart = Cart.objects.get(cart_id=cart_id, user=request.user)
            
            # Get booking for this cart
            booking = Booking.objects.select_related(
                'user', 'cart', 'address', 'assigned_to'
            ).prefetch_related(
                'attachments'
            ).filter(cart=cart, user=request.user).first()
            
            if not booking:
                # Check if payment was successful but booking creation failed
                payment = PaymentOrder.objects.filter(
                    cart_id=cart_id, 
                    user=request.user,
                    status='SUCCESS'
                ).first()
                
                if payment:
                    # Payment successful but booking missing - try to create it
                    webhook_service = WebhookService()
                    booking = webhook_service._create_booking_from_cart(payment)
                    
                    if booking:
                        logger.info(f"Created missing booking for cart {cart_id}: {booking.book_id}")
                    else:
                        return Response({
                            'success': False,
                            'message': 'Payment successful but booking creation failed. Please contact support.',
                            'payment_status': 'SUCCESS',
                            'cart_id': cart_id
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response({
                        'success': False,
                        'message': 'No booking found for this cart. Payment may still be processing.',
                        'payment_status': payment.status if payment else 'NOT_FOUND',
                        'cart_id': cart_id
                    }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.get_serializer(booking)
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Cart.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Cart not found or you do not have permission to view it'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving booking by cart_id {cart_id}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error retrieving booking: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminBookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related(
        'user', 'cart', 'address', 'assigned_to'
    ).prefetch_related(
        'attachments'
    ).order_by('-created_at')
    
    serializer_class = AdminBookingListSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status', 'user', 'assigned_to']
    search_fields = ['book_id', 'user__email', 'assigned_to__email']
    parser_classes = [MultiPartParser, JSONParser]

    def get_serializer_class(self):
        if self.action in ['update_status', 'partial_update_status']:
            return BookingStatusUpdateSerializer
        if self.action == 'reschedule':
            return BookingRescheduleSerializer
        if self.action == 'assign':
            return BookingAssignmentSerializer
        if self.action in ['retrieve', 'update', 'partial_update']:
            return BookingSerializer
        return AdminBookingListSerializer

    @swagger_auto_schema(
        method='post',
        request_body=BookingStatusUpdateSerializer,
        responses={200: BookingSerializer}
    )
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
        
        return Response(BookingSerializer(booking).data)

    @swagger_auto_schema(
        method='post',
        request_body=BookingRescheduleSerializer,
        responses={200: BookingSerializer}
    )
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Admin reschedule a booking"""
        booking = self.get_object()
        
        serializer = BookingRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                booking.reschedule(
                    new_date=serializer.validated_data['selected_date'],
                    new_time=serializer.validated_data['selected_time'],
                    rescheduled_by=request.user
                )
                
            return Response({
                'message': 'Booking rescheduled successfully',
                'booking': BookingSerializer(booking).data
            })
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        method='post',
        request_body=BookingAssignmentSerializer,
        responses={200: BookingSerializer}
    )
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Admin assign booking to an employee/priest"""
        booking = self.get_object()
        serializer = BookingAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not booking.can_be_assigned():
            return Response(
                {'error': 'This booking cannot be assigned'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from accounts.models import User
            employee = User.objects.get(id=serializer.validated_data['assigned_to_id'])
            
            with transaction.atomic():
                booking.assign_to(employee, request.user)
                
            return Response({
                'message': f'Booking assigned to {employee.email} successfully',
                'booking': BookingSerializer(booking).data
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Employee not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def employees(self, request):
        """Get list of employees that can be assigned to bookings"""
        from accounts.models import User
        employees = User.objects.filter(
            role__in=[User.Role.EMPLOYEE, User.Role.ADMIN],
            account_status=User.AccountStatus.ACTIVE
        ).select_related('profile').values(
            'id', 'email', 'username',
            'profile__first_name', 'profile__last_name'
        )
        
        # Transform the data to have proper field names
        employees_data = []
        for emp in employees:
            employees_data.append({
                'id': emp['id'],
                'email': emp['email'],
                'username': emp['username'],
                'first_name': emp['profile__first_name'] or '',
                'last_name': emp['profile__last_name'] or ''
            })
        
        return Response(employees_data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for admin"""
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        stats = {
            'total_bookings': Booking.objects.count(),
            'pending_bookings': Booking.objects.filter(status=BookingStatus.PENDING).count(),
            'confirmed_bookings': Booking.objects.filter(status=BookingStatus.CONFIRMED).count(),
            'completed_bookings': Booking.objects.filter(status=BookingStatus.COMPLETED).count(),
            'cancelled_bookings': Booking.objects.filter(status=BookingStatus.CANCELLED).count(),
            'this_week_bookings': Booking.objects.filter(created_at__date__gte=week_ago).count(),
            'today_bookings': Booking.objects.filter(selected_date=today).count(),
            'unassigned_bookings': Booking.objects.filter(assigned_to__isnull=True).count(),
        }
        
        return Response(stats)