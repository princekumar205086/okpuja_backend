from rest_framework import serializers
from .models import GalleryCategory, GalleryItem, GalleryView
from accounts.serializers import UserSerializer

class GalleryCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryCategory
        fields = [
            'id', 'title', 'slug', 'description',
            'status', 'position', 'item_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'item_count', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        return obj.items.filter(status='PUBLISHED').count()

class GalleryItemListSerializer(serializers.ModelSerializer):
    category = GalleryCategorySerializer(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    medium_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GalleryItem
        fields = [
            'id', 'title', 'category', 'thumbnail_url', 'medium_url',
            'popularity', 'is_featured', 'status', 'created_at'
        ]
        read_only_fields = fields

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return self.context['request'].build_absolute_uri(obj.thumbnail.url)
        return None

    def get_medium_url(self, obj):
        if obj.medium:
            return self.context['request'].build_absolute_uri(obj.medium.url)
        return None

class GalleryItemDetailSerializer(GalleryItemListSerializer):
    large_url = serializers.SerializerMethodField()
    web_url = serializers.SerializerMethodField()
    original_url = serializers.SerializerMethodField()
    
    class Meta(GalleryItemListSerializer.Meta):
        fields = GalleryItemListSerializer.Meta.fields + [
            'description', 'large_url', 'web_url', 'original_url',
            'taken_at', 'updated_at'
        ]
    
    def get_large_url(self, obj):
        if obj.large:
            return self.context['request'].build_absolute_uri(obj.large.url)
        return None

    def get_web_url(self, obj):
        if obj.web_optimized:
            return self.context['request'].build_absolute_uri(obj.web_optimized.url)
        return None

    def get_original_url(self, obj):
        if obj.original_image:
            return self.context['request'].build_absolute_uri(obj.original_image.url)
        return None

class GalleryViewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = GalleryView
        fields = ['id', 'user', 'ip_address', 'created_at']
        read_only_fields = fields