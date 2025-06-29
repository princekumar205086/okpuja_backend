from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Address, SMSLog
from imagekit.admin import AdminThumbnail

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = ('profile_thumbnail',)
    fields = ('first_name', 'last_name', 'dob', 'profile_picture', 'profile_thumbnail')


class AddressInline(admin.TabularInline):
    model = Address
    extra = 1

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, AddressInline)
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
            'fields': ('email', 'phone', 'password', 'password2'),
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