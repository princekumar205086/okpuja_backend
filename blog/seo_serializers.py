from rest_framework import serializers
from django.template.defaultfilters import truncatewords
from .models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView
from accounts.serializers import UserSerializer

class SEOBlogCategorySerializer(serializers.ModelSerializer):
    """Enhanced category serializer with SEO fields"""
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogCategory
        fields = [
            'id', 'name', 'slug', 'description', 
            'meta_title', 'meta_keywords', 'meta_description',
            'status', 'created_at', 'updated_at', 'post_count'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'post_count']
    
    def get_post_count(self, obj):
        return obj.posts.filter(status='PUBLISHED').count()

class SEOBlogTagSerializer(serializers.ModelSerializer):
    """Enhanced tag serializer with SEO fields"""
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogTag
        fields = [
            'id', 'name', 'slug', 'description',
            'status', 'created_at', 'updated_at', 'post_count'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'post_count']
    
    def get_post_count(self, obj):
        return obj.posts.filter(status='PUBLISHED').count()

class EnterpriseMinimalBlogPostSerializer(serializers.ModelSerializer):
    """Minimal serializer for blog post listings with SEO optimization"""
    author = serializers.CharField(source='user.get_full_name', read_only=True)
    author_avatar = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    tag_names = serializers.SerializerMethodField()
    featured_image_url = serializers.SerializerMethodField()
    featured_image_alt = serializers.SerializerMethodField()
    reading_time = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    canonical_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'excerpt', 'author', 'author_avatar',
            'category_name', 'category_slug', 'tag_names', 
            'featured_image_url', 'featured_image_alt', 'reading_time',
            'view_count', 'like_count', 'comment_count',
            'is_featured', 'published_at', 'canonical_url'
        ]
        read_only_fields = fields
    
    def get_author_avatar(self, obj):
        # Placeholder for future user avatar implementation
        return None
    
    def get_tag_names(self, obj):
        return [tag.name for tag in obj.tags.filter(status='PUBLISHED')]
    
    def get_featured_image_url(self, obj):
        request = self.context.get('request')
        if obj.featured_image_thumbnail and hasattr(obj.featured_image_thumbnail, 'url'):
            url = obj.featured_image_thumbnail.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None
    
    def get_featured_image_alt(self, obj):
        # Generate SEO-friendly alt text
        return f"{obj.title} - {obj.category.name if obj.category else 'Blog'} | OkPuja"
    
    def get_reading_time(self, obj):
        """Calculate reading time based on content length"""
        word_count = len(obj.content.split())
        # Average reading speed: 200 words per minute
        reading_time = max(1, round(word_count / 200))
        return reading_time
    
    def get_like_count(self, obj):
        return getattr(obj, 'like_count', obj.likes.count())
    
    def get_comment_count(self, obj):
        return obj.comments.filter(is_approved=True).count()
    
    def get_canonical_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/blog/{obj.slug}/')
        return f'/blog/{obj.slug}/'

class EnterpriseBlogPostDetailSerializer(EnterpriseMinimalBlogPostSerializer):
    """Detailed blog post serializer with full SEO optimization"""
    content = serializers.CharField(read_only=True)
    youtube_url = serializers.URLField(read_only=True)
    meta_title = serializers.CharField(read_only=True)
    meta_description = serializers.CharField(read_only=True)
    meta_keywords = serializers.CharField(read_only=True)
    structured_data = serializers.SerializerMethodField()
    open_graph_data = serializers.SerializerMethodField()
    twitter_card_data = serializers.SerializerMethodField()
    breadcrumbs = serializers.SerializerMethodField()
    table_of_contents = serializers.SerializerMethodField()
    
    class Meta(EnterpriseMinimalBlogPostSerializer.Meta):
        fields = EnterpriseMinimalBlogPostSerializer.Meta.fields + [
            'content', 'youtube_url', 'meta_title', 'meta_description', 
            'meta_keywords', 'structured_data', 'open_graph_data', 
            'twitter_card_data', 'breadcrumbs', 'table_of_contents'
        ]
    
    def get_structured_data(self, obj):
        """Generate JSON-LD structured data for the blog post"""
        request = self.context.get('request')
        base_url = request.build_absolute_uri('/') if request else 'https://okpuja.com/'
        
        return {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": obj.title,
            "description": obj.excerpt or truncatewords(obj.content, 30),
            "image": self.get_featured_image_url(obj),
            "author": {
                "@type": "Person",
                "name": obj.user.get_full_name() or obj.user.email,
                "url": f"{base_url}author/{obj.user.id}/"
            },
            "publisher": {
                "@type": "Organization",
                "name": "OkPuja",
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{base_url}static/images/okpuja-logo.png"
                }
            },
            "datePublished": obj.published_at.isoformat() if obj.published_at else obj.created_at.isoformat(),
            "dateModified": obj.updated_at.isoformat(),
            "url": self.get_canonical_url(obj),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": self.get_canonical_url(obj)
            },
            "keywords": obj.meta_keywords or ', '.join(self.get_tag_names(obj)),
            "wordCount": len(obj.content.split()),
            "timeRequired": f"PT{self.get_reading_time(obj)}M",
            "articleSection": obj.category.name if obj.category else "Spirituality",
            "inLanguage": "en-US"
        }
    
    def get_open_graph_data(self, obj):
        """Generate Open Graph meta tags data"""
        return {
            "og:type": "article",
            "og:title": obj.meta_title or obj.title,
            "og:description": obj.meta_description or obj.excerpt or truncatewords(obj.content, 30),
            "og:image": self.get_featured_image_url(obj),
            "og:url": self.get_canonical_url(obj),
            "og:site_name": "OkPuja - Hindu Spiritual Services",
            "article:author": obj.user.get_full_name() or obj.user.email,
            "article:published_time": obj.published_at.isoformat() if obj.published_at else obj.created_at.isoformat(),
            "article:modified_time": obj.updated_at.isoformat(),
            "article:section": obj.category.name if obj.category else "Spirituality",
            "article:tag": ', '.join(self.get_tag_names(obj))
        }
    
    def get_twitter_card_data(self, obj):
        """Generate Twitter Card meta tags data"""
        return {
            "twitter:card": "summary_large_image",
            "twitter:site": "@OkPuja",
            "twitter:creator": f"@{obj.user.username}" if hasattr(obj.user, 'username') else "@OkPuja",
            "twitter:title": obj.meta_title or obj.title,
            "twitter:description": obj.meta_description or obj.excerpt or truncatewords(obj.content, 30),
            "twitter:image": self.get_featured_image_url(obj),
            "twitter:url": self.get_canonical_url(obj)
        }
    
    def get_breadcrumbs(self, obj):
        """Generate breadcrumb navigation data"""
        breadcrumbs = [
            {"name": "Home", "url": "/"},
            {"name": "Blog", "url": "/blog/"}
        ]
        
        if obj.category:
            breadcrumbs.append({
                "name": obj.category.name,
                "url": f"/blog/category/{obj.category.slug}/"
            })
        
        breadcrumbs.append({
            "name": obj.title,
            "url": f"/blog/{obj.slug}/",
            "current": True
        })
        
        return breadcrumbs
    
    def get_table_of_contents(self, obj):
        """Extract table of contents from content headings"""
        import re
        
        # Extract headings from markdown/HTML content
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        headings = []
        
        for line in obj.content.split('\n'):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                slug = re.sub(r'[^a-zA-Z0-9\s]', '', title).replace(' ', '-').lower()
                
                headings.append({
                    "level": level,
                    "title": title,
                    "slug": slug,
                    "url": f"#{slug}"
                })
        
        return headings

class SEOBlogCommentSerializer(serializers.ModelSerializer):
    """Enhanced comment serializer with moderation features"""
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogComment
        fields = [
            'id', 'user', 'content', 'is_approved', 'is_author',
            'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'replies', 'is_author']
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True).order_by('created_at')
        return SEOBlogCommentSerializer(replies, many=True, context=self.context).data
    
    def get_is_author(self, obj):
        """Check if comment is from the blog post author"""
        return obj.user == obj.post.user

class BlogAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for blog analytics and performance data"""
    daily_views = serializers.SerializerMethodField()
    referrer_data = serializers.SerializerMethodField()
    engagement_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'view_count', 'daily_views',
            'referrer_data', 'engagement_rate', 'published_at'
        ]
        read_only_fields = fields
    
    def get_daily_views(self, obj):
        """Get view count for the last 30 days"""
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return obj.views.filter(created_at__gte=thirty_days_ago).count()
    
    def get_referrer_data(self, obj):
        """Get top referrer sources (placeholder for future implementation)"""
        return {
            "google": 45,
            "direct": 30,
            "social": 15,
            "other": 10
        }
    
    def get_engagement_rate(self, obj):
        """Calculate engagement rate based on likes and comments"""
        if obj.view_count == 0:
            return 0
        
        engagements = obj.likes.count() + obj.comments.filter(is_approved=True).count()
        return round((engagements / obj.view_count) * 100, 2)

# Backward compatibility with existing serializers
BlogCategorySerializer = SEOBlogCategorySerializer
BlogTagSerializer = SEOBlogTagSerializer
BlogPostListSerializer = EnterpriseMinimalBlogPostSerializer
BlogPostDetailSerializer = EnterpriseBlogPostDetailSerializer
BlogCommentSerializer = SEOBlogCommentSerializer

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
