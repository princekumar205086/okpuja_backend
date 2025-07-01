from django.contrib import admin
from .models import PromoCode, PromoCodeUsage

class PromoCodeUsageInline(admin.TabularInline):
    model = PromoCodeUsage
    extra = 0
    readonly_fields = ['used_at', 'discount_amount', 'original_amount']
    can_delete = False

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'get_discount_type_display', 
                   'is_active', 'start_date', 'expiry_date',
                   'usage_limit', 'used_count')
    list_filter = ('is_active', 'discount_type', 'code_type')
    search_fields = ('code', 'description')
    readonly_fields = ('used_count', 'created_at', 'updated_at')
    inlines = [PromoCodeUsageInline]
    actions = ['activate_selected', 'deactivate_selected']

    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)
    activate_selected.short_description = "Activate selected promo codes"

    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_selected.short_description = "Deactivate selected promo codes"

@admin.register(PromoCodeUsage)
class PromoCodeUsageAdmin(admin.ModelAdmin):
    list_display = ('promo_code', 'user', 'discount_amount', 'used_at')
    list_filter = ('used_at', 'promo_code')
    search_fields = ('promo_code__code', 'user__email')
    readonly_fields = ('used_at',)
    date_hierarchy = 'used_at'