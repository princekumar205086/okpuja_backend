import logging
from django.shortcuts import redirect
from django.views import View
from django.http import HttpRequest, HttpResponse, JsonResponse
from accounts.models import User
from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder
from payments.services import WebhookService
import traceback

logger = logging.getLogger(__name__)

class SimpleRedirectView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        logger.info("SimpleRedirectView: GET request received.")
        
        user = request.user
        if not user.is_authenticated:
            logger.warning("User is not authenticated. Redirecting to login.")
            return redirect("/login?error=unauthenticated")

        try:
            # 1. Strategy: Find the cart that was actually paid for
            # Look for the most recent payment that's either SUCCESS or has been initiated recently
            # This is more reliable than just finding the "latest cart"
            
            # First, try to find a cart with a successful payment
            successful_payment = PaymentOrder.objects.filter(
                user=user, 
                status='SUCCESS'
            ).order_by('-created_at').first()
            
            target_cart = None
            
            if successful_payment:
                target_cart = Cart.objects.filter(cart_id=successful_payment.cart_id).first()
                logger.info(f"Found cart {target_cart.cart_id if target_cart else 'None'} with successful payment.")
            
            # If no successful payment, look for the most recent initiated payment
            # (user might have just completed payment but webhook hasn't processed yet)
            if not target_cart:
                recent_payment = PaymentOrder.objects.filter(
                    user=user,
                    status='INITIATED'
                ).order_by('-created_at').first()
                
                if recent_payment:
                    target_cart = Cart.objects.filter(cart_id=recent_payment.cart_id).first()
                    logger.info(f"Found cart {target_cart.cart_id if target_cart else 'None'} with recent initiated payment.")
            
            # Fallback: find latest cart
            if not target_cart:
                target_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
                logger.info(f"Fallback: using latest cart {target_cart.cart_id if target_cart else 'None'}.")

            if not target_cart:
                logger.error(f"No carts found for user {user.id}. Cannot proceed.")
                return JsonResponse({"error": "No cart found for user."}, status=404)

            logger.info(f"Selected target cart {target_cart.cart_id} (status: {target_cart.status}) for user {user.id}.")

            # 2. Verify a successful payment exists for this cart
            payment = PaymentOrder.objects.filter(cart_id=target_cart.cart_id, status='SUCCESS').order_by('-created_at').first()

            if not payment:
                logger.warning(f"No successful payment found in DB for cart {target_cart.cart_id}. Webhook might be delayed or payment failed.")
                # Even if payment not marked SUCCESS, a booking might have been created by a fast webhook.
                booking = Booking.objects.filter(cart=target_cart).first()
                if booking:
                    logger.info(f"Found existing booking {booking.book_id}. Proceeding with redirect.")
                    # Try to find any payment order for the redirect URL.
                    payment = PaymentOrder.objects.filter(cart_id=target_cart.cart_id).order_by('-created_at').first()
                else:
                    logger.error(f"CRITICAL: No successful payment and no booking for cart {target_cart.cart_id}. Cannot proceed.")
                    return JsonResponse({"error": "Payment not successful or webhook is delayed. Cannot find or create booking."}, status=400)

            if not payment:
                 logger.error(f"CRITICAL: No payment object found for cart {target_cart.cart_id} even after finding a booking.")
                 return JsonResponse({"error": "Internal state inconsistency. Booking exists without a payment order."}, status=500)

            logger.info(f"Found payment {payment.merchant_order_id} (Status: {payment.status}) for cart {target_cart.cart_id}.")

            # 3. Check if a booking already exists for this cart
            booking = Booking.objects.filter(cart=target_cart).first()

            if booking:
                logger.info(f"Booking {booking.book_id} already exists for cart {target_cart.cart_id}. Redirecting.")
            else:
                # 4. If no booking exists, create one (should only happen if redirect is faster than webhook)
                logger.warning(f"No booking found for cart {target_cart.cart_id}. Attempting to create one now.")
                try:
                    webhook_service = WebhookService()
                    booking = webhook_service._create_booking_from_cart(target_cart)
                    if not booking:
                         raise Exception("Booking creation failed in redirect handler.")
                    logger.info(f"Successfully created new booking {booking.book_id} via redirect handler.")
                except Exception as e:
                    logger.error(f"Error creating booking from cart {target_cart.cart_id} in redirect: {e}")
                    logger.error(traceback.format_exc())
                    return JsonResponse({"error": "Failed to create booking after successful payment."}, status=500)

            # 5. Redirect to the frontend confirmation page
            redirect_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}&redirect_source=phonepe"
            logger.info(f"Redirecting user to: {redirect_url}")
            
            return redirect(redirect_url)

        except Exception as e:
            logger.error(f"An unexpected error occurred in SimpleRedirectView for user {user.id}: {e}")
            logger.error(traceback.format_exc())
            return JsonResponse({"error": "An unexpected server error occurred."}, status=500)
