from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('categories/', views.GalleryCategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.GalleryCategoryDetailView.as_view(), name='category-detail'),
    path('items/', views.GalleryItemListView.as_view(), name='item-list'),
    path('items/featured/', views.FeaturedGalleryItemsView.as_view(), name='featured-items'),
    path('items/<int:pk>/', views.GalleryItemDetailView.as_view(), name='item-detail'),
    path('categories/<slug:slug>/items/', views.GalleryCategoryItemsView.as_view(), name='category-items'),
    
    # Admin endpoints
    path('admin/items/', views.GalleryAdminListView.as_view(), name='admin-item-list'),
    path('admin/items/upload/', views.GalleryUploadView.as_view(), name='item-upload'),
    path('admin/items/<int:pk>/', views.GalleryAdminDetailView.as_view(), name='admin-item-detail'),
]