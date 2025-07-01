# cart/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Cart
from .serializers import CartSerializer, CartCreateSerializer

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

    @action(detail=False, methods=['get'])
    def active(self, request):
        active_carts = self.get_queryset().filter(status='ACTIVE')
        serializer = self.get_serializer(active_carts, many=True)
        return Response(serializer.data)

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