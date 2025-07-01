from django.contrib import admin
from .models import (
    TermsOfService, 
    PrivacyPolicy, 
    CancellationRefundPolicy,
    UserConsent
)

class VersionedModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'version', 'is_current', 'status', 'published_at')
    list_filter = ('status', 'is_current')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'version')
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'status')
        }),
        ('Metadata', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Versioning', {
            'fields': ('version', 'is_current', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TermsOfService)
class TermsOfServiceAdmin(VersionedModelAdmin):
    fieldsets = VersionedModelAdmin.fieldsets + (
        ('Additional Options', {
            'fields': ('attachment', 'requires_consent')
        }),
    )

@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(VersionedModelAdmin):
    fieldsets = VersionedModelAdmin.fieldsets + (
        ('Additional Options', {
            'fields': ('attachment', 'requires_consent')
        }),
    )

@admin.register(CancellationRefundPolicy)
class CancellationRefundPolicyAdmin(VersionedModelAdmin):
    fieldsets = VersionedModelAdmin.fieldsets + (
        ('Refund Details', {
            'fields': ('refund_period_days', 'cancellation_fee_percentage')
        }),
    )

@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'terms', 'privacy_policy', 'consented_at')
    list_filter = ('consented_at',)
    search_fields = ('user__email', 'terms__title', 'privacy_policy__title')
    readonly_fields = ('user', 'terms', 'privacy_policy', 'ip_address', 'user_agent', 'consented_at')
    
    def has_add_permission(self, request):
        return False