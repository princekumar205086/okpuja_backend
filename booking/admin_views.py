"""
Enterprise-level admin views for Booking system
Comprehensive booking management with advanced features
"""
import logging
from datetime import datetime, date, timedelta
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, F
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

from booking.models import Booking, BookingAttachment, BookingStatus
from cart.models import Cart
from .booking_admin_serializers import (
    AdminBookingSerializer,
    AdminBookingDetailSerializer,
    AdminBookingUpdateSerializer,
    AdminBookingBulkActionSerializer,
    AdminBookingDashboardSerializer,
    AdminBookingReportSerializer,
    AdminBookingAssignmentSerializer
)
from core.permissions import IsAdminUser, IsStaffUser

logger = logging.getLogger(__name__)


class AdminBookingDashboardView(APIView):
    """
    Enterprise Dashboard for Booking Admin
    Provides comprehensive booking analytics and overview
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get comprehensive booking dashboard data",
        operation_summary="Admin Booking Dashboard Analytics",
        tags=['Admin', 'Booking', 'Analytics'],
        responses={
            200: openapi.Response(
                description="Dashboard data retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "overview": {
                                "total_bookings": 1250,
                                "confirmed_bookings": 980,
                                "completed_bookings": 850,
                                "cancelled_bookings": 75,
                                "pending_bookings": 195,
                                "total_revenue": "2750000.00",
                                "average_booking_value": "2200.00",
                                "active_employees": 25
                            },
                            "recent_bookings": [],
                            "upcoming_bookings": [],
                            "revenue_analytics": {},
                            "booking_trends": []
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        try:
            # Date range for analytics
            days = int(request.GET.get('days', 30))
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Basic metrics
            total_bookings = Booking.objects.count()
            confirmed_bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED).count()
            completed_bookings = Booking.objects.filter(status=BookingStatus.COMPLETED).count()
            cancelled_bookings = Booking.objects.filter(status=BookingStatus.CANCELLED).count()
            pending_bookings = Booking.objects.filter(status=BookingStatus.PENDING).count()
            rejected_bookings = Booking.objects.filter(status=BookingStatus.REJECTED).count()
            failed_bookings = Booking.objects.filter(status=BookingStatus.FAILED).count()
            
            # Revenue analytics (based on total_amount property)
            period_bookings = Booking.objects.filter(
                created_at__date__range=[start_date, end_date],
                status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
            ).select_related('cart', 'user')
            
            # Calculate revenue from bookings
            total_revenue = sum(booking.total_amount for booking in period_bookings)
            avg_booking_value = total_revenue / period_bookings.count() if period_bookings.count() > 0 else 0
            
            # Employee/assignment stats
            assigned_bookings = Booking.objects.filter(assigned_to__isnull=False).count()
            unassigned_bookings = Booking.objects.filter(
                assigned_to__isnull=True,
                status__in=[BookingStatus.CONFIRMED, BookingStatus.PENDING]
            ).count()
            
            # Recent bookings
            recent_bookings = Booking.objects.select_related(
                'user', 'cart', 'assigned_to', 'address'
            ).order_by('-created_at')[:15]
            
            # Upcoming bookings (next 7 days)
            upcoming_bookings = Booking.objects.filter(
                status=BookingStatus.CONFIRMED,
                selected_date__range=[timezone.now().date(), timezone.now().date() + timedelta(days=7)]
            ).select_related('user', 'cart', 'assigned_to', 'address').order_by('selected_date', 'selected_time')
            
            # Today's bookings
            today_bookings = Booking.objects.filter(
                selected_date=timezone.now().date(),
                status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
            ).count()
            
            # Overdue bookings (past date, still pending/confirmed)
            overdue_bookings = Booking.objects.filter(
                selected_date__lt=timezone.now().date(),
                status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
            ).count()
            
            # Employee performance
            from django.contrib.auth import get_user_model
            User = get_user_model()
            active_employees = User.objects.filter(
                is_staff=True,
                assigned_bookings__isnull=False
            ).distinct().count()
            
            # Monthly trends (last 6 months)
            monthly_trends = []
            for i in range(6):
                month_date = end_date.replace(day=1) - timedelta(days=32*i)
                month_bookings = Booking.objects.filter(
                    created_at__year=month_date.year,
                    created_at__month=month_date.month
                )
                month_revenue = sum(booking.total_amount for booking in month_bookings)
                monthly_trends.append({
                    'month': month_date.strftime('%Y-%m'),
                    'month_name': month_date.strftime('%B %Y'),
                    'bookings': month_bookings.count(),
                    'revenue': float(month_revenue),
                    'confirmed': month_bookings.filter(status=BookingStatus.CONFIRMED).count(),
                    'completed': month_bookings.filter(status=BookingStatus.COMPLETED).count()
                })
            
            monthly_trends.reverse()  # Show oldest to newest
            
            dashboard_data = {
                "overview": {
                    "total_bookings": total_bookings,
                    "confirmed_bookings": confirmed_bookings,
                    "completed_bookings": completed_bookings,
                    "cancelled_bookings": cancelled_bookings,
                    "pending_bookings": pending_bookings,
                    "rejected_bookings": rejected_bookings,
                    "failed_bookings": failed_bookings,
                    "total_revenue": str(total_revenue),
                    "average_booking_value": str(avg_booking_value),
                    "bookings_this_period": period_bookings.count(),
                    "assigned_bookings": assigned_bookings,
                    "unassigned_bookings": unassigned_bookings,
                    "active_employees": active_employees,
                    "today_bookings": today_bookings,
                    "overdue_bookings": overdue_bookings
                },
                "recent_bookings": AdminBookingSerializer(recent_bookings, many=True).data,
                "upcoming_bookings": AdminBookingSerializer(upcoming_bookings, many=True).data,
                "status_distribution": {
                    "confirmed": confirmed_bookings,
                    "completed": completed_bookings,
                    "cancelled": cancelled_bookings,
                    "pending": pending_bookings,
                    "rejected": rejected_bookings,
                    "failed": failed_bookings
                },
                "monthly_trends": monthly_trends,
                "assignment_stats": {
                    "assigned": assigned_bookings,
                    "unassigned": unassigned_bookings,
                    "assignment_rate": round((assigned_bookings / total_bookings * 100), 2) if total_bookings > 0 else 0
                }
            }
            
            return Response({
                "success": True,
                "data": dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Booking admin dashboard error: {str(e)}")
            return Response({
                "success": False,
                "error": "Failed to load dashboard data"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminBookingManagementView(generics.ListAPIView):
    """
    Advanced booking management for admins
    Supports comprehensive filtering, search, and analytics
    """
    serializer_class = AdminBookingSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'assigned_to', 'selected_date']
    search_fields = ['book_id', 'user__email', 'user__first_name', 'user__last_name', 'address__full_address']
    ordering_fields = ['created_at', 'selected_date', 'selected_time', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Booking.objects.select_related(
            'user', 'cart', 'assigned_to', 'address'
        ).all()
        
        # Additional filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        created_from = self.request.GET.get('created_from')
        created_to = self.request.GET.get('created_to')
        has_assignment = self.request.GET.get('has_assignment')
        is_overdue = self.request.GET.get('is_overdue')
        amount_min = self.request.GET.get('amount_min')
        amount_max = self.request.GET.get('amount_max')
        
        if date_from:
            queryset = queryset.filter(selected_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(selected_date__lte=date_to)
        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)
        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)
        if has_assignment is not None:
            if has_assignment.lower() == 'true':
                queryset = queryset.filter(assigned_to__isnull=False)
            else:
                queryset = queryset.filter(assigned_to__isnull=True)
        if is_overdue and is_overdue.lower() == 'true':
            queryset = queryset.filter(
                selected_date__lt=timezone.now().date(),
                status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
            )
            
        return queryset
    
    @swagger_auto_schema(
        operation_description="Get all bookings with advanced filtering and search",
        operation_summary="Admin Booking Management",
        tags=['Admin', 'Booking', 'Management'],
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Filter from service date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="Filter to service date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_from', openapi.IN_QUERY, description="Filter from creation date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_to', openapi.IN_QUERY, description="Filter to creation date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('has_assignment', openapi.IN_QUERY, description="Filter by assignment status (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_overdue', openapi.IN_QUERY, description="Filter overdue bookings (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('assigned_to', openapi.IN_QUERY, description="Filter by assigned employee ID", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminBookingDetailView(generics.RetrieveUpdateAPIView):
    """
    Detailed booking view and update for admins
    Includes comprehensive booking information and update capabilities
    """
    queryset = Booking.objects.select_related('user', 'cart', 'assigned_to', 'address').all()
    serializer_class = AdminBookingDetailSerializer
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminBookingUpdateSerializer
        return AdminBookingDetailSerializer
    
    def perform_update(self, serializer):
        """Handle booking updates with notifications and tracking"""
        booking = self.get_object()
        old_status = booking.status
        old_date = booking.selected_date
        old_time = booking.selected_time
        old_assigned = booking.assigned_to
        
        # Save the booking
        updated_booking = serializer.save(updated_by=self.request.user)
        
        # Send notifications based on changes
        try:
            # Status change notification
            if old_status != updated_booking.status:
                self._send_status_change_notification(updated_booking, old_status)
            
            # Schedule change notification
            if (old_date != updated_booking.selected_date or 
                old_time != updated_booking.selected_time):
                self._send_reschedule_notification(updated_booking, old_date, old_time)
            
            # Assignment change notification
            if old_assigned != updated_booking.assigned_to:
                self._send_assignment_notification(updated_booking, old_assigned)
                
        except Exception as e:
            logger.error(f"Failed to send booking update notifications: {str(e)}")
    
    def _send_status_change_notification(self, booking, old_status):
        """Send notification when booking status changes"""
        try:
            subject = f"Booking Status Updated - #{booking.book_id}"
            
            html_message = render_to_string('emails/booking/status_update.html', {
                'booking': booking,
                'old_status': old_status,
                'new_status': booking.status,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your booking status has been updated to {booking.get_status_display()}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                html_message=html_message
            )
            
            # Send admin notification
            self._send_admin_notification(booking, 'status_updated', {
                'old_status': old_status,
                'new_status': booking.status
            })
            
            logger.info(f"Status change notification sent for booking {booking.book_id}")
            
        except Exception as e:
            logger.error(f"Failed to send booking status change notification: {str(e)}")
    
    def _send_reschedule_notification(self, booking, old_date, old_time):
        """Send reschedule notification to customer"""
        try:
            subject = f"Service Rescheduled - Booking #{booking.book_id}"
            
            html_message = render_to_string('emails/booking/rescheduled.html', {
                'booking': booking,
                'old_date': old_date,
                'old_time': old_time,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your service has been rescheduled to {booking.selected_date} at {booking.selected_time}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                html_message=html_message
            )
            
            logger.info(f"Reschedule notification sent for booking {booking.book_id}")
            
        except Exception as e:
            logger.error(f"Failed to send booking reschedule notification: {str(e)}")
    
    def _send_assignment_notification(self, booking, old_assigned):
        """Send assignment notification"""
        try:
            # Notify new assignee
            if booking.assigned_to:
                subject = f"New Booking Assignment - #{booking.book_id}"
                
                html_message = render_to_string('emails/booking/assignment.html', {
                    'booking': booking,
                    'assignee': booking.assigned_to,
                    'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
                })
                
                send_mail(
                    subject,
                    f"You have been assigned to booking #{booking.book_id}",
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.assigned_to.email],
                    html_message=html_message
                )
            
            # Notify customer about assignment
            customer_subject = f"Service Team Assigned - Booking #{booking.book_id}"
            customer_html = render_to_string('emails/booking/customer_assignment.html', {
                'booking': booking,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                customer_subject,
                f"A service team member has been assigned to your booking #{booking.book_id}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                html_message=customer_html
            )
            
            logger.info(f"Assignment notification sent for booking {booking.book_id}")
            
        except Exception as e:
            logger.error(f"Failed to send booking assignment notification: {str(e)}")
    
    def _send_admin_notification(self, booking, notification_type, context=None):
        """Send notification to admin team"""
        try:
            admin_emails = getattr(settings, 'BOOKING_ADMIN_EMAILS', ['admin@okpuja.com'])
            
            subject_map = {
                'status_updated': f"Booking Status Updated - #{booking.book_id}",
                'booking_created': f"New Booking - #{booking.book_id}",
                'booking_cancelled': f"Booking Cancelled - #{booking.book_id}",
                'assignment_changed': f"Booking Assignment Changed - #{booking.book_id}"
            }
            
            subject = subject_map.get(notification_type, f"Booking Notification - #{booking.book_id}")
            
            html_message = render_to_string('emails/booking/admin_notification.html', {
                'booking': booking,
                'notification_type': notification_type,
                'context': context or {},
                'admin_panel_url': getattr(settings, 'ADMIN_PANEL_URL', 'https://admin.okpuja.com')
            })
            
            for admin_email in admin_emails:
                send_mail(
                    subject,
                    f"Booking notification: {notification_type} for booking #{booking.book_id}",
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                    html_message=html_message,
                    fail_silently=True
                )
            
            logger.info(f"Admin notification sent for booking {booking.book_id} - {notification_type}")
            
        except Exception as e:
            logger.error(f"Failed to send booking admin notification: {str(e)}")


class AdminBookingBulkActionsView(APIView):
    """
    Bulk operations for booking management
    Supports multiple actions on selected bookings
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Perform bulk actions on bookings",
        operation_summary="Bulk Booking Actions",
        tags=['Admin', 'Booking', 'Bulk Operations'],
        request_body=AdminBookingBulkActionSerializer,
        responses={
            200: openapi.Response(
                description="Bulk action completed successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Bulk action completed",
                        "processed": 25,
                        "failed": 0,
                        "details": []
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = AdminBookingBulkActionSerializer(data=request.data)
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
                bookings = Booking.objects.filter(id__in=booking_ids).select_related(
                    'user', 'cart', 'assigned_to'
                )
                processed = 0
                failed = 0
                details = []
                
                for booking in bookings:
                    try:
                        old_status = booking.status
                        old_assigned = booking.assigned_to
                        
                        if action == 'confirm_bookings':
                            booking.status = BookingStatus.CONFIRMED
                            booking.save()
                            self._send_bulk_confirmation(booking)
                            
                        elif action == 'cancel_bookings':
                            booking.status = BookingStatus.CANCELLED
                            booking.cancellation_reason = params.get('reason', 'Cancelled by admin')
                            booking.save()
                            self._send_bulk_cancellation(booking, params.get('reason'))
                            
                        elif action == 'complete_bookings':
                            booking.status = BookingStatus.COMPLETED
                            booking.save()
                            self._send_bulk_completion(booking)
                            
                        elif action == 'assign_bookings':
                            from django.contrib.auth import get_user_model
                            User = get_user_model()
                            employee_id = params.get('employee_id')
                            if employee_id:
                                employee = User.objects.get(id=employee_id)
                                booking.assigned_to = employee
                                booking.save()
                                self._send_assignment_notification(booking, old_assigned)
                            
                        elif action == 'send_reminders':
                            self._send_booking_reminder(booking)
                            
                        elif action == 'update_status':
                            new_status = params.get('status')
                            if new_status and new_status != old_status:
                                booking.status = new_status
                                if new_status == BookingStatus.CANCELLED:
                                    booking.cancellation_reason = params.get('reason', 'Updated by admin')
                                booking.save()
                                self._send_status_update_notification(booking, old_status, new_status)
                        
                        processed += 1
                        details.append({
                            "booking_id": booking.book_id,
                            "status": "success",
                            "message": f"Action '{action}' completed successfully"
                        })
                        
                    except Exception as e:
                        failed += 1
                        details.append({
                            "booking_id": booking.book_id if hasattr(booking, 'book_id') else f"ID-{booking.id}",
                            "status": "failed",
                            "message": str(e)
                        })
                        logger.error(f"Bulk action failed for booking {booking.id}: {str(e)}")
                
                return Response({
                    "success": True,
                    "message": f"Bulk action '{action}' completed",
                    "processed": processed,
                    "failed": failed,
                    "details": details
                })
                
        except Exception as e:
            logger.error(f"Booking bulk action failed: {str(e)}")
            return Response({
                "success": False,
                "error": "Bulk action failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_bulk_confirmation(self, booking):
        """Send confirmation email for bulk operations"""
        try:
            subject = f"Booking Confirmed - #{booking.book_id}"
            
            html_message = render_to_string('emails/booking/confirmed.html', {
                'booking': booking,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your booking has been confirmed for {booking.selected_date} at {booking.selected_time}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send bulk confirmation: {str(e)}")
    
    def _send_bulk_cancellation(self, booking, reason):
        """Send cancellation email for bulk operations"""
        try:
            subject = f"Booking Cancelled - #{booking.book_id}"
            
            html_message = render_to_string('emails/booking/cancelled.html', {
                'booking': booking,
                'cancellation_reason': reason,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your booking has been cancelled. Reason: {reason}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send bulk cancellation: {str(e)}")
    
    def _send_bulk_completion(self, booking):
        """Send completion email for bulk operations"""
        try:
            subject = f"Service Completed - Thank You! - #{booking.book_id}"
            
            html_message = render_to_string('emails/booking/completed.html', {
                'booking': booking,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your service has been completed. Thank you for choosing our services!",
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send bulk completion: {str(e)}")


class AdminBookingReportsView(APIView):
    """
    Comprehensive booking reporting system
    Generate detailed reports and analytics
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Generate comprehensive booking reports",
        operation_summary="Admin Booking Reports",
        tags=['Admin', 'Booking', 'Reports'],
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
            elif report_type == 'performance':
                report_data = self._generate_performance_report(start_date, end_date)
            elif report_type == 'assignments':
                report_data = self._generate_assignment_report(start_date, end_date)
            elif report_type == 'status':
                report_data = self._generate_status_report(start_date, end_date)
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
            logger.error(f"Booking report generation failed: {str(e)}")
            return Response({
                "success": False,
                "error": "Failed to generate report"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_revenue_report(self, start_date, end_date):
        """Generate detailed revenue report"""
        bookings = Booking.objects.filter(
            created_at__date__range=[start_date, end_date],
            status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
        ).select_related('user', 'cart')
        
        total_revenue = sum(booking.total_amount for booking in bookings)
        
        # Daily revenue breakdown
        daily_revenue = {}
        current_date = start_date
        while current_date <= end_date:
            day_bookings = bookings.filter(created_at__date=current_date)
            daily_revenue[current_date.isoformat()] = {
                'revenue': float(sum(booking.total_amount for booking in day_bookings)),
                'bookings': day_bookings.count()
            }
            current_date += timedelta(days=1)
        
        return {
            "total_revenue": float(total_revenue),
            "total_bookings": bookings.count(),
            "average_booking_value": float(total_revenue / bookings.count()) if bookings.count() > 0 else 0,
            "daily_breakdown": daily_revenue
        }
    
    def _generate_performance_report(self, start_date, end_date):
        """Generate performance report"""
        bookings = Booking.objects.filter(
            created_at__date__range=[start_date, end_date]
        )
        
        # Status performance
        status_performance = {}
        for status in BookingStatus.choices:
            count = bookings.filter(status=status[0]).count()
            status_performance[status[0]] = {
                'count': count,
                'percentage': round((count / bookings.count() * 100), 2) if bookings.count() > 0 else 0,
                'display_name': status[1]
            }
        
        # Completion rate
        completed = bookings.filter(status=BookingStatus.COMPLETED).count()
        total_services = bookings.filter(
            status__in=[BookingStatus.COMPLETED, BookingStatus.CANCELLED]
        ).count()
        completion_rate = round((completed / total_services * 100), 2) if total_services > 0 else 0
        
        return {
            "total_bookings": bookings.count(),
            "status_breakdown": status_performance,
            "completion_rate": completion_rate,
            "cancellation_rate": status_performance.get(BookingStatus.CANCELLED, {}).get('percentage', 0)
        }
    
    def _generate_assignment_report(self, start_date, end_date):
        """Generate assignment performance report"""
        bookings = Booking.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).select_related('assigned_to')
        
        assigned_count = bookings.filter(assigned_to__isnull=False).count()
        assignment_rate = round((assigned_count / bookings.count() * 100), 2) if bookings.count() > 0 else 0
        
        # Employee performance
        from django.contrib.auth import get_user_model
        User = get_user_model()
        employee_stats = User.objects.filter(
            is_staff=True,
            assigned_bookings__created_at__date__range=[start_date, end_date]
        ).annotate(
            booking_count=Count('assigned_bookings'),
            completed_count=Count('assigned_bookings', filter=Q(assigned_bookings__status=BookingStatus.COMPLETED))
        ).order_by('-booking_count')
        
        employee_data = []
        for employee in employee_stats:
            completion_rate = round(
                (employee.completed_count / employee.booking_count * 100), 2
            ) if employee.booking_count > 0 else 0
            
            employee_data.append({
                "id": employee.id,
                "name": f"{employee.first_name} {employee.last_name}".strip() or employee.email,
                "email": employee.email,
                "total_assignments": employee.booking_count,
                "completed_assignments": employee.completed_count,
                "completion_rate": completion_rate
            })
        
        return {
            "total_bookings": bookings.count(),
            "assigned_bookings": assigned_count,
            "assignment_rate": assignment_rate,
            "employee_performance": employee_data
        }
    
    def _generate_status_report(self, start_date, end_date):
        """Generate detailed status report"""
        bookings = Booking.objects.filter(
            created_at__date__range=[start_date, end_date]
        )
        
        status_trends = {}
        for status in BookingStatus.choices:
            status_bookings = bookings.filter(status=status[0])
            status_trends[status[0]] = {
                'count': status_bookings.count(),
                'display_name': status[1],
                'recent_bookings': list(status_bookings.order_by('-created_at')[:5].values(
                    'book_id', 'user__email', 'created_at'
                ))
            }
        
        return {
            "total_bookings": bookings.count(),
            "status_distribution": status_trends
        }
    
    def _generate_summary_report(self, start_date, end_date):
        """Generate comprehensive summary report"""
        revenue_data = self._generate_revenue_report(start_date, end_date)
        performance_data = self._generate_performance_report(start_date, end_date)
        assignment_data = self._generate_assignment_report(start_date, end_date)
        
        return {
            "revenue": revenue_data,
            "performance": performance_data,
            "assignments": {
                "assignment_rate": assignment_data['assignment_rate'],
                "top_performers": assignment_data['employee_performance'][:5]
            },
            "summary_metrics": {
                "total_bookings": revenue_data['total_bookings'],
                "total_revenue": revenue_data['total_revenue'],
                "completion_rate": performance_data['completion_rate'],
                "assignment_rate": assignment_data['assignment_rate']
            }
        }


@api_view(['POST'])
@permission_classes([IsAdminUser])
@swagger_auto_schema(
    operation_description="Send manual notification to booking customer",
    operation_summary="Send Manual Booking Notification",
    tags=['Admin', 'Booking', 'Notifications'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'booking_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'message_type': openapi.Schema(type=openapi.TYPE_STRING),
            'custom_message': openapi.Schema(type=openapi.TYPE_STRING),
            'include_booking_details': openapi.Schema(type=openapi.TYPE_BOOLEAN)
        },
        required=['booking_id', 'message_type']
    )
)
def send_manual_booking_notification(request):
    """Send manual notification to booking customer"""
    try:
        booking_id = request.data.get('booking_id')
        message_type = request.data.get('message_type')
        custom_message = request.data.get('custom_message', '')
        include_details = request.data.get('include_booking_details', True)
        
        booking = Booking.objects.select_related('user', 'cart', 'assigned_to').get(id=booking_id)
        
        subject_map = {
            'reminder': f"Service Reminder - Booking #{booking.book_id}",
            'update': f"Booking Update - #{booking.book_id}",
            'custom': f"Message from OkPuja - Booking #{booking.book_id}",
            'follow_up': f"Follow-up - Service #{booking.book_id}"
        }
        
        subject = subject_map.get(message_type, f"Notification - Booking #{booking.book_id}")
        
        context = {
            'booking': booking,
            'custom_message': custom_message,
            'include_details': include_details,
            'message_type': message_type,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
        }
        
        html_message = render_to_string('emails/booking/manual_notification.html', context)
        
        send_mail(
            subject,
            custom_message or f"You have a notification regarding your booking #{booking.book_id}",
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            html_message=html_message
        )
        
        return Response({
            "success": True,
            "message": f"Notification sent to {booking.user.email}"
        })
        
    except Booking.DoesNotExist:
        return Response({
            "success": False,
            "error": "Booking not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Manual booking notification failed: {str(e)}")
        return Response({
            "success": False,
            "error": "Failed to send notification"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
