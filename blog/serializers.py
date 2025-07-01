from rest_framework import serializers
from .models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView
from accounts.serializers import UserSerializer

class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = [
            'id', 'name', 'slug', 'description', 
            'meta_title', 'meta_keywords', 'meta_description',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTag
        fields = [
            'id', 'name', 'slug', 'description',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

class BlogPostListSerializer(serializers.ModelSerializer):
    author = UserSerializer(source='user', read_only=True)
    category = BlogCategorySerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    featured_image_thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'excerpt', 'author',
            'category', 'tags', 'featured_image_thumbnail_url',
            'status', 'is_featured', 'view_count',
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = fields

    def get_featured_image_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.featured_image_thumbnail and hasattr(obj.featured_image_thumbnail, 'url'):
            url = obj.featured_image_thumbnail.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

class BlogPostDetailSerializer(BlogPostListSerializer):
    class Meta(BlogPostListSerializer.Meta):
        fields = BlogPostListSerializer.Meta.fields + ['content', 'youtube_url']

class BlogCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogComment
        fields = [
            'id', 'user', 'content', 'is_approved',
            'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'replies']
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True)
        return BlogCommentSerializer(replies, many=True).data

class BlogLikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BlogLike
        fields = ['id', 'user', 'created_at']
        read_only_fields = fields

class BlogViewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BlogView
        fields = ['id', 'user', 'ip_address', 'created_at']
        read_only_fields = fields