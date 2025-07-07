from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, UserProfile, Address, SMSLog, PanCard

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = ('profile_thumbnail_display',)
    fields = ('first_name', 'last_name', 'dob', 'profile_picture_display', 'profile_thumbnail_display')
    
    def profile_picture_display(self, obj):
        if obj.profile_picture_url:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="150" style="border: 1px solid #ddd; border-radius: 4px; padding: 5px;" /></a>',
                obj.profile_picture_url,
                obj.profile_picture_url
            )
        return "No image uploaded"
    profile_picture_display.short_description = 'Profile Picture'
    
    def profile_thumbnail_display(self, obj):
        if obj.profile_thumbnail_url:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="75" style="border: 1px solid #ddd; border-radius: 4px; padding: 2px;" /></a>',
                obj.profile_thumbnail_url,
                obj.profile_thumbnail_url
            )
        return "No thumbnail available"
    profile_thumbnail_display.short_description = 'Thumbnail'

class PanCardInline(admin.StackedInline):
    model = PanCard
    can_delete = False
    verbose_name_plural = 'PAN Card'
    readonly_fields = ('pan_card_thumbnail_display',)
    fields = ('pan_number', 'pan_card_image_display', 'pan_card_thumbnail_display', 'is_verified')
    
    def pan_card_image_display(self, obj):
        if obj.pan_card_image_url:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="150" style="border: 1px solid #ddd; border-radius: 4px; padding: 5px;" /></a>',
                obj.pan_card_image_url,
                obj.pan_card_image_url
            )
        return "No PAN card uploaded"
    pan_card_image_display.short_description = 'PAN Card Image'
    
    def pan_card_thumbnail_display(self, obj):
        if obj.pan_card_thumbnail_url:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="75" style="border: 1px solid #ddd; border-radius: 4px; padding: 2px;" /></a>',
                obj.pan_card_thumbnail_url,
                obj.pan_card_thumbnail_url
            )
        return "No thumbnail available"
    pan_card_thumbnail_display.short_description = 'Thumbnail'

class AddressInline(admin.TabularInline):
    model = Address
    extra = 1

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, PanCardInline, AddressInline)
    list_display = ('email', 'get_full_name', 'phone', 'role', 'account_status', 'is_staff')
    list_filter = ('role', 'account_status', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'phone')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'account_status', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('OTP', {'fields': ('otp', 'otp_created_at', 'otp_verified')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'phone')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')

    def get_full_name(self, obj):
        return obj.profile.__str__() if hasattr(obj, 'profile') else ''
    get_full_name.short_description = 'Full Name'

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line1', 'city', 'state', 'is_default')
    list_filter = ('city', 'state', 'is_default')
    search_fields = ('user__email', 'address_line1', 'city', 'state', 'postal_code')

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('phone', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('phone',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'