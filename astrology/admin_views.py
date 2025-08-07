"""
Enterprise-level admin views for Astrology system
Comprehensive admin endpoints with notification management
"""
import logging
from datetime import datetime, date, timedelta
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import AstrologyService, AstrologyBooking
from .serializers import AstrologyServiceSerializer
from .admin_serializers import (
    AdminAstrologyServiceSerializer,
    AdminAstrologyBookingSerializer,
    AdminBookingUpdateSerializer,
    AdminSessionScheduleSerializer,
    AdminBulkActionSerializer,
    AdminDashboardSerializer
)
from core.permissions import IsAdminUser, IsStaffUser
# Import tasks if available
try:
    from .tasks import (
        send_astrology_booking_confirmation, 
        send_astrology_session_reminder,
        send_astrology_booking_reschedule,
        send_astrology_booking_status_update,
        send_custom_astrology_notification
    )
except ImportError:
    # Graceful fallback if celery is not configured
    send_astrology_booking_confirmation = None
    send_astrology_session_reminder = None
    send_astrology_booking_reschedule = None
    send_astrology_booking_status_update = None
    send_custom_astrology_notification = None

logger = logging.getLogger(__name__)


class AdminAstrologyDashboardView(APIView):
    """
    Enterprise Dashboard for Astrology Admin
    Provides comprehensive analytics and overview
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get comprehensive astrology dashboard data",
        operation_summary="Admin Dashboard Analytics",
        tags=['Admin', 'Analytics'],
        responses={
            200: openapi.Response(
                description="Dashboard data retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "overview": {
                                "total_bookings": 150,
                                "confirmed_bookings": 120,
                                "completed_bookings": 80,
                                "cancelled_bookings": 10,
                                "total_revenue": "299800.00",
                                "average_session_duration": 45,
                                "customer_satisfaction": 4.2
                            },
                            "recent_bookings": [],
                            "pending_sessions": [],
                            "revenue_analytics": {},
                            "service_performance": []
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        try:
            # Date range for analytics (default: last 30 days)
            days = int(request.GET.get('days', 30))
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Basic metrics
            total_bookings = AstrologyBooking.objects.count()
            confirmed_bookings = AstrologyBooking.objects.filter(status='CONFIRMED').count()
            completed_bookings = AstrologyBooking.objects.filter(status='COMPLETED').count()
            cancelled_bookings = AstrologyBooking.objects.filter(status='CANCELLED').count()
            
            # Revenue analytics
            revenue_data = AstrologyBooking.objects.filter(
                created_at__date__range=[start_date, end_date],
                status__in=['CONFIRMED', 'COMPLETED']
            ).aggregate(
                total_revenue=Sum('service__price'),
                avg_booking_value=Avg('service__price'),
                booking_count=Count('id')
            )
            
            # Service performance
            service_stats = AstrologyService.objects.annotate(
                booking_count=Count('astrologybooking'),
                total_revenue=Sum('astrologybooking__service__price')
            ).order_by('-booking_count')[:5]
            
            # Recent bookings (last 10)
            recent_bookings = AstrologyBooking.objects.select_related('service', 'user').order_by('-created_at')[:10]
            
            # Pending sessions (needs Google Meet link)
            pending_sessions = AstrologyBooking.objects.filter(
                status='CONFIRMED',
                google_meet_link__isnull=True,
                preferred_date__gte=timezone.now().date()
            ).select_related('service', 'user').order_by('preferred_date', 'preferred_time')[:10]
            
            # Upcoming sessions (next 7 days)
            upcoming_sessions = AstrologyBooking.objects.filter(
                status='CONFIRMED',
                preferred_date__range=[timezone.now().date(), timezone.now().date() + timedelta(days=7)]
            ).select_related('service', 'user').order_by('preferred_date', 'preferred_time')
            
            dashboard_data = {
                "overview": {
                    "total_bookings": total_bookings,
                    "confirmed_bookings": confirmed_bookings,
                    "completed_bookings": completed_bookings,
                    "cancelled_bookings": cancelled_bookings,
                    "pending_sessions": pending_sessions.count(),
                    "total_revenue": str(revenue_data.get('total_revenue') or 0),
                    "average_booking_value": str(revenue_data.get('avg_booking_value') or 0),
                    "bookings_this_period": revenue_data.get('booking_count', 0),
                    "active_services": AstrologyService.objects.filter(is_active=True).count()
                },
                "recent_bookings": AdminAstrologyBookingSerializer(recent_bookings, many=True).data,
                "pending_sessions": AdminAstrologyBookingSerializer(pending_sessions, many=True).data,
                "upcoming_sessions": AdminAstrologyBookingSerializer(upcoming_sessions, many=True).data,
                "service_performance": [
                    {
                        "id": service.id,
                        "title": service.title,
                        "service_type": service.get_service_type_display(),
                        "booking_count": service.booking_count or 0,
                        "total_revenue": str(service.total_revenue or 0),
                        "price": str(service.price)
                    } for service in service_stats
                ]
            }
            
            return Response({
                "success": True,
                "data": dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Admin dashboard error: {str(e)}")
            return Response({
                "success": False,
                "error": "Failed to load dashboard data"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAstrologyBookingManagementView(generics.ListAPIView):
    """
    Advanced booking management for admins
    Supports filtering, search, and bulk operations
    """
    serializer_class = AdminAstrologyBookingSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'service', 'preferred_date', 'is_session_scheduled']
    search_fields = ['astro_book_id', 'contact_email', 'contact_phone', 'birth_place']
    ordering_fields = ['created_at', 'preferred_date', 'preferred_time']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = AstrologyBooking.objects.select_related('service', 'user').all()
        
        # Additional filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            queryset = queryset.filter(preferred_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(preferred_date__lte=date_to)
            
        return queryset
    
    @swagger_auto_schema(
        operation_description="Get all astrology bookings with advanced filtering",
        operation_summary="Admin Booking Management",
        tags=['Admin', 'Bookings'],
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('service', openapi.IN_QUERY, description="Filter by service ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Filter from date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="Filter to date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('is_session_scheduled', openapi.IN_QUERY, description="Filter by session status", type=openapi.TYPE_BOOLEAN),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminAstrologerManagementView(generics.RetrieveUpdateAPIView):
    """
    Detailed booking view and update for admins
    Includes session scheduling and status management
    """
    queryset = AstrologyBooking.objects.select_related('service', 'user').all()
    serializer_class = AdminBookingUpdateSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'astro_book_id'
    
    def perform_update(self, serializer):
        """Handle booking updates with notifications"""
        booking = self.get_object()
        old_status = booking.status
        old_google_meet = booking.google_meet_link
        old_date = booking.preferred_date
        old_time = booking.preferred_time
        
        # Save the booking
        updated_booking = serializer.save()
        
        # Send notifications based on changes
        try:
            # Status change notification
            if old_status != updated_booking.status:
                self._send_status_change_notification(updated_booking, old_status)
            
            # Google Meet link added/updated notification
            if old_google_meet != updated_booking.google_meet_link and updated_booking.google_meet_link:
                self._send_session_link_notification(updated_booking)
            
            # Schedule change notification
            if old_date != updated_booking.preferred_date or old_time != updated_booking.preferred_time:
                self._send_reschedule_notification(updated_booking, old_date, old_time)
                
        except Exception as e:
            logger.error(f"Failed to send booking update notifications: {str(e)}")
    
    def _send_status_change_notification(self, booking, old_status):
        """Send notification when booking status changes"""
        try:
            subject = f"Booking Status Updated - {booking.astro_book_id}"
            
            # Email to customer
            html_message = render_to_string('emails/astrology/booking_status_update.html', {
                'booking': booking,
                'old_status': old_status,
                'new_status': booking.status
            })
            
            send_mail(
                subject,
                f"Your booking {booking.astro_book_id} status has been updated to {booking.get_status_display()}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
            
            logger.info(f"Status change notification sent for booking {booking.astro_book_id}")
            
        except Exception as e:
            logger.error(f"Failed to send status change notification: {str(e)}")
    
    def _send_session_link_notification(self, booking):
        """Send Google Meet link to customer"""
        try:
            booking.send_session_link_notification()
            booking.is_session_scheduled = True
            booking.save(update_fields=['is_session_scheduled'])
            
        except Exception as e:
            logger.error(f"Failed to send session link notification: {str(e)}")
    
    def _send_reschedule_notification(self, booking, old_date, old_time):
        """Send reschedule notification to customer"""
        try:
            subject = f"Session Rescheduled - {booking.astro_book_id}"
            
            html_message = render_to_string('emails/astrology/booking_rescheduled.html', {
                'booking': booking,
                'old_date': old_date,
                'old_time': old_time
            })
            
            send_mail(
                subject,
                f"Your astrology session has been rescheduled from {old_date} {old_time} to {booking.preferred_date} {booking.preferred_time}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
            
            logger.info(f"Reschedule notification sent for booking {booking.astro_book_id}")
            
        except Exception as e:
            logger.error(f"Failed to send reschedule notification: {str(e)}")


class AdminAstrologyBulkActionsView(APIView):
    """
    Bulk operations for booking management
    Supports bulk status updates, session scheduling, etc.
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Perform bulk actions on multiple bookings",
        operation_summary="Bulk Booking Actions",
        tags=['Admin', 'Bulk Operations'],
        request_body=AdminBulkActionSerializer,
        responses={
            200: openapi.Response(
                description="Bulk action completed successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Bulk action completed",
                        "processed": 10,
                        "failed": 0,
                        "details": []
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = AdminBulkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        booking_ids = serializer.validated_data['booking_ids']
        action = serializer.validated_data['action']
        params = serializer.validated_data.get('params', {})
        
        try:
            with transaction.atomic():
                bookings = AstrologyBooking.objects.filter(id__in=booking_ids)
                processed = 0
                failed = 0
                details = []
                
                for booking in bookings:
                    try:
                        if action == 'update_status':
                            old_status = booking.status
                            booking.status = params.get('status')
                            booking.save()
                            self._send_bulk_status_notification(booking, old_status)
                            
                        elif action == 'schedule_sessions':
                            if 'google_meet_link' in params:
                                booking.google_meet_link = params['google_meet_link']
                                booking.is_session_scheduled = True
                                booking.save()
                                booking.send_session_link_notification()
                                
                        elif action == 'send_reminders':
                            self._send_session_reminder(booking)
                            
                        elif action == 'mark_completed':
                            booking.status = 'COMPLETED'
                            booking.save()
                            self._send_completion_notification(booking)
                        
                        processed += 1
                        details.append({
                            "booking_id": booking.astro_book_id,
                            "status": "success",
                            "message": f"Action '{action}' completed successfully"
                        })
                        
                    except Exception as e:
                        failed += 1
                        details.append({
                            "booking_id": booking.astro_book_id,
                            "status": "failed",
                            "message": str(e)
                        })
                        logger.error(f"Bulk action failed for booking {booking.astro_book_id}: {str(e)}")
                
                return Response({
                    "success": True,
                    "message": f"Bulk action '{action}' completed",
                    "processed": processed,
                    "failed": failed,
                    "details": details
                })
                
        except Exception as e:
            logger.error(f"Bulk action failed: {str(e)}")
            return Response({
                "success": False,
                "error": "Bulk action failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_bulk_status_notification(self, booking, old_status):
        """Send notification for bulk status changes"""
        try:
            if old_status != booking.status:
                subject = f"Booking Status Updated - {booking.astro_book_id}"
                
                html_message = render_to_string('emails/astrology_booking_status_update.html', {
                    'booking': booking,
                    'old_status': old_status,
                    'new_status': booking.status
                })
                
                send_mail(
                    subject,
                    f"Your booking status has been updated to {booking.get_status_display()}",
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.contact_email],
                    html_message=html_message
                )
        except Exception as e:
            logger.error(f"Failed to send bulk status notification: {str(e)}")
    
    def _send_session_reminder(self, booking):
        """Send session reminder to customer"""
        try:
            subject = f"Session Reminder - {booking.astro_book_id}"
            
            html_message = render_to_string('emails/astrology/session_reminder.html', {
                'booking': booking
            })
            
            send_mail(
                subject,
                f"Reminder: Your astrology session is scheduled for {booking.preferred_date} at {booking.preferred_time}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send session reminder: {str(e)}")
    
    def _send_completion_notification(self, booking):
        """Send completion notification to customer"""
        try:
            subject = f"Session Completed - {booking.astro_book_id}"
            
            html_message = render_to_string('emails/astrology/session_completed.html', {
                'booking': booking
            })
            
            send_mail(
                subject,
                f"Your astrology session has been completed. Thank you for choosing our services!",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send completion notification: {str(e)}")


class AdminServiceManagementView(generics.ListCreateAPIView):
    """
    Advanced service management for admins
    """
    queryset = AstrologyService.objects.all()
    serializer_class = AstrologyServiceSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['service_type', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price', 'created_at']
    ordering = ['title']


class AdminAstrologyReportsView(APIView):
    """
    Comprehensive reporting system for admin
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Generate comprehensive reports",
        operation_summary="Admin Reports",
        tags=['Admin', 'Reports'],
        manual_parameters=[
            openapi.Parameter('report_type', openapi.IN_QUERY, description="Type of report", type=openapi.TYPE_STRING),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request):
        report_type = request.GET.get('report_type', 'summary')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        try:
            if report_type == 'revenue':
                report_data = self._generate_revenue_report(start_date, end_date)
            elif report_type == 'bookings':
                report_data = self._generate_booking_report(start_date, end_date)
            elif report_type == 'services':
                report_data = self._generate_service_report(start_date, end_date)
            else:
                report_data = self._generate_summary_report(start_date, end_date)
            
            return Response({
                "success": True,
                "report_type": report_type,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "data": report_data
            })
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return Response({
                "success": False,
                "error": "Failed to generate report"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_revenue_report(self, start_date, end_date):
        """Generate detailed revenue report"""
        bookings = AstrologyBooking.objects.filter(
            created_at__date__range=[start_date, end_date],
            status__in=['CONFIRMED', 'COMPLETED']
        ).select_related('service')
        
        total_revenue = sum(booking.service.price for booking in bookings)
        
        # Revenue by service type
        service_revenue = {}
        for booking in bookings:
            service_type = booking.service.get_service_type_display()
            if service_type not in service_revenue:
                service_revenue[service_type] = {
                    'count': 0,
                    'revenue': 0
                }
            service_revenue[service_type]['count'] += 1
            service_revenue[service_type]['revenue'] += float(booking.service.price)
        
        return {
            "total_revenue": float(total_revenue),
            "total_bookings": bookings.count(),
            "average_booking_value": float(total_revenue / bookings.count()) if bookings.count() > 0 else 0,
            "service_breakdown": service_revenue
        }
    
    def _generate_booking_report(self, start_date, end_date):
        """Generate detailed booking report"""
        bookings = AstrologyBooking.objects.filter(
            created_at__date__range=[start_date, end_date]
        )
        
        status_breakdown = {}
        for status_choice in AstrologyBooking.STATUS_CHOICES:
            status = status_choice[0]
            count = bookings.filter(status=status).count()
            status_breakdown[status] = {
                'count': count,
                'display_name': status_choice[1]
            }
        
        return {
            "total_bookings": bookings.count(),
            "status_breakdown": status_breakdown,
            "sessions_scheduled": bookings.filter(google_meet_link__isnull=False).count(),
            "pending_sessions": bookings.filter(
                status='CONFIRMED',
                google_meet_link__isnull=True
            ).count()
        }
    
    def _generate_service_report(self, start_date, end_date):
        """Generate service performance report"""
        services = AstrologyService.objects.annotate(
            booking_count=Count('astrologybooking', 
                filter=Q(astrologybooking__created_at__date__range=[start_date, end_date])
            ),
            total_revenue=Sum('astrologybooking__service__price',
                filter=Q(astrologybooking__created_at__date__range=[start_date, end_date])
            )
        )
        
        service_data = []
        for service in services:
            service_data.append({
                "id": service.id,
                "title": service.title,
                "service_type": service.get_service_type_display(),
                "price": float(service.price),
                "booking_count": service.booking_count or 0,
                "total_revenue": float(service.total_revenue or 0),
                "is_active": service.is_active
            })
        
        return {
            "services": service_data,
            "top_performing": sorted(service_data, key=lambda x: x['booking_count'], reverse=True)[:5]
        }
    
    def _generate_summary_report(self, start_date, end_date):
        """Generate comprehensive summary report"""
        revenue_data = self._generate_revenue_report(start_date, end_date)
        booking_data = self._generate_booking_report(start_date, end_date)
        service_data = self._generate_service_report(start_date, end_date)
        
        return {
            "revenue": revenue_data,
            "bookings": booking_data,
            "services": {
                "total_active_services": len([s for s in service_data['services'] if s['is_active']]),
                "top_services": service_data['top_performing'][:3]
            }
        }


@api_view(['POST'])
@permission_classes([IsAdminUser])
@swagger_auto_schema(
    operation_description="Send manual notification to customer",
    operation_summary="Send Manual Notification",
    tags=['Admin', 'Notifications'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'booking_id': openapi.Schema(type=openapi.TYPE_STRING),
            'message_type': openapi.Schema(type=openapi.TYPE_STRING),
            'custom_message': openapi.Schema(type=openapi.TYPE_STRING),
            'include_booking_details': openapi.Schema(type=openapi.TYPE_BOOLEAN)
        },
        required=['booking_id', 'message_type']
    )
)
def send_manual_astrology_notification(request):
    """Send manual notification to customer"""
    try:
        booking_id = request.data.get('booking_id')
        message_type = request.data.get('message_type')
        custom_message = request.data.get('custom_message', '')
        include_details = request.data.get('include_booking_details', True)
        
        booking = AstrologyBooking.objects.get(astro_book_id=booking_id)
        
        subject_map = {
            'reminder': f"Session Reminder - {booking.astro_book_id}",
            'update': f"Booking Update - {booking.astro_book_id}",
            'custom': f"Message from OkPuja - {booking.astro_book_id}",
            'follow_up': f"Follow-up - {booking.astro_book_id}"
        }
        
        subject = subject_map.get(message_type, f"Notification - {booking.astro_book_id}")
        
        context = {
            'booking': booking,
            'custom_message': custom_message,
            'include_details': include_details,
            'message_type': message_type
        }
        
        html_message = render_to_string('emails/astrology/manual_notification.html', context)
        
        send_mail(
            subject,
            custom_message or f"You have a notification regarding your booking {booking.astro_book_id}",
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message
        )
        
        return Response({
            "success": True,
            "message": f"Notification sent to {booking.contact_email}"
        })
        
    except AstrologyBooking.DoesNotExist:
        return Response({
            "success": False,
            "error": "Booking not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Manual notification failed: {str(e)}")
        return Response({
            "success": False,
            "error": "Failed to send notification"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
