from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    # Categories
    path('categories/', views.BlogCategoryListCreateView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.BlogCategoryDetailView.as_view(), name='category-detail'),
    
    # Tags
    path('tags/', views.BlogTagListCreateView.as_view(), name='tag-list'),
    path('tags/<slug:slug>/', views.BlogTagDetailView.as_view(), name='tag-detail'),
    
    # Posts
    path('posts/', views.BlogPostListView.as_view(), name='post-list'),
    path('posts/create/', views.BlogPostCreateView.as_view(), name='post-create'),
    path('posts/<slug:slug>/', views.BlogPostDetailView.as_view(), name='post-detail'),
    path('posts/popular/', views.BlogPopularPostsView.as_view(), name='popular-posts'),
    path('posts/<slug:post_slug>/related/', views.BlogRelatedPostsView.as_view(), name='related-posts'),
    
    # Comments
    path('posts/<slug:post_slug>/comments/', views.BlogCommentListView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', views.BlogCommentDetailView.as_view(), name='comment-detail'),
    
    # Likes
    path('posts/<slug:post_slug>/like/', views.BlogLikeView.as_view(), name='post-like'),
]

urlpatterns += router.urls