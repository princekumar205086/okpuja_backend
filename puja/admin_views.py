"""
Enterprise-level admin views for Puja system
Comprehensive admin endpoints with notification management
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

from puja.models import PujaCategory, PujaService, Package, PujaBooking
from .puja_admin_serializers import (
    AdminPujaServiceSerializer,
    AdminPujaBookingSerializer,
    AdminPujaBookingUpdateSerializer,
    AdminPujaBulkActionSerializer,
    AdminPujaDashboardSerializer,
    AdminPujaReportSerializer
)
from core.permissions import IsAdminUser, IsStaffUser

logger = logging.getLogger(__name__)


class AdminPujaDashboardView(APIView):
    """
    Enterprise Dashboard for Puja Admin
    Provides comprehensive analytics and overview
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get comprehensive puja dashboard data",
        operation_summary="Admin Puja Dashboard Analytics",
        tags=['Admin', 'Puja', 'Analytics'],
        responses={
            200: openapi.Response(
                description="Dashboard data retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "overview": {
                                "total_bookings": 250,
                                "confirmed_bookings": 180,
                                "completed_bookings": 150,
                                "cancelled_bookings": 15,
                                "total_revenue": "375000.00",
                                "average_booking_value": "1500.00",
                                "active_services": 15,
                                "total_packages": 45
                            },
                            "recent_bookings": [],
                            "popular_services": [],
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
            total_bookings = PujaBooking.objects.count()
            confirmed_bookings = PujaBooking.objects.filter(status='CONFIRMED').count()
            completed_bookings = PujaBooking.objects.filter(status='COMPLETED').count()
            cancelled_bookings = PujaBooking.objects.filter(status='CANCELLED').count()
            pending_bookings = PujaBooking.objects.filter(status='PENDING').count()
            
            # Revenue analytics (based on package prices)
            revenue_data = PujaBooking.objects.filter(
                created_at__date__range=[start_date, end_date],
                status__in=['CONFIRMED', 'COMPLETED']
            ).select_related('package').aggregate(
                total_revenue=Sum('package__price'),
                avg_booking_value=Avg('package__price'),
                booking_count=Count('id')
            )
            
            # Service performance
            service_stats = PujaService.objects.annotate(
                booking_count=Count('bookings'),
                total_revenue=Sum('packages__bookings__package__price',
                    filter=Q(packages__bookings__status__in=['CONFIRMED', 'COMPLETED'])
                ),
                package_count=Count('packages')
            ).filter(is_active=True).order_by('-booking_count')[:10]
            
            # Recent bookings
            recent_bookings = PujaBooking.objects.select_related(
                'puja_service', 'package', 'user'
            ).order_by('-created_at')[:15]
            
            # Upcoming bookings (next 7 days)
            upcoming_bookings = PujaBooking.objects.filter(
                status='CONFIRMED',
                booking_date__range=[timezone.now().date(), timezone.now().date() + timedelta(days=7)]
            ).select_related('puja_service', 'package', 'user').order_by('booking_date', 'start_time')
            
            # Popular services by booking count
            popular_services = PujaService.objects.annotate(
                booking_count=Count('bookings', filter=Q(bookings__created_at__gte=start_date))
            ).filter(is_active=True, booking_count__gt=0).order_by('-booking_count')[:5]
            
            dashboard_data = {
                "overview": {
                    "total_bookings": total_bookings,
                    "confirmed_bookings": confirmed_bookings,
                    "completed_bookings": completed_bookings,
                    "cancelled_bookings": cancelled_bookings,
                    "pending_bookings": pending_bookings,
                    "total_revenue": str(revenue_data.get('total_revenue') or 0),
                    "average_booking_value": str(revenue_data.get('avg_booking_value') or 0),
                    "bookings_this_period": revenue_data.get('booking_count', 0),
                    "active_services": PujaService.objects.filter(is_active=True).count(),
                    "total_packages": Package.objects.filter(is_active=True).count(),
                    "total_categories": PujaCategory.objects.count()
                },
                "recent_bookings": AdminPujaBookingSerializer(recent_bookings, many=True).data,
                "upcoming_bookings": AdminPujaBookingSerializer(upcoming_bookings, many=True).data,
                "popular_services": [
                    {
                        "id": service.id,
                        "title": service.title,
                        "category": service.category.name,
                        "type": service.get_type_display(),
                        "booking_count": service.booking_count or 0,
                        "package_count": service.package_count or 0
                    } for service in popular_services
                ],
                "service_performance": [
                    {
                        "id": service.id,
                        "title": service.title,
                        "category": service.category.name,
                        "booking_count": service.booking_count or 0,
                        "total_revenue": str(service.total_revenue or 0),
                        "package_count": service.package_count or 0
                    } for service in service_stats
                ]
            }
            
            return Response({
                "success": True,
                "data": dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Puja admin dashboard error: {str(e)}")
            return Response({
                "success": False,
                "error": "Failed to load dashboard data"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminPujaBookingManagementView(generics.ListAPIView):
    """
    Advanced puja booking management for admins
    Supports filtering, search, and analytics
    """
    serializer_class = AdminPujaBookingSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'puja_service', 'package', 'booking_date']
    search_fields = ['contact_name', 'contact_email', 'contact_number', 'address']
    ordering_fields = ['created_at', 'booking_date', 'start_time']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = PujaBooking.objects.select_related(
            'puja_service', 'package', 'user', 'puja_service__category'
        ).all()
        
        # Additional filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        service_type = self.request.GET.get('service_type')
        category = self.request.GET.get('category')
        
        if date_from:
            queryset = queryset.filter(booking_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(booking_date__lte=date_to)
        if service_type:
            queryset = queryset.filter(puja_service__type=service_type)
        if category:
            queryset = queryset.filter(puja_service__category_id=category)
            
        return queryset
    
    @swagger_auto_schema(
        operation_description="Get all puja bookings with advanced filtering",
        operation_summary="Admin Puja Booking Management",
        tags=['Admin', 'Puja', 'Bookings'],
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Filter from date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="Filter to date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('service_type', openapi.IN_QUERY, description="Filter by service type", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminPujaBookingDetailView(generics.RetrieveUpdateAPIView):
    """
    Detailed puja booking view and update for admins
    """
    queryset = PujaBooking.objects.select_related('puja_service', 'package', 'user').all()
    serializer_class = AdminPujaBookingUpdateSerializer
    permission_classes = [IsAdminUser]
    
    def perform_update(self, serializer):
        """Handle booking updates with notifications"""
        booking = self.get_object()
        old_status = booking.status
        old_date = booking.booking_date
        old_time = booking.start_time
        
        # Save the booking
        updated_booking = serializer.save()
        
        # Send notifications based on changes
        try:
            # Status change notification
            if old_status != updated_booking.status:
                self._send_status_change_notification(updated_booking, old_status)
            
            # Schedule change notification
            if (old_date != updated_booking.booking_date or 
                old_time != updated_booking.start_time):
                self._send_reschedule_notification(updated_booking, old_date, old_time)
                
        except Exception as e:
            logger.error(f"Failed to send puja booking update notifications: {str(e)}")
    
    def _send_status_change_notification(self, booking, old_status):
        """Send notification when booking status changes"""
        try:
            subject = f"Puja Booking Status Updated - {booking.id}"
            
            html_message = render_to_string('emails/puja/booking_status_update.html', {
                'booking': booking,
                'old_status': old_status,
                'new_status': booking.status,
                'service_name': booking.puja_service.title,
                'package_details': booking.package,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your puja booking status has been updated to {booking.get_status_display()}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
            
            # Send admin notification
            self._send_admin_notification(booking, 'status_updated', {
                'old_status': old_status,
                'new_status': booking.status
            })
            
            logger.info(f"Status change notification sent for puja booking {booking.id}")
            
        except Exception as e:
            logger.error(f"Failed to send puja status change notification: {str(e)}")
    
    def _send_reschedule_notification(self, booking, old_date, old_time):
        """Send reschedule notification to customer"""
        try:
            subject = f"Puja Session Rescheduled - Booking #{booking.id}"
            
            html_message = render_to_string('emails/puja/booking_rescheduled.html', {
                'booking': booking,
                'old_date': old_date,
                'old_time': old_time,
                'service_name': booking.puja_service.title,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your puja session has been rescheduled to {booking.booking_date} at {booking.start_time}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
            
            logger.info(f"Reschedule notification sent for puja booking {booking.id}")
            
        except Exception as e:
            logger.error(f"Failed to send puja reschedule notification: {str(e)}")
    
    def _send_admin_notification(self, booking, notification_type, context=None):
        """Send notification to admin team"""
        try:
            admin_emails = [getattr(settings, 'ADMIN_PERSONAL_EMAIL', 'okpuja108@gmail.com')]
            
            subject_map = {
                'status_updated': f"Puja Booking Status Updated - #{booking.id}",
                'booking_created': f"New Puja Booking - #{booking.id}",
                'booking_cancelled': f"Puja Booking Cancelled - #{booking.id}",
            }
            
            subject = subject_map.get(notification_type, f"Puja Notification - #{booking.id}")
            
            html_message = render_to_string('emails/puja/admin_notification.html', {
                'booking': booking,
                'notification_type': notification_type,
                'context': context or {},
                'admin_panel_url': getattr(settings, 'ADMIN_PANEL_URL', 'https://admin.okpuja.com')
            })
            
            for admin_email in admin_emails:
                send_mail(
                    subject,
                    f"Puja booking notification: {notification_type} for booking #{booking.id}",
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                    html_message=html_message,
                    fail_silently=True
                )
            
            logger.info(f"Admin notification sent for puja booking {booking.id} - {notification_type}")
            
        except Exception as e:
            logger.error(f"Failed to send puja admin notification: {str(e)}")


class AdminPujaBulkActionsView(APIView):
    """
    Bulk operations for puja booking management
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Perform bulk actions on puja bookings",
        operation_summary="Bulk Puja Booking Actions",
        tags=['Admin', 'Puja', 'Bulk Operations'],
        request_body=AdminPujaBulkActionSerializer,
        responses={
            200: openapi.Response(
                description="Bulk action completed successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Bulk action completed",
                        "processed": 15,
                        "failed": 0,
                        "details": []
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = AdminPujaBulkActionSerializer(data=request.data)
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
                bookings = PujaBooking.objects.filter(id__in=booking_ids).select_related(
                    'puja_service', 'package'
                )
                processed = 0
                failed = 0
                details = []
                
                for booking in bookings:
                    try:
                        old_status = booking.status
                        
                        if action == 'confirm_bookings':
                            booking.status = 'CONFIRMED'
                            booking.save()
                            self._send_bulk_confirmation(booking)
                            
                        elif action == 'cancel_bookings':
                            booking.status = 'CANCELLED'
                            booking.cancellation_reason = params.get('reason', 'Cancelled by admin')
                            booking.save()
                            self._send_bulk_cancellation(booking, params.get('reason'))
                            
                        elif action == 'complete_bookings':
                            booking.status = 'COMPLETED'
                            booking.save()
                            self._send_bulk_completion(booking)
                            
                        elif action == 'send_reminders':
                            self._send_booking_reminder(booking)
                            
                        elif action == 'update_status':
                            new_status = params.get('status')
                            if new_status:
                                booking.status = new_status
                                booking.save()
                                self._send_status_update_notification(booking, old_status, new_status)
                        
                        processed += 1
                        details.append({
                            "booking_id": booking.id,
                            "status": "success",
                            "message": f"Action '{action}' completed successfully"
                        })
                        
                    except Exception as e:
                        failed += 1
                        details.append({
                            "booking_id": booking.id,
                            "status": "failed",
                            "message": str(e)
                        })
                        logger.error(f"Bulk action failed for puja booking {booking.id}: {str(e)}")
                
                return Response({
                    "success": True,
                    "message": f"Bulk action '{action}' completed",
                    "processed": processed,
                    "failed": failed,
                    "details": details
                })
                
        except Exception as e:
            logger.error(f"Puja bulk action failed: {str(e)}")
            return Response({
                "success": False,
                "error": "Bulk action failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _send_bulk_confirmation(self, booking):
        """Send confirmation email for bulk operations"""
        try:
            subject = f"Puja Booking Confirmed - #{booking.id}"
            
            html_message = render_to_string('emails/puja/booking_confirmed.html', {
                'booking': booking,
                'service_name': booking.puja_service.title,
                'package_details': booking.package,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your puja booking has been confirmed for {booking.booking_date} at {booking.start_time}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send bulk confirmation: {str(e)}")
    
    def _send_bulk_cancellation(self, booking, reason):
        """Send cancellation email for bulk operations"""
        try:
            subject = f"Puja Booking Cancelled - #{booking.id}"
            
            html_message = render_to_string('emails/puja/booking_cancelled.html', {
                'booking': booking,
                'cancellation_reason': reason,
                'service_name': booking.puja_service.title,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your puja booking has been cancelled. Reason: {reason}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send bulk cancellation: {str(e)}")
    
    def _send_bulk_completion(self, booking):
        """Send completion email for bulk operations"""
        try:
            subject = f"Puja Completed - Thank You! - #{booking.id}"
            
            html_message = render_to_string('emails/puja/puja_completed.html', {
                'booking': booking,
                'service_name': booking.puja_service.title,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Your puja service has been completed. Thank you for choosing our services!",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send bulk completion: {str(e)}")
    
    def _send_booking_reminder(self, booking):
        """Send reminder email"""
        try:
            subject = f"Puja Reminder - #{booking.id}"
            
            html_message = render_to_string('emails/puja/booking_reminder.html', {
                'booking': booking,
                'service_name': booking.puja_service.title,
                'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
            })
            
            send_mail(
                subject,
                f"Reminder: Your puja is scheduled for {booking.booking_date} at {booking.start_time}",
                settings.DEFAULT_FROM_EMAIL,
                [booking.contact_email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send booking reminder: {str(e)}")


class AdminPujaServiceManagementView(generics.ListCreateAPIView):
    """
    Advanced puja service management for admins
    """
    queryset = PujaService.objects.all()
    serializer_class = AdminPujaServiceSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'type', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at']
    ordering = ['title']


class AdminPujaReportsView(APIView):
    """
    Comprehensive puja reporting system
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Generate comprehensive puja reports",
        operation_summary="Admin Puja Reports",
        tags=['Admin', 'Puja', 'Reports'],
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
            elif report_type == 'categories':
                report_data = self._generate_category_report(start_date, end_date)
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
            logger.error(f"Puja report generation failed: {str(e)}")
            return Response({
                "success": False,
                "error": "Failed to generate report"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_revenue_report(self, start_date, end_date):
        """Generate detailed revenue report"""
        bookings = PujaBooking.objects.filter(
            created_at__date__range=[start_date, end_date],
            status__in=['CONFIRMED', 'COMPLETED']
        ).select_related('package', 'puja_service')
        
        total_revenue = sum(booking.package.price for booking in bookings)
        
        # Revenue by service type
        service_revenue = {}
        for booking in bookings:
            service_type = booking.puja_service.get_type_display()
            if service_type not in service_revenue:
                service_revenue[service_type] = {
                    'count': 0,
                    'revenue': 0
                }
            service_revenue[service_type]['count'] += 1
            service_revenue[service_type]['revenue'] += float(booking.package.price)
        
        return {
            "total_revenue": float(total_revenue),
            "total_bookings": bookings.count(),
            "average_booking_value": float(total_revenue / bookings.count()) if bookings.count() > 0 else 0,
            "service_type_breakdown": service_revenue
        }
    
    def _generate_booking_report(self, start_date, end_date):
        """Generate detailed booking report"""
        bookings = PujaBooking.objects.filter(
            created_at__date__range=[start_date, end_date]
        )
        
        status_breakdown = {}
        for status_choice in PujaBooking.BookingStatus.choices:
            status = status_choice[0]
            count = bookings.filter(status=status).count()
            status_breakdown[status] = {
                'count': count,
                'display_name': status_choice[1]
            }
        
        return {
            "total_bookings": bookings.count(),
            "status_breakdown": status_breakdown,
            "upcoming_bookings": PujaBooking.objects.filter(
                booking_date__gte=timezone.now().date(),
                status='CONFIRMED'
            ).count()
        }
    
    def _generate_service_report(self, start_date, end_date):
        """Generate service performance report"""
        services = PujaService.objects.annotate(
            booking_count=Count('bookings',
                filter=Q(bookings__created_at__date__range=[start_date, end_date])
            ),
            total_revenue=Sum('packages__bookings__package__price',
                filter=Q(packages__bookings__created_at__date__range=[start_date, end_date])
            )
        )
        
        service_data = []
        for service in services:
            service_data.append({
                "id": service.id,
                "title": service.title,
                "category": service.category.name,
                "type": service.get_type_display(),
                "booking_count": service.booking_count or 0,
                "total_revenue": float(service.total_revenue or 0),
                "is_active": service.is_active
            })
        
        return {
            "services": service_data,
            "top_performing": sorted(service_data, key=lambda x: x['booking_count'], reverse=True)[:5]
        }
    
    def _generate_category_report(self, start_date, end_date):
        """Generate category performance report"""
        categories = PujaCategory.objects.annotate(
            service_count=Count('services'),
            booking_count=Count('services__bookings',
                filter=Q(services__bookings__created_at__date__range=[start_date, end_date])
            ),
            total_revenue=Sum('services__packages__bookings__package__price',
                filter=Q(services__packages__bookings__created_at__date__range=[start_date, end_date])
            )
        )
        
        category_data = []
        for category in categories:
            category_data.append({
                "id": category.id,
                "name": category.name,
                "service_count": category.service_count or 0,
                "booking_count": category.booking_count or 0,
                "total_revenue": float(category.total_revenue or 0)
            })
        
        return {
            "categories": category_data,
            "most_popular": sorted(category_data, key=lambda x: x['booking_count'], reverse=True)[:3]
        }
    
    def _generate_summary_report(self, start_date, end_date):
        """Generate comprehensive summary report"""
        revenue_data = self._generate_revenue_report(start_date, end_date)
        booking_data = self._generate_booking_report(start_date, end_date)
        service_data = self._generate_service_report(start_date, end_date)
        category_data = self._generate_category_report(start_date, end_date)
        
        return {
            "revenue": revenue_data,
            "bookings": booking_data,
            "services": {
                "total_active_services": len([s for s in service_data['services'] if s['is_active']]),
                "top_services": service_data['top_performing'][:3]
            },
            "categories": {
                "total_categories": len(category_data['categories']),
                "most_popular": category_data['most_popular']
            }
        }


@api_view(['POST'])
@permission_classes([IsAdminUser])
@swagger_auto_schema(
    operation_description="Send manual notification to puja customer",
    operation_summary="Send Manual Puja Notification",
    tags=['Admin', 'Puja', 'Notifications'],
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
def send_manual_puja_notification(request):
    """Send manual notification to puja customer"""
    try:
        booking_id = request.data.get('booking_id')
        message_type = request.data.get('message_type')
        custom_message = request.data.get('custom_message', '')
        include_details = request.data.get('include_booking_details', True)
        
        booking = PujaBooking.objects.select_related('puja_service', 'package').get(id=booking_id)
        
        subject_map = {
            'reminder': f"Puja Reminder - Booking #{booking.id}",
            'update': f"Puja Booking Update - #{booking.id}",
            'custom': f"Message from OkPuja - Booking #{booking.id}",
            'follow_up': f"Follow-up - Puja Service #{booking.id}"
        }
        
        subject = subject_map.get(message_type, f"Notification - Booking #{booking.id}")
        
        context = {
            'booking': booking,
            'custom_message': custom_message,
            'include_details': include_details,
            'message_type': message_type,
            'service_name': booking.puja_service.title,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja')
        }
        
        html_message = render_to_string('emails/puja/manual_notification.html', context)
        
        send_mail(
            subject,
            custom_message or f"You have a notification regarding your puja booking #{booking.id}",
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message
        )
        
        return Response({
            "success": True,
            "message": f"Notification sent to {booking.contact_email}"
        })
        
    except PujaBooking.DoesNotExist:
        return Response({
            "success": False,
            "error": "Booking not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Manual puja notification failed: {str(e)}")
        return Response({
            "success": False,
            "error": "Failed to send notification"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
