from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PromoCodeViewSet, PublicPromoCodeViewSet, UserPromoCodeViewSet

router = DefaultRouter()
router.register(r'admin/promos', PromoCodeViewSet, basename='admin-promo')
router.register(r'promos', PublicPromoCodeViewSet, basename='public-promo')
router.register(r'user/promos', UserPromoCodeViewSet, basename='user-promo')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional endpoints
    path('admin/promos/bulk-create/',
         PromoCodeViewSet.as_view({'post': 'bulk_create'}),
         name='promo-bulk-create'),
    
    path('admin/promos/export/',
         PromoCodeViewSet.as_view({'get': 'export'}),
         name='promo-export'),
    
    path('admin/promos/stats/',
         PromoCodeViewSet.as_view({'get': 'stats'}),
         name='promo-stats'),
    
    path('promos/validate/',
         PublicPromoCodeViewSet.as_view({'get': 'validate'}),
         name='promo-validate'),
    
    path('user/promos/history/',
         UserPromoCodeViewSet.as_view({'get': 'history'}),
         name='user-promo-history'),
]