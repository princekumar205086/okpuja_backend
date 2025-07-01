from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .models import BlogCategory, BlogTag, BlogPost, BlogComment, BlogLike, BlogView
from .serializers import (
    BlogCategorySerializer, BlogTagSerializer,
    BlogPostListSerializer, BlogPostDetailSerializer,
    BlogCommentSerializer, BlogLikeSerializer, BlogViewSerializer
)
from core.permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly

class BlogCategoryListCreateView(generics.ListCreateAPIView):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class BlogCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

class BlogTagListCreateView(generics.ListCreateAPIView):
    queryset = BlogTag.objects.all()
    serializer_class = BlogTagSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class BlogTagDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogTag.objects.all()
    serializer_class = BlogTagSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

class BlogPostListView(generics.ListAPIView):
    serializer_class = BlogPostListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'tags', 'status', 'is_featured']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['published_at', 'created_at', 'view_count']
    ordering = ['-published_at']

    def get_queryset(self):
        queryset = BlogPost.objects.filter(status='PUBLISHED')
        
        # For admin users, show all posts
        if self.request.user.is_staff:
            queryset = BlogPost.objects.all()
        
        return queryset.select_related('user', 'category').prefetch_related('tags')

class BlogPostCreateView(generics.CreateAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostDetailSerializer
    lookup_field = 'slug'
    permission_classes = [IsOwnerOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        if instance.status == 'PUBLISHED':
            BlogView.objects.create(
                post=instance,
                user=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request)
            )
            instance.increment_view_count()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class BlogCommentListView(generics.ListCreateAPIView):
    serializer_class = BlogCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        post_slug = self.kwargs['post_slug']
        post = get_object_or_404(BlogPost, slug=post_slug)
        return BlogComment.objects.filter(
            post=post, 
            parent__isnull=True,
            is_approved=True
        ).select_related('user')

    def perform_create(self, serializer):
        post_slug = self.kwargs['post_slug']
        post = get_object_or_404(BlogPost, slug=post_slug)
        
        # Auto-approve comments from staff users
        is_approved = self.request.user.is_staff
        
        serializer.save(
            post=post,
            user=self.request.user,
            is_approved=is_approved
        )

class BlogCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogComment.objects.all()
    serializer_class = BlogCommentSerializer
    permission_classes = [IsOwnerOrReadOnly]

class BlogLikeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_slug):
        post = get_object_or_404(BlogPost, slug=post_slug)
        like, created = BlogLike.objects.get_or_create(
            post=post,
            user=request.user
        )
        
        if not created:
            like.delete()
            return Response(
                {'status': 'unliked'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'status': 'liked'},
            status=status.HTTP_201_CREATED
        )

class BlogPopularPostsView(generics.ListAPIView):
    serializer_class = BlogPostListSerializer

    def get_queryset(self):
        return BlogPost.objects.filter(status='PUBLISHED') \
            .annotate(like_count=Count('likes')) \
            .order_by('-view_count', '-like_count')[:5]

class BlogRelatedPostsView(generics.ListAPIView):
    serializer_class = BlogPostListSerializer

    def get_queryset(self):
        post_slug = self.kwargs['post_slug']
        post = get_object_or_404(BlogPost, slug=post_slug)
        
        # Get posts with same tags or category
        return BlogPost.objects.filter(
            Q(tags__in=post.tags.all()) | Q(category=post.category),
            status='PUBLISHED'
        ).exclude(id=post.id).distinct()[:4]