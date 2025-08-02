"""
Cart-based Payment Integration
Handles cart -> payment -> booking flow
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime, timedelta
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

from .models import PaymentOrder
from .services import PaymentService, WebhookService
from cart.models import Cart
from booking.models import Booking


class CartPaymentView(APIView):
    """Create payment from cart"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create payment order from cart",
        operation_summary="Pay for Cart",
        tags=['Payments'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cart_id': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Cart ID (UUID) to create payment for. Use the cart_id field from cart API response, not the database ID.'
                ),
            },
            required=['cart_id']
        ),
        responses={
            201: openapi.Response(
                description="Payment order created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Payment order created for cart",
                        "data": {
                            "payment_order": {
                                "id": "uuid-here",
                                "merchant_order_id": "CART_123_ORDER_456",
                                "amount": 80000,
                                "cart_id": "1f956446-cde2-4e51-a223-06250cb4ed53",
                                "phonepe_payment_url": "https://api-preprod.phonepe.com/..."
                            }
                        }
                    }
                }
            ),
            400: openapi.Response(description="Invalid cart or cart already paid"),
            404: openapi.Response(description="Cart not found")
        }
    )
    def post(self, request):
        """Create payment order from cart"""
        try:
            cart_id = request.data.get('cart_id')
            
            if not cart_id:
                return Response({
                    'success': False,
                    'message': 'cart_id is required (use the cart_id UUID field, not database ID)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get cart using cart_id field (UUID), not database ID
            cart = get_object_or_404(Cart, cart_id=cart_id, user=request.user)
            
            # Check if cart is active
            if cart.status != Cart.StatusChoices.ACTIVE:
                return Response({
                    'success': False,
                    'message': f'Cart is not active. Current status: {cart.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if payment already exists for this cart
            existing_payment = PaymentOrder.objects.filter(
                cart_id=cart_id, 
                status__in=['PENDING', 'INITIATED', 'SUCCESS']
            ).first()
            
            if existing_payment:
                if existing_payment.status == 'SUCCESS':
                    return Response({
                        'success': False,
                        'message': 'Cart has already been paid for'
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Return existing pending payment
                    return Response({
                        'success': True,
                        'message': 'Existing payment order found',
                        'data': {
                            'payment_order': {
                                'id': str(existing_payment.id),
                                'merchant_order_id': existing_payment.merchant_order_id,
                                'amount': existing_payment.amount,
                                'cart_id': existing_payment.cart_id,
                                'status': existing_payment.status,
                                'phonepe_payment_url': existing_payment.phonepe_payment_url
                            }
                        }
                    }, status=status.HTTP_200_OK)
            
            # Calculate amount from cart
            amount_in_rupees = cart.total_price
            amount_in_paisa = int(amount_in_rupees * 100)
            
            # Create payment order with professional redirect handler URL
            payment_data = {
                'amount': amount_in_paisa,
                'description': f"Payment for cart {cart_id}",
                'redirect_url': getattr(settings, 'PHONEPE_PROFESSIONAL_REDIRECT_URL', 'http://localhost:8000/api/payments/redirect/professional/'),
                'cart_id': cart_id
            }
            
            payment_service = PaymentService()
            result = payment_service.create_payment_order(
                user=request.user,
                **payment_data
            )
            
            if result['success']:
                payment_order = result['payment_order']
                
                return Response({
                    'success': True,
                    'message': 'Payment order created for cart',
                    'data': {
                        'payment_order': {
                            'id': str(payment_order.id),
                            'merchant_order_id': payment_order.merchant_order_id,
                            'amount': payment_order.amount,
                            'amount_in_rupees': payment_order.amount_in_rupees,
                            'cart_id': payment_order.cart_id,
                            'status': payment_order.status,
                            'phonepe_payment_url': payment_order.phonepe_payment_url,
                            'created_at': payment_order.created_at.isoformat()
                        }
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': result['message']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Cart.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Cart not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            logger.error(f"Error creating cart payment: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({
                'success': False,
                'message': f'Internal server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartPaymentStatusView(APIView):
    """Get payment status for cart"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get payment status for a cart",
        operation_summary="Get Cart Payment Status",
        tags=['Payments'],
        manual_parameters=[
            openapi.Parameter('cart_id', openapi.IN_PATH, description="Cart ID", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(
                description="Payment status retrieved",
                examples={
                    "application/json": {
                        "success": True,
                        "data": {
                            "cart_id": "CART_123",
                            "payment_status": "SUCCESS",
                            "booking_created": True,
                            "booking_id": "BK-12345678"
                        }
                    }
                }
            ),
            404: openapi.Response(description="Cart or payment not found")
        }
    )
    def get(self, request, cart_id):
        """Get payment status for cart"""
        try:
            # Get cart
            cart = get_object_or_404(Cart, cart_id=cart_id, user=request.user)
            
            # Get payment for cart
            payment = PaymentOrder.objects.filter(cart_id=cart_id).order_by('-created_at').first()
            
            if not payment:
                return Response({
                    'success': False,
                    'message': 'No payment found for this cart'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # IMMEDIATE PAYMENT VERIFICATION (Professional UX)
            if payment.status == 'INITIATED':
                logger.info(f"🔍 IMMEDIATE verification for {payment.merchant_order_id}")
                
                try:
                    # Check payment status with PhonePe immediately
                    payment_service = PaymentService()
                    phonepe_status = payment_service.check_payment_status(payment.merchant_order_id)
                    
                    if phonepe_status and phonepe_status.get('success'):
                        response_data = phonepe_status.get('data', {})
                        transaction_status = response_data.get('state', 'PENDING')
                        
                        logger.info(f"✅ PhonePe immediate status for {payment.merchant_order_id}: {transaction_status}")
                        
                        if transaction_status == 'COMPLETED':
                            # Update payment to SUCCESS immediately
                            payment.status = 'SUCCESS'
                            payment.phonepe_transaction_id = response_data.get('transactionId', '')
                            payment.completed_at = timezone.now()
                            payment.save()
                            
                            logger.info(f"✅ Payment {payment.merchant_order_id} immediately updated to SUCCESS")
                            
                            # Create booking immediately
                            try:
                                webhook_service = WebhookService()
                                booking_result = webhook_service.create_booking_from_payment(payment)
                                if booking_result['success']:
                                    logger.info(f"✅ Booking {booking_result['booking'].book_id} immediately created")
                            except Exception as booking_error:
                                logger.error(f"❌ Error creating booking immediately: {str(booking_error)}")
                                
                        elif transaction_status == 'FAILED':
                            payment.status = 'FAILED'
                            payment.save()
                            logger.info(f"❌ Payment {payment.merchant_order_id} marked as failed")
                            
                except Exception as verify_error:
                    logger.error(f"❌ Error in immediate verification: {str(verify_error)}")
                    # Continue with normal response even if immediate verification fails
            
            # Check if booking was created
            booking = None
            booking_created = False
            
            if payment.status == 'SUCCESS':
                try:
                    booking = Booking.objects.filter(cart=cart).first()
                    booking_created = booking is not None
                except:
                    booking_created = False
            
            return Response({
                'success': True,
                'data': {
                    'cart_id': cart_id,
                    'payment_status': payment.status,
                    'payment_amount': payment.amount_in_rupees,
                    'merchant_order_id': payment.merchant_order_id,
                    'booking_created': booking_created,
                    'booking_id': booking.book_id if booking else None,
                    'cart_status': cart.status,
                    'payment_created_at': payment.created_at.isoformat(),
                    'payment_completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
                    'auto_verified': payment.status != 'INITIATED'  # Indicates if auto-verification occurred
                }
            }, status=status.HTTP_200_OK)
            
        except Cart.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Cart not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting cart payment status: {str(e)}")
            return Response({
                'success': False,
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
