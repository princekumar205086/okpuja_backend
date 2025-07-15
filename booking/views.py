from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Booking, BookingAttachment
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
    parser_classes = [MultiPartParser]

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
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reschedule(self, request, pk=None):
        """Reschedule a booking (available to assigned employee or admin)"""
        booking = self.get_object()
        
        # Check permissions: user can reschedule their own booking, or employee can reschedule assigned booking
        if not (booking.user == request.user or 
                booking.assigned_to == request.user or 
                request.user.role == User.Role.ADMIN):
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
    parser_classes = [MultiPartParser]

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
        ).values('id', 'email', 'username', 'first_name', 'last_name')
        
        return Response(list(employees))

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