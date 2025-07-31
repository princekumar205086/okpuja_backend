from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Payments app configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'Payment Management'
