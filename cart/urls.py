# cart/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]