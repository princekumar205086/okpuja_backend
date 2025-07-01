from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from core.views import info_view

schema_view = get_schema_view(
   openapi.Info(
      title="OKPUJA API",
      default_version='v1',
      description="API for Hindu Puja and Astrology Services",
      terms_of_service="https://www.okpuja.com/terms/",
      contact=openapi.Contact(email="contact@okpuja.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    #info page
    path('', info_view, name='info'),
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/puja/', include('puja.urls')),
    path('api/astrology/', include('astrology.urls')),
    path('api/promo/', include('promo.urls')),
    path('api/cart/', include('cart.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)