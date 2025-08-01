import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from cart.models import Cart
from .models import PaymentOrder
from .serializers_v2 import CreatePaymentOrderFromCartSerializer, PaymentOrderSerializer
from .phonepe_v2_corrected import PhonePeV2
from .services import WebhookService

logger = logging.getLogger(__name__)

class CreatePaymentOrderFromCartView(generics.CreateAPIView):
    """
    Create a PhonePe payment order directly from a user's cart.
    """
    serializer_class = CreatePaymentOrderFromCartSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create payment order from cart",
        responses={
            201: "Payment order created successfully",
            400: "Invalid cart or cart already paid",
            404: "Cart not found"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_id = serializer.validated_data['cart_id']

        try:
            cart = Cart.objects.get(cart_id=cart_id, user=request.user, status='ACTIVE')
        except Cart.DoesNotExist:
            return Response({"error": "Active cart not found or does not belong to user."}, status=status.HTTP_404_NOT_FOUND)

        if PaymentOrder.objects.filter(cart_id=cart.cart_id, status='SUCCESS').exists():
            return Response({"error": "This cart has already been paid for."}, status=status.HTTP_400_BAD_REQUEST)

        phonepe = PhonePeV2()
        
        # Use the simple redirect URL
        redirect_url = "http://127.0.0.1:8000/api/payments/redirect/simple/"

        try:
            payment_order, phonepe_response = phonepe.create_payment_for_cart(cart, redirect_url)
            
            if payment_order and phonepe_response.get("success"):
                return Response({
                    "success": True,
                    "message": "Payment order created for cart",
                    "data": {
                        "payment_order": PaymentOrderSerializer(payment_order).data,
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"PhonePe payment initiation failed for cart {cart.cart_id}: {phonepe_response.get('message')}")
                return Response({
                    "success": False,
                    "message": f"Failed to create payment order: {phonepe_response.get('message')}"
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Error creating payment for cart {cart.cart_id}: {e}")
            return Response({"error": "An unexpected error occurred while creating the payment."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PhonePeWebhookView(generics.GenericAPIView):
    """
    Handles incoming webhooks from PhonePe to update payment status.
    """
    permission_classes = [] # Webhooks are not authenticated

    @swagger_auto_schema(
        operation_summary="PhonePe Webhook Handler",
        request_body=None, # Manually document if needed
        responses={200: "Webhook processed", 400: "Invalid payload or signature"}
    )
    def post(self, request, *args, **kwargs):
        payload = request.data
        headers = request.headers
        
        logger.info(f"Webhook received with headers: {headers}")
        logger.info(f"Webhook payload: {payload}")

        phonepe = PhonePeV2()
        if not phonepe.verify_webhook_signature(request.body, headers.get('X-Verify')):
            logger.warning("Webhook signature verification failed.")
            return Response({"error": "Signature verification failed"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = WebhookService()
            service.handle_webhook(payload)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error processing webhook: {e}")
            return Response({"error": "Failed to process webhook"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckPaymentStatusView(generics.GenericAPIView):
    """
    Check the status of a payment with PhonePe.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Check Payment Status")
    def get(self, request, merchant_order_id, *args, **kwargs):
        try:
            payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id, user=request.user)
        except PaymentOrder.DoesNotExist:
            return Response({"error": "Payment order not found."}, status=status.HTTP_404_NOT_FOUND)

        phonepe = PhonePeV2()
        status_response = phonepe.check_payment_status(payment_order.merchant_order_id)

        if status_response.get("success"):
            # Update local status based on PhonePe's response
            new_status = status_response.get("data", {}).get("state")
            if new_status and new_status != payment_order.status:
                payment_order.status = new_status
                payment_order.save()
                
                # If payment is now successful, trigger booking creation
                if new_status == 'SUCCESS':
                    service = WebhookService()
                    service.handle_successful_payment(payment_order)

            return Response(status_response, status=status.HTTP_200_OK)
        else:
            return Response(status_response, status=status.HTTP_400_BAD_REQUEST)
