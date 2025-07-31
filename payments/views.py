"""
Clean Payment API Views
"""

import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from .models import PaymentOrder, PaymentRefund
from .serializers import (
    PaymentOrderSerializer, CreatePaymentOrderSerializer,
    PaymentRefundSerializer, CreateRefundSerializer,
    PaymentStatusSerializer
)
from .services import PaymentService, WebhookService

logger = logging.getLogger(__name__)


class CreatePaymentView(APIView):
    """Create a new payment order"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create payment order and get payment URL"""
        try:
            serializer = CreatePaymentOrderSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create payment order using service
            payment_service = PaymentService()
            result = payment_service.create_payment_order(
                user=request.user,
                amount=serializer.validated_data['amount'],
                redirect_url=serializer.validated_data['redirect_url'],
                description=serializer.validated_data.get('description'),
                metadata=serializer.validated_data.get('metadata', {})
            )
            
            if result['success']:
                payment_serializer = PaymentOrderSerializer(result['payment_order'])
                
                return Response({
                    'success': True,
                    'message': 'Payment order created successfully',
                    'data': {
                        'payment_order': payment_serializer.data,
                        'payment_url': result['payment_url'],
                        'merchant_order_id': result['merchant_order_id']
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Payment creation error: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatusView(APIView):
    """Check payment status"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, merchant_order_id):
        """Get payment status"""
        try:
            # Check if user owns this payment
            payment_order = get_object_or_404(
                PaymentOrder, 
                merchant_order_id=merchant_order_id,
                user=request.user
            )
            
            # Check status with PhonePe
            payment_service = PaymentService()
            result = payment_service.check_payment_status(merchant_order_id)
            
            if result['success']:
                payment_serializer = PaymentOrderSerializer(result['payment_order'])
                
                return Response({
                    'success': True,
                    'data': payment_serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Payment status check error: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentListView(APIView):
    """List user's payments"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's payment orders"""
        try:
            payments = PaymentOrder.objects.filter(user=request.user)
            serializer = PaymentOrderSerializer(payments, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Payment list error: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateRefundView(APIView):
    """Create refund for a payment"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, merchant_order_id):
        """Create refund"""
        try:
            # Check if user owns this payment
            payment_order = get_object_or_404(
                PaymentOrder,
                merchant_order_id=merchant_order_id,
                user=request.user
            )
            
            serializer = CreateRefundSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create refund using service
            payment_service = PaymentService()
            result = payment_service.create_refund(
                payment_order=payment_order,
                amount=serializer.validated_data['amount'],
                reason=serializer.validated_data.get('reason')
            )
            
            if result['success']:
                refund_serializer = PaymentRefundSerializer(result['refund'])
                
                return Response({
                    'success': True,
                    'message': 'Refund created successfully',
                    'data': refund_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Refund creation error: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefundStatusView(APIView):
    """Check refund status"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, merchant_refund_id):
        """Get refund status"""
        try:
            # Check if user owns this refund
            refund = get_object_or_404(
                PaymentRefund,
                merchant_refund_id=merchant_refund_id,
                payment_order__user=request.user
            )
            
            # Check status with PhonePe
            payment_service = PaymentService()
            result = payment_service.check_refund_status(merchant_refund_id)
            
            if result['success']:
                refund_serializer = PaymentRefundSerializer(result['refund'])
                
                return Response({
                    'success': True,
                    'data': refund_serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Refund status check error: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class PhonePeWebhookView(APIView):
    """Handle PhonePe webhooks"""
    
    permission_classes = []  # No authentication for webhooks
    
    def post(self, request):
        """Process PhonePe webhook"""
        try:
            webhook_data = request.data
            headers = dict(request.headers)
            
            # Process webhook using service
            webhook_service = WebhookService()
            result = webhook_service.process_payment_webhook(webhook_data, headers)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Webhook processed successfully'
                })
            else:
                logger.error(f"Webhook processing failed: {result['error']}")
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return Response({
                'success': False,
                'error': 'Webhook processing failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Simple function-based views for quick testing
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_health_check(request):
    """Simple health check for payment service"""
    return Response({
        'success': True,
        'message': 'Payment service is running',
        'user': request.user.username,
        'environment': getattr(settings, 'PHONEPE_ENV', 'uat')
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def quick_payment_test(request):
    """Quick payment test endpoint"""
    try:
        payment_service = PaymentService()
        
        result = payment_service.create_payment_order(
            user=request.user,
            amount=10000,  # ₹100
            redirect_url='https://okpuja.com/payment/success',
            description='Test payment'
        )
        
        return Response({
            'success': result['success'],
            'data': {
                'merchant_order_id': result.get('merchant_order_id'),
                'payment_url': result.get('payment_url'),
                'error': result.get('error')
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
