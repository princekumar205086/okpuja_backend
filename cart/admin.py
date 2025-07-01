# # cart/admin.py
# from django.contrib import admin
# from .models import Cart

# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ('cart_id', 'user', 'service_type', 'status', 'total_price', 'created_at')
#     list_filter = ('status', 'service_type', 'created_at')
#     search_fields = ('cart_id', 'user__email', 'user__username')
#     readonly_fields = ('cart_id', 'created_at', 'updated_at', 'total_price')
#     fieldsets = (
#         (None, {
#             'fields': ('cart_id', 'user', 'status')
#         }),
#         ('Service Information', {
#             'fields': ('service_type', 'puja_service', 'package', 'astrology_service')
#         }),
#         ('Booking Details', {
#             'fields': ('selected_date', 'selected_time')
#         }),
#         ('Pricing', {
#             'fields': ('promo_code', 'total_price')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at')
#         }),
#     )