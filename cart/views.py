# cart/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import ProtectedError
from django.utils import timezone
from .models import Cart
from .serializers import CartSerializer, CartCreateSerializer
from promo.models import PromoCode

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CartCreateSerializer
        return CartSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to handle protected foreign keys gracefully with auto-cleanup"""
        cart = self.get_object()
        
        try:
            # Try auto-cleanup first
            cleanup_result = cart.auto_cleanup_old_payments()
            
            # Get detailed deletion info
            deletion_info = cart.get_deletion_info()
            
            if not deletion_info["can_delete"]:
                if deletion_info["reason"] == "pending_payment_wait":
                    return Response({
                        'error': 'Cannot delete cart with recent pending payments',
                        'detail': deletion_info["message"],
                        'can_delete': False,
                        'wait_time_minutes': deletion_info["wait_time_minutes"],
                        'retry_after': deletion_info["retry_after"],
                        'payment_count': deletion_info["payment_count"],
                        'latest_payment_age_minutes': deletion_info["latest_payment_age_minutes"],
                        'auto_cleanup': cleanup_result if cleanup_result["cleaned_up"] else None
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'error': 'Cannot delete cart',
                        'detail': deletion_info.get("message", deletion_info["reason"]),
                        'can_delete': False,
                        'reason': deletion_info["reason"]
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # If cart can be deleted, proceed with cleanup
            response_data = {
                'message': 'Cart deleted successfully',
                'deleted_cart_id': cart.cart_id
            }
            
            # Include cleanup info if any payments were auto-cancelled
            if cleanup_result["cleaned_up"]:
                response_data['auto_cleanup'] = cleanup_result
            
            # If cart is converted, clear payments reference first
            if cart.status == Cart.StatusChoices.CONVERTED:
                from payment.models import Payment
                Payment.objects.filter(cart=cart).update(cart=None)
            
            cart.delete()
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ProtectedError as e:
            return Response({
                'error': 'Cannot delete cart',
                'detail': 'Cart has protected references that prevent deletion',
                'can_delete': False,
                'technical_details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Unexpected error during cart deletion',
                'detail': str(e),
                'can_delete': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get user's active cart (single cart system)"""
        active_cart = self.get_queryset().filter(status='ACTIVE').first()
        if active_cart:
            serializer = self.get_serializer(active_cart)
            return Response(serializer.data)
        return Response({'detail': 'No active cart found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def clear_converted(self, request):
        """Clear all converted carts for the user"""
        converted_carts = self.get_queryset().filter(status='CONVERTED')
        cleared_count = 0
        
        for cart in converted_carts:
            if cart.clear_if_converted():
                cleared_count += 1
        
        return Response({
            'message': f'{cleared_count} converted carts cleared',
            'cleared_count': cleared_count
        })

    @action(detail=True, methods=['post'])
    def apply_promo(self, request, pk=None):
        cart = self.get_object()
        promo_code = request.data.get('promo_code')
        
        if not promo_code:
            return Response(
                {'error': 'Promo code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            promo = PromoCode.objects.get(code=promo_code, is_active=True)
            cart.promo_code = promo
            cart.save()
            return Response(self.get_serializer(cart).data)
        except PromoCode.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired promo code'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def remove_promo(self, request, pk=None):
        cart = self.get_object()
        cart.promo_code = None
        cart.save()
        return Response(self.get_serializer(cart).data)

    @action(detail=True, methods=['post'])
    def cleanup_old_payments(self, request, pk=None):
        """Manually trigger cleanup of old pending payments for this cart"""
        cart = self.get_object()
        
        # Perform auto-cleanup
        cleanup_result = cart.auto_cleanup_old_payments()
        
        # Get updated deletion info
        deletion_info = cart.get_deletion_info()
        
        response_data = {
            'cleanup_performed': cleanup_result["cleaned_up"],
            'payments_cancelled': cleanup_result["payments_cancelled"],
            'message': cleanup_result.get("message", "No old payments to cleanup"),
            'can_delete_now': deletion_info["can_delete"],
            'deletion_info': deletion_info
        }
        
        if cleanup_result["cleaned_up"]:
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def deletion_status(self, request, pk=None):
        """Check if cart can be deleted and get detailed timing information"""
        cart = self.get_object()
        from payment.models import Payment, PaymentStatus
        
        # Get detailed deletion information
        deletion_info = cart.get_deletion_info()
        
        # Get payment summary
        payments = Payment.objects.filter(cart=cart)
        payment_summary = []
        
        for payment in payments:
            payment_summary.append({
                'transaction_id': payment.transaction_id,
                'status': payment.status,
                'amount': str(payment.amount),
                'created_at': payment.created_at,
                'age_minutes': int((timezone.now() - payment.created_at).total_seconds() / 60),
                'has_booking': bool(payment.booking)
            })
        
        # Check if auto-cleanup can be performed
        cleanup_available = False
        if not deletion_info["can_delete"]:
            cleanup_result = cart.auto_cleanup_old_payments()
            if cleanup_result["cleaned_up"]:
                cleanup_available = True
                deletion_info = cart.get_deletion_info()  # Refresh after cleanup
        
        response_data = {
            'can_delete': deletion_info["can_delete"],
            'cart_status': cart.status,
            'payments_count': payments.count(),
            'payments': payment_summary,
            'deletion_info': deletion_info
        }
        
        if cleanup_available:
            response_data['auto_cleanup_performed'] = cleanup_result
        
        return Response(response_data)
    
    def _get_deletion_reasons(self, cart, payments):
        """Get reasons why cart cannot be deleted"""
        reasons = []
        
        if not payments.exists():
            reasons.append("No payments - can delete safely")
            return reasons
        
        from payment.models import PaymentStatus
        pending_payments = payments.filter(status=PaymentStatus.PENDING)
        failed_payments = payments.filter(status__in=[PaymentStatus.FAILED, PaymentStatus.CANCELLED])
        successful_payments = payments.filter(status=PaymentStatus.SUCCESS)
        
        if pending_payments.exists():
            reasons.append(f"{pending_payments.count()} pending payments prevent deletion")
        
        if failed_payments.exists():
            reasons.append(f"{failed_payments.count()} failed/cancelled payments can be cleared")
        
        if successful_payments.exists():
            with_booking = successful_payments.filter(booking__isnull=False).count()
            without_booking = successful_payments.filter(booking__isnull=True).count()
            
            if with_booking > 0:
                reasons.append(f"{with_booking} successful payments with bookings - references can be cleared")
            if without_booking > 0:
                reasons.append(f"{without_booking} successful payments without bookings - need investigation")
        
        return reasons

    def create(self, request, *args, **kwargs):
        """Create cart and return full cart details (single cart system)"""
        # For single cart system, deactivate any existing active carts
        Cart.objects.filter(
            user=request.user, 
            status=Cart.StatusChoices.ACTIVE
        ).update(status=Cart.StatusChoices.INACTIVE)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = serializer.save(user=request.user)
        
        # Return full cart details using the read serializer
        response_serializer = CartSerializer(cart)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)