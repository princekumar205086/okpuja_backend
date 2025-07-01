from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import GalleryCategory, GalleryItem, GalleryView
from .serializers import (
    GalleryCategorySerializer,
    GalleryItemListSerializer,
    GalleryItemDetailSerializer,
    GalleryViewSerializer
)
from core.permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly

class GalleryCategoryListView(generics.ListAPIView):
    queryset = GalleryCategory.objects.filter(status='PUBLISHED')
    serializer_class = GalleryCategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

class GalleryCategoryDetailView(generics.RetrieveAPIView):
    queryset = GalleryCategory.objects.all()
    serializer_class = GalleryCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

class GalleryItemListView(generics.ListAPIView):
    serializer_class = GalleryItemListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'status', 'is_featured']
    
    def get_queryset(self):
        return GalleryItem.objects.filter(status='PUBLISHED').select_related('category')

class GalleryItemDetailView(generics.RetrieveAPIView):
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemDetailSerializer
    permission_classes = [permissions.AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Record view
        GalleryView.objects.create(
            item=instance,
            user=request.user if request.user.is_authenticated else None,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Increment popularity
        instance.increment_popularity()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class FeaturedGalleryItemsView(generics.ListAPIView):
    serializer_class = GalleryItemListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return GalleryItem.objects.filter(
            status='PUBLISHED',
            is_featured=True
        ).order_by('-popularity')[:12]

class GalleryCategoryItemsView(generics.ListAPIView):
    serializer_class = GalleryItemListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        category_slug = self.kwargs['slug']
        category = get_object_or_404(GalleryCategory, slug=category_slug)
        return GalleryItem.objects.filter(
            category=category,
            status='PUBLISHED'
        ).order_by('-is_featured', '-popularity')

class GalleryUploadView(generics.CreateAPIView):
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save()

class GalleryAdminListView(generics.ListAPIView):
    serializer_class = GalleryItemDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'status', 'is_featured']
    
    def get_queryset(self):
        return GalleryItem.objects.all().select_related('category')

class GalleryAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemDetailSerializer
    permission_classes = [permissions.IsAdminUser]