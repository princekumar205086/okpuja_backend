from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from django.utils import timezone

from .models import PromoCode, PromoCodeUsage
from .serializers import (
    PromoCodeSerializer,
    PromoCodeCreateSerializer,
    PromoCodeUsageSerializer,
    ValidatePromoCodeSerializer,
    BulkCreatePromoCodeSerializer
)

class PromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.all().prefetch_related('usages')
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['code_type', 'is_active', 'discount_type']
    search_fields = ['code', 'description']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PromoCodeCreateSerializer
        if self.action == 'bulk_create':
            return BulkCreatePromoCodeSerializer
        return PromoCodeSerializer

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            created = serializer.save()
        
        return Response({
            'status': 'success',
            'created': len(created),
            'codes': [promo.code for promo in created]
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = PromoCode.objects.aggregate(
            total_codes=Count('id'),
            active_codes=Count('id', filter=Q(is_active=True)),
            total_uses=Sum('used_count')
        )
        return Response(stats)

    @action(detail=False, methods=['get'])
    def export(self, request):
        import csv
        from io import StringIO
        
        buffer = StringIO()
        writer = csv.writer(buffer)
        
        writer.writerow(['Code', 'Discount', 'Type', 'Usage Count'])
        for promo in self.get_queryset():
            writer.writerow([
                promo.code,
                promo.discount,
                promo.get_discount_type_display(),
                promo.used_count
            ])
        
        response = HttpResponse(buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="promo_codes.csv"'
        return response

class PublicPromoCodeViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = PromoCode.objects.filter(is_active=True)
    serializer_class = PromoCodeSerializer
    permission_classes = []

    @action(detail=False, methods=['get'])
    def validate(self, request):
        serializer = ValidatePromoCodeSerializer(
            data=request.query_params,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        promo_code = serializer.validated_data['promo_code']
        amount = serializer.validated_data.get('amount', 0)
        
        discounted_amount = promo_code.apply_discount(amount)
        
        return Response({
            'promo_code': self.get_serializer(promo_code).data,
            'original_amount': amount,
            'discounted_amount': discounted_amount,
            'discount_amount': amount - discounted_amount
        })

class UserPromoCodeViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PromoCode.objects.none()
        return PromoCode.objects.filter(
            code_type=PromoCode.CODE_TYPES.PUBLIC,
            is_active=True,
            expiry_date__gte=timezone.now()
        ).distinct()

    @action(detail=False, methods=['get'])
    def history(self, request):
        usages = PromoCodeUsage.objects.filter(
            user=request.user
        ).select_related('promo_code')
        
        page = self.paginate_queryset(usages)
        serializer = PromoCodeUsageSerializer(page or usages, many=True)
        
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)