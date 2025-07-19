# cart/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import ProtectedError
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
        """Override destroy to handle protected foreign keys gracefully"""
        cart = self.get_object()
        
        try:
            # Check if cart can be safely deleted
            if not cart.can_be_deleted():
                return Response({
                    'error': 'Cannot delete cart with pending payments',
                    'detail': 'This cart has pending payments. Please wait for payment completion or cancellation.',
                    'can_delete': False
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If cart is converted, clear payments reference first
            if cart.status == Cart.StatusChoices.CONVERTED:
                from payment.models import Payment
                Payment.objects.filter(cart=cart).update(cart=None)
            
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except ProtectedError as e:
            return Response({
                'error': 'Cannot delete cart',
                'detail': str(e),
                'can_delete': False
            }, status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=True, methods=['get'])
    def deletion_status(self, request, pk=None):
        """Check if cart can be deleted and get related payment info"""
        cart = self.get_object()
        from payment.models import Payment, PaymentStatus
        
        payments = Payment.objects.filter(cart=cart)
        payment_summary = []
        
        for payment in payments:
            payment_summary.append({
                'transaction_id': payment.transaction_id,
                'status': payment.status,
                'amount': str(payment.amount),
                'created_at': payment.created_at,
                'has_booking': bool(payment.booking)
            })
        
        return Response({
            'can_delete': cart.can_be_deleted(),
            'cart_status': cart.status,
            'payments_count': payments.count(),
            'payments': payment_summary,
            'reasons': self._get_deletion_reasons(cart, payments)
        })
    
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