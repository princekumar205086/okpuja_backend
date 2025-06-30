import django_filters
from .models import PujaService, Package

class PujaServiceFilter(django_filters.FilterSet):
    min_duration = django_filters.NumberFilter(field_name="duration_minutes", lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name="duration_minutes", lookup_expr='lte')

    class Meta:
        model = PujaService
        fields = ['category', 'type', 'is_active']

class PackageFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')

    class Meta:
        model = Package
        fields = ['puja_service', 'language', 'package_type', 'is_active']