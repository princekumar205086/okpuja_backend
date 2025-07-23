from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BlogCategoryViewSet,
    BlogTagViewSet,
    BlogPostViewSet,
    BlogCommentViewSet,
    BlogLikeViewSet,
    BlogViewViewSet,
    BlogSitemapView,
    BlogRSSFeedView,
    BlogAnalyticsView,
    BlogSearchView,
    TrendingBlogPostsView,
    RelatedBlogPostsView,
    BlogPostBySlugView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', BlogCategoryViewSet, basename='blog-category')
router.register(r'tags', BlogTagViewSet, basename='blog-tag')
router.register(r'posts', BlogPostViewSet, basename='blog-post')
router.register(r'comments', BlogCommentViewSet, basename='blog-comment')
router.register(r'likes', BlogLikeViewSet, basename='blog-like')
router.register(r'views', BlogViewViewSet, basename='blog-view')

# Enterprise SEO and performance URLs
urlpatterns = [
    # Main API routes
    path('api/', include(router.urls)),
    
    # SEO-optimized URLs
    path('post/<slug:slug>/', BlogPostBySlugView.as_view(), name='blog-post-by-slug'),
    path('search/', BlogSearchView.as_view(), name='blog-search'),
    path('trending/', TrendingBlogPostsView.as_view(), name='trending-posts'),
    path('related/<int:post_id>/', RelatedBlogPostsView.as_view(), name='related-posts'),
    
    # XML Sitemap for SEO
    path('sitemap.xml', BlogSitemapView.as_view(), name='blog-sitemap'),
    
    # RSS Feed
    path('feed/', BlogRSSFeedView.as_view(), name='blog-rss-feed'),
    path('rss/', BlogRSSFeedView.as_view(), name='blog-rss-feed-alt'),
    
    # Analytics and Performance
    path('analytics/', BlogAnalyticsView.as_view(), name='blog-analytics'),
    
    # Category and Tag SEO URLs
    path('category/<slug:slug>/', BlogPostViewSet.as_view({'get': 'list'}), name='blog-category-posts'),
    path('tag/<slug:slug>/', BlogPostViewSet.as_view({'get': 'list'}), name='blog-tag-posts'),
    
    # Author pages
    path('author/<int:user_id>/', BlogPostViewSet.as_view({'get': 'list'}), name='blog-author-posts'),
]
