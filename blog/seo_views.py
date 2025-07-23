from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.syndication.views import Feed
from django.urls import reverse
from datetime import timedelta
import xml.etree.ElementTree as ET

from .models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView
from .seo_serializers import (
    SEOBlogCategorySerializer,
    SEOBlogTagSerializer,
    EnterpriseMinimalBlogPostSerializer,
    EnterpriseBlogPostDetailSerializer,
    SEOBlogCommentSerializer,
    BlogLikeSerializer,
    BlogViewSerializer,
    BlogAnalyticsSerializer
)

class BlogCategoryViewSet(viewsets.ModelViewSet):
    """Enhanced category viewset with SEO optimization"""
    serializer_class = SEOBlogCategorySerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return BlogCategory.objects.filter(status='PUBLISHED').annotate(
            post_count=Count('posts', filter=Q(posts__status='PUBLISHED'))
        )
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts for a specific category"""
        category = self.get_object()
        posts = BlogPost.objects.filter(
            category=category,
            status='PUBLISHED'
        ).select_related('user', 'category').prefetch_related('tags')
        
        serializer = EnterpriseMinimalBlogPostSerializer(
            posts, many=True, context={'request': request}
        )
        return Response(serializer.data)

class BlogTagViewSet(viewsets.ModelViewSet):
    """Enhanced tag viewset with SEO optimization"""
    serializer_class = SEOBlogTagSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return BlogTag.objects.filter(status='PUBLISHED').annotate(
            post_count=Count('posts', filter=Q(posts__status='PUBLISHED'))
        )
    
    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts for a specific tag"""
        tag = self.get_object()
        posts = BlogPost.objects.filter(
            tags=tag,
            status='PUBLISHED'
        ).select_related('user', 'category').prefetch_related('tags')
        
        serializer = EnterpriseMinimalBlogPostSerializer(
            posts, many=True, context={'request': request}
        )
        return Response(serializer.data)

class BlogPostViewSet(viewsets.ModelViewSet):
    """Enterprise-level blog post viewset with full SEO optimization"""
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EnterpriseBlogPostDetailSerializer
        return EnterpriseMinimalBlogPostSerializer
    
    def get_queryset(self):
        queryset = BlogPost.objects.filter(status='PUBLISHED').select_related(
            'user', 'category'
        ).prefetch_related(
            'tags',
            Prefetch('comments', queryset=BlogComment.objects.filter(is_approved=True)),
            'likes'
        ).annotate(
            like_count=Count('likes'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True))
        )
        
        # Filter by category
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by tag
        tag_slug = self.request.query_params.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Filter by author
        user_id = self.request.query_params.get('author')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(meta_keywords__icontains=search)
            )
        
        return queryset.order_by('-published_at', '-created_at')
    
    def retrieve(self, request, *args, **kwargs):
        """Enhanced retrieve with view tracking"""
        instance = self.get_object()
        
        # Track view
        user = request.user if request.user.is_authenticated else None
        ip_address = self.get_client_ip(request)
        
        # Create view record (avoid duplicates within 24 hours for same IP)
        if not BlogView.objects.filter(
            post=instance,
            ip_address=ip_address,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).exists():
            BlogView.objects.create(
                post=instance,
                user=user,
                ip_address=ip_address
            )
            # Update view count
            instance.view_count += 1
            instance.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=True, methods=['post'])
    def like(self, request, slug=None):
        """Like/Unlike a blog post"""
        post = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        like, created = BlogLike.objects.get_or_create(post=post, user=user)
        
        if not created:
            like.delete()
            return Response({'liked': False, 'message': 'Like removed'})
        
        return Response({'liked': True, 'message': 'Post liked'})
    
    @action(detail=True, methods=['get'])
    def comments(self, request, slug=None):
        """Get comments for a blog post"""
        post = self.get_object()
        comments = post.comments.filter(
            is_approved=True, 
            parent_comment__isnull=True
        ).select_related('user').order_by('-created_at')
        
        serializer = SEOBlogCommentSerializer(
            comments, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """Get related blog posts"""
        post = self.get_object()
        
        related_posts = BlogPost.objects.filter(
            status='PUBLISHED'
        ).filter(
            Q(category=post.category) | Q(tags__in=post.tags.all())
        ).exclude(id=post.id).distinct().select_related(
            'user', 'category'
        ).prefetch_related('tags')[:5]
        
        serializer = EnterpriseMinimalBlogPostSerializer(
            related_posts, many=True, context={'request': request}
        )
        return Response(serializer.data)

class BlogPostBySlugView(RetrieveAPIView):
    """Dedicated view for retrieving blog posts by slug for SEO URLs"""
    serializer_class = EnterpriseBlogPostDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return BlogPost.objects.filter(status='PUBLISHED').select_related(
            'user', 'category'
        ).prefetch_related('tags', 'comments', 'likes')

class BlogCommentViewSet(viewsets.ModelViewSet):
    """Enhanced comment viewset with moderation"""
    serializer_class = SEOBlogCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return BlogComment.objects.filter(is_approved=True).select_related(
            'user', 'post'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BlogLikeViewSet(viewsets.ReadOnlyModelViewSet):
    """Blog like viewset"""
    serializer_class = BlogLikeSerializer
    
    def get_queryset(self):
        return BlogLike.objects.all().select_related('user', 'post')

class BlogViewViewSet(viewsets.ReadOnlyModelViewSet):
    """Blog view tracking viewset"""
    serializer_class = BlogViewSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return BlogView.objects.all().select_related('user', 'post')

class BlogSearchView(ListAPIView):
    """Advanced blog search with SEO optimization"""
    serializer_class = EnterpriseMinimalBlogPostSerializer
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        
        if not query:
            return BlogPost.objects.none()
        
        return BlogPost.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(meta_keywords__icontains=query) |
            Q(category__name__icontains=query) |
            Q(tags__name__icontains=query)
        ).filter(status='PUBLISHED').distinct().select_related(
            'user', 'category'
        ).prefetch_related('tags').order_by('-published_at')

class TrendingBlogPostsView(ListAPIView):
    """Get trending blog posts based on views and engagement"""
    serializer_class = EnterpriseMinimalBlogPostSerializer
    
    def get_queryset(self):
        # Posts with high engagement in the last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        
        return BlogPost.objects.filter(
            status='PUBLISHED',
            published_at__gte=week_ago
        ).annotate(
            recent_views=Count('views', filter=Q(views__created_at__gte=week_ago)),
            like_count=Count('likes'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True))
        ).order_by('-recent_views', '-like_count', '-comment_count')[:10]

class RelatedBlogPostsView(ListAPIView):
    """Get related posts for a specific blog post"""
    serializer_class = EnterpriseMinimalBlogPostSerializer
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        
        try:
            post = BlogPost.objects.get(id=post_id)
        except BlogPost.DoesNotExist:
            return BlogPost.objects.none()
        
        return BlogPost.objects.filter(
            status='PUBLISHED'
        ).filter(
            Q(category=post.category) | Q(tags__in=post.tags.all())
        ).exclude(id=post.id).distinct().select_related(
            'user', 'category'
        ).prefetch_related('tags')[:5]

class BlogSitemapView(APIView):
    """Generate XML sitemap for blog posts"""
    
    def get(self, request):
        posts = BlogPost.objects.filter(status='PUBLISHED').order_by('-updated_at')
        
        # Create XML sitemap
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Add blog index
        url = ET.SubElement(urlset, 'url')
        ET.SubElement(url, 'loc').text = request.build_absolute_uri('/blog/')
        ET.SubElement(url, 'changefreq').text = 'daily'
        ET.SubElement(url, 'priority').text = '0.8'
        
        # Add individual posts
        for post in posts:
            url = ET.SubElement(urlset, 'url')
            ET.SubElement(url, 'loc').text = request.build_absolute_uri(f'/blog/{post.slug}/')
            ET.SubElement(url, 'lastmod').text = post.updated_at.strftime('%Y-%m-%d')
            ET.SubElement(url, 'changefreq').text = 'weekly'
            ET.SubElement(url, 'priority').text = '0.6'
        
        xml_content = ET.tostring(urlset, encoding='unicode')
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content
        
        return HttpResponse(xml_content, content_type='application/xml')

class BlogRSSFeedView(Feed):
    """RSS feed for blog posts"""
    title = "OkPuja Blog - Hindu Spiritual Services"
    link = "/blog/"
    description = "Latest spiritual insights, puja guides, and Hindu traditions from OkPuja"
    
    def items(self):
        return BlogPost.objects.filter(status='PUBLISHED').order_by('-published_at')[:20]
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        return item.excerpt or item.content[:200] + '...'
    
    def item_link(self, item):
        return f'/blog/{item.slug}/'
    
    def item_pubdate(self, item):
        return item.published_at or item.created_at

class BlogAnalyticsView(APIView):
    """Blog analytics and performance data"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        # Get time range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Overall stats
        total_posts = BlogPost.objects.filter(status='PUBLISHED').count()
        total_views = BlogView.objects.filter(created_at__gte=start_date).count()
        total_likes = BlogLike.objects.filter(created_at__gte=start_date).count()
        total_comments = BlogComment.objects.filter(
            is_approved=True, 
            created_at__gte=start_date
        ).count()
        
        # Top performing posts
        top_posts = BlogPost.objects.filter(
            status='PUBLISHED'
        ).annotate(
            recent_views=Count('views', filter=Q(views__created_at__gte=start_date))
        ).order_by('-recent_views')[:10]
        
        top_posts_data = BlogAnalyticsSerializer(
            top_posts, many=True, context={'request': request}
        ).data
        
        # Category performance
        category_stats = BlogCategory.objects.filter(
            status='PUBLISHED'
        ).annotate(
            post_count=Count('posts', filter=Q(posts__status='PUBLISHED')),
            total_views=Count('posts__views', filter=Q(posts__views__created_at__gte=start_date))
        ).values('name', 'post_count', 'total_views')
        
        return Response({
            'overview': {
                'total_posts': total_posts,
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'date_range': f'{days} days'
            },
            'top_posts': top_posts_data,
            'category_performance': list(category_stats)
        })

# Backward compatibility
BlogCategoryListView = BlogCategoryViewSet
BlogTagListView = BlogTagViewSet
BlogPostListView = BlogPostViewSet
BlogPostDetailView = BlogPostBySlugView
