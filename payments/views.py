"""
Clean Payment API Views with Swagger Documentation
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
from django.utils import timezone
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import PaymentOrder, PaymentRefund
from .serializers import (
    PaymentOrderSerializer, CreatePaymentOrderSerializer,
    PaymentRefundSerializer, CreateRefundSerializer,
    PaymentStatusSerializer
)
from .services import PaymentService, WebhookService
from .webhook_auth import authenticate_webhook

logger = logging.getLogger(__name__)


class CreatePaymentView(APIView):
    """Create a new payment order and get PhonePe payment URL"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create a new payment order for PhonePe V2 Standard Checkout",
        operation_summary="Create Payment Order",
        tags=['Payments'],
        request_body=CreatePaymentOrderSerializer,
        responses={
            201: openapi.Response(
                description="Payment order created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Payment order created successfully",
                        "data": {
                            "payment_order": {
                                "id": 123,
                                "merchant_order_id": "OKPUJA_ORDER_123456",
                                "amount": 99900,
                                "amount_in_rupees": "999.00",
                                "currency": "INR",
                                "status": "INITIATED",
                                "description": "Payment for puja booking"
                            },
                            "payment_url": "https://mercury-uat.phonepe.com/transact/uat_v2?token=...",
                            "merchant_order_id": "OKPUJA_ORDER_123456"
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
                            "amount": ["This field is required."],
                            "redirect_url": ["Enter a valid URL."]
                        }
                    }
                }
            ),
            401: openapi.Response(
                description="Authentication required",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
            500: openapi.Response(
                description="Internal server error",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Internal server error"
                    }
                }
            )
        }
    )
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
    """Check payment status and get updated information"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check the current status of a payment order",
        operation_summary="Check Payment Status",
        tags=['Payments'],
        manual_parameters=[
            openapi.Parameter(
                'merchant_order_id',
                openapi.IN_PATH,
                description="Unique merchant order ID for the payment",
                type=openapi.TYPE_STRING,
                required=True,
                example="OKPUJA_ORDER_123456"
            )
        ],
        responses={
            200: openapi.Response(
                description="Payment status retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "id": 123,
                            "merchant_order_id": "OKPUJA_ORDER_123456",
                            "amount": 99900,
                            "amount_in_rupees": "999.00",
                            "currency": "INR",
                            "status": "SUCCESS",
                            "payment_method": "PHONEPE",
                            "completed_at": "2025-08-01T10:30:00Z"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request or payment not found",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Payment status check failed"
                    }
                }
            ),
            401: openapi.Response(description="Authentication required"),
            404: openapi.Response(
                description="Payment order not found",
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            )
        }
    )
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
    """List user's payment orders with pagination and filtering"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get a list of all payment orders for the authenticated user",
        operation_summary="List Payment Orders",
        tags=['Payments'],
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter payments by status (PENDING, SUCCESS, FAILED, CANCELLED)",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['PENDING', 'SUCCESS', 'FAILED', 'CANCELLED']
            ),
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Number of results to return per page",
                type=openapi.TYPE_INTEGER,
                required=False,
                default=20
            ),
            openapi.Parameter(
                'offset',
                openapi.IN_QUERY,
                description="Number of results to skip",
                type=openapi.TYPE_INTEGER,
                required=False,
                default=0
            )
        ],
        responses={
            200: openapi.Response(
                description="Payment orders retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "count": 25,
                        "data": [
                            {
                                "id": 123,
                                "merchant_order_id": "OKPUJA_ORDER_123456",
                                "amount": 99900,
                                "amount_in_rupees": "999.00",
                                "currency": "INR",
                                "status": "SUCCESS",
                                "description": "Payment for puja booking",
                                "created_at": "2025-08-01T10:00:00Z",
                                "completed_at": "2025-08-01T10:30:00Z"
                            }
                        ]
                    }
                }
            ),
            401: openapi.Response(description="Authentication required")
        }
    )
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
    """Create a refund for a successful payment"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create a refund for a successful payment order",
        operation_summary="Create Refund",
        tags=['Refunds'],
        manual_parameters=[
            openapi.Parameter(
                'merchant_order_id',
                openapi.IN_PATH,
                description="Unique merchant order ID for the payment to refund",
                type=openapi.TYPE_STRING,
                required=True,
                example="OKPUJA_ORDER_123456"
            )
        ],
        request_body=CreateRefundSerializer,
        responses={
            201: openapi.Response(
                description="Refund created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Refund created successfully",
                        "data": {
                            "id": 456,
                            "merchant_refund_id": "OKPUJA_REFUND_789012",
                            "amount": 50000,
                            "amount_in_rupees": "500.00",
                            "status": "INITIATED",
                            "reason": "Customer requested cancellation",
                            "created_at": "2025-08-01T11:00:00Z"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request - Invalid refund data or payment not eligible",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Payment is not eligible for refund"
                    }
                }
            ),
            401: openapi.Response(description="Authentication required"),
            404: openapi.Response(description="Payment order not found")
        }
    )
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
    """Check refund status and processing information"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check the current status of a refund request",
        operation_summary="Check Refund Status",
        tags=['Refunds'],
        manual_parameters=[
            openapi.Parameter(
                'merchant_refund_id',
                openapi.IN_PATH,
                description="Unique merchant refund ID",
                type=openapi.TYPE_STRING,
                required=True,
                example="OKPUJA_REFUND_789012"
            )
        ],
        responses={
            200: openapi.Response(
                description="Refund status retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "id": 456,
                            "merchant_refund_id": "OKPUJA_REFUND_789012",
                            "amount": 50000,
                            "amount_in_rupees": "500.00",
                            "status": "SUCCESS",
                            "reason": "Customer requested cancellation",
                            "created_at": "2025-08-01T11:00:00Z",
                            "processed_at": "2025-08-01T11:15:00Z"
                        }
                    }
                }
            ),
            400: openapi.Response(description="Bad request"),
            401: openapi.Response(description="Authentication required"),
            404: openapi.Response(description="Refund not found")
        }
    )
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
    """Handle PhonePe webhook notifications for payment status updates"""
    
    permission_classes = []  # No authentication for webhooks
    
    @swagger_auto_schema(
        operation_description="Get webhook endpoint information for testing purposes",
        operation_summary="Webhook Endpoint Info",
        tags=['Webhooks'],
        responses={
            200: openapi.Response(
                description="Webhook endpoint information",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "PhonePe Webhook Endpoint",
                        "info": {
                            "method": "POST",
                            "description": "This endpoint accepts PhonePe webhook notifications",
                            "usage": "Send POST requests with PhonePe webhook payload",
                            "environment": "uat"
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get webhook endpoint information (for testing purposes)"""
        return Response({
            'success': True,
            'message': 'PhonePe Webhook Endpoint',
            'info': {
                'method': 'POST',
                'description': 'This endpoint accepts PhonePe webhook notifications',
                'usage': 'Send POST requests with PhonePe webhook payload',
                'environment': getattr(settings, 'PHONEPE_ENV', 'uat'),
                'timestamp': timezone.now().isoformat()
            }
        })
    
    @swagger_auto_schema(
        operation_description="Process PhonePe webhook notifications for payment status updates",
        operation_summary="PhonePe Webhook Handler",
        tags=['Webhooks'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="PhonePe webhook payload",
            properties={
                'transactionId': openapi.Schema(type=openapi.TYPE_STRING, description="PhonePe transaction ID"),
                'merchantOrderId': openapi.Schema(type=openapi.TYPE_STRING, description="Merchant order ID"),
                'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description="Amount in paisa"),
                'state': openapi.Schema(type=openapi.TYPE_STRING, description="Payment state"),
                'responseCode': openapi.Schema(type=openapi.TYPE_STRING, description="Response code"),
            },
            example={
                "transactionId": "T1234567890",
                "merchantOrderId": "OKPUJA_ORDER_123456",
                "amount": 99900,
                "state": "COMPLETED",
                "responseCode": "SUCCESS"
            }
        ),
        responses={
            200: openapi.Response(
                description="Webhook processed successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Webhook processed successfully"
                    }
                }
            ),
            400: openapi.Response(
                description="Webhook processing failed",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Invalid webhook data"
                    }
                }
            )
        }
    )
    def post(self, request):
        """Process PhonePe webhook with authentication"""
        try:
            # First authenticate the webhook request
            is_authenticated, auth_error = authenticate_webhook(request)
            if not is_authenticated:
                return auth_error
            
            webhook_data = request.data
            headers = dict(request.headers)
            
            logger.info(f"Authenticated webhook received: {webhook_data}")
            
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
@swagger_auto_schema(
    method='get',
    operation_description="Health check endpoint to verify payment service status",
    operation_summary="Payment Service Health Check",
    tags=['Utilities'],
    responses={
        200: openapi.Response(
            description="Payment service is healthy",
            examples={
                "application/json": {
                    "success": True,
                    "message": "Payment service is running",
                    "user": "user@example.com",
                    "environment": "uat"
                }
            }
        ),
        401: openapi.Response(description="Authentication required")
    }
)
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


@swagger_auto_schema(
    method='post',
    operation_description="Quick test endpoint for payment integration - creates a test payment order",
    operation_summary="Quick Payment Test",
    tags=['Utilities'],
    responses={
        200: openapi.Response(
            description="Test payment created successfully",
            examples={
                "application/json": {
                    "success": True,
                    "data": {
                        "merchant_order_id": "OKPUJA_TEST_123456",
                        "payment_url": "https://mercury-uat.phonepe.com/transact/uat_v2?token=...",
                        "error": None
                    }
                }
            }
        ),
        401: openapi.Response(description="Authentication required"),
        500: openapi.Response(
            description="Test failed",
            examples={
                "application/json": {
                    "success": False,
                    "error": "Payment service unavailable"
                }
            }
        )
    }
)
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


class LatestPaymentStatusView(APIView):
    """Get user's latest payment status - useful after redirect"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get the latest payment order for the authenticated user",
        operation_summary="Latest Payment Status",
        tags=['Payments'],
        responses={
            200: openapi.Response(
                description="Latest payment order",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "id": "uuid",
                            "merchant_order_id": "OKPUJA_123456",
                            "amount": 500,
                            "status": "SUCCESS",
                            "created_at": "2025-07-31T19:21:48.146218Z"
                        }
                    }
                }
            ),
            404: openapi.Response(description="No payments found"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request):
        """Get user's latest payment order"""
        try:
            # Get the most recent payment order for this user
            latest_payment = PaymentOrder.objects.filter(
                user=request.user
            ).order_by('-created_at').first()
            
            if not latest_payment:
                return Response({
                    'success': False,
                    'error': 'No payments found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check current status with PhonePe
            payment_service = PaymentService()
            result = payment_service.check_payment_status(latest_payment.merchant_order_id)
            
            if result['success']:
                payment_serializer = PaymentOrderSerializer(result['payment_order'])
                
                return Response({
                    'success': True,
                    'data': payment_serializer.data
                })
            else:
                # Return local data if PhonePe check fails
                payment_serializer = PaymentOrderSerializer(latest_payment)
                return Response({
                    'success': True,
                    'data': payment_serializer.data,
                    'note': 'Local status (PhonePe check failed)'
                })
                
        except Exception as e:
            logger.error(f"Latest payment status error: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
