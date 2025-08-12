"""
Professional Payment Status and Retry Management Views
"""

import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import PaymentOrder
from .services import PaymentService

logger = logging.getLogger(__name__)


class PaymentStatusView(APIView):
    """Professional payment status management with timeout handling"""
    
    @swagger_auto_schema(
        operation_description="Get payment status with timeout management",
        responses={
            200: openapi.Response(
                description="Payment status retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "status": "PENDING",
                        "merchant_order_id": "OKPUJA_12345",
                        "amount": 100.00,
                        "remaining_seconds": 240,
                        "expires_at": "2025-08-11T10:35:00",
                        "can_retry": True,
                        "payment_url": "https://mercury-t2.phonepe.com/..."
                    }
                }
            ),
            404: openapi.Response(
                description="Payment order not found"
            )
        }
    )
    def get(self, request, merchant_order_id):
        """Get payment status with timeout handling"""
        try:
            payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
            
            # Check if payment is expired
            if PaymentService.is_payment_expired(payment_order):
                if payment_order.status == 'PENDING':
                    payment_order.status = 'EXPIRED'
                    payment_order.metadata['expired_at'] = datetime.now().isoformat()
                    payment_order.save()
                
                return Response({
                    'success': False,
                    'status': 'EXPIRED',
                    'merchant_order_id': merchant_order_id,
                    'message': 'Payment session has expired. Please create a new booking.',
                    'can_retry': PaymentService.can_retry_payment(payment_order),
                    'expires_at': None,
                    'remaining_seconds': 0
                })
            
            # Calculate remaining time
            remaining_seconds = PaymentService.get_payment_remaining_time(payment_order)
            timeout_minutes = payment_order.metadata.get('payment_timeout_minutes', 5)
            expires_at = payment_order.created_at + timedelta(minutes=timeout_minutes)
            
            return Response({
                'success': True,
                'status': payment_order.status,
                'merchant_order_id': merchant_order_id,
                'amount': float(payment_order.amount),
                'remaining_seconds': remaining_seconds,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'can_retry': PaymentService.can_retry_payment(payment_order),
                'retry_count': payment_order.metadata.get('retry_count', 0),
                'max_retry_attempts': payment_order.metadata.get('max_retry_attempts', 3),
                'payment_url': payment_order.phonepe_payment_url if payment_order.status == 'PENDING' else None
            })
            
        except PaymentOrder.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment status check error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Unable to check payment status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentRetryView(APIView):
    """Handle payment retry with professional limits and validation"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retry payment with professional validation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'redirect_url': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Optional new redirect URL'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Payment retry created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "payment_url": "https://mercury-t2.phonepe.com/...",
                        "expires_in_minutes": 5,
                        "retry_attempt": 2,
                        "max_attempts": 3,
                        "message": "Payment retry 2 created successfully"
                    }
                }
            ),
            400: openapi.Response(
                description="Retry not allowed - limit exceeded or expired"
            ),
            404: openapi.Response(
                description="Payment order not found"
            )
        }
    )
    def post(self, request, merchant_order_id):
        """Retry payment with proper validation"""
        try:
            payment_order = PaymentOrder.objects.get(
                merchant_order_id=merchant_order_id,
                user_id=request.user.id
            )
            
            # Initialize payment service
            payment_service = PaymentService()
            
            # Attempt to retry payment
            retry_result = payment_service.retry_payment(
                payment_order=payment_order,
                redirect_url=request.data.get('redirect_url')
            )
            
            if retry_result['success']:
                return Response({
                    'success': True,
                    'payment_url': retry_result['payment_url'],
                    'expires_in_minutes': retry_result['expires_in_minutes'],
                    'retry_attempt': retry_result['retry_attempt'],
                    'max_attempts': retry_result['max_attempts'],
                    'message': retry_result['message']
                })
            else:
                return Response({
                    'success': False,
                    'error': retry_result['error'],
                    'can_retry': retry_result.get('can_retry', False)
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except PaymentOrder.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment order not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment retry error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Unable to retry payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentCleanupView(APIView):
    """Administrative endpoint to cleanup expired payments"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Cleanup expired payment orders (admin only)",
        responses={
            200: openapi.Response(
                description="Cleanup completed",
                examples={
                    "application/json": {
                        "success": True,
                        "expired_count": 5,
                        "message": "Successfully expired 5 payment orders"
                    }
                }
            ),
            403: openapi.Response(
                description="Admin access required"
            )
        }
    )
    def post(self, request):
        """Clean up expired payment orders (admin only)"""
        try:
            # Check if user is admin
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'error': 'Admin access required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            expired_count = 0
            
            # Find pending payments that should be expired
            pending_orders = PaymentOrder.objects.filter(
                status='PENDING'
            )
            
            for order in pending_orders:
                if PaymentService.is_payment_expired(order):
                    order.status = 'EXPIRED'
                    order.metadata['expired_at'] = datetime.now().isoformat()
                    order.metadata['expired_by_cleanup'] = True
                    order.save()
                    expired_count += 1
            
            logger.info(f'Manual cleanup expired {expired_count} payment orders')
            
            return Response({
                'success': True,
                'expired_count': expired_count,
                'message': f'Successfully expired {expired_count} payment orders'
            })
            
        except Exception as e:
            logger.error(f"Payment cleanup error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Unable to cleanup payments'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
