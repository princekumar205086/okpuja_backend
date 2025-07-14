from django.core.management.base import BaseCommand
from django.conf import settings
from payment.gateways import get_payment_gateway


class Command(BaseCommand):
    help = 'Test PhonePe payment gateway configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--amount',
            type=float,
            default=100.0,
            help='Test payment amount (default: 100.0)'
        )
        parser.add_argument(
            '--test-status',
            action='store_true',
            help='Test status check for a merchant transaction ID'
        )
        parser.add_argument(
            '--merchant-id',
            type=str,
            help='Merchant transaction ID for status check'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== PhonePe Payment Gateway Test ===')
        )
        
        # Test configuration
        self.test_configuration()
        
        # Test gateway initialization
        gateway = self.test_gateway_init()
        
        if gateway and options['test_status'] and options['merchant_id']:
            self.test_status_check(gateway, options['merchant_id'])
        
        self.stdout.write(
            self.style.SUCCESS('\n=== Test Complete ===')
        )

    def test_configuration(self):
        """Test PhonePe configuration"""
        self.stdout.write('\n--- Configuration Test ---')
        
        config_items = [
            ('Environment', settings.PHONEPE_ENV),
            ('Client ID', settings.PHONEPE_CLIENT_ID),
            ('Client Secret', '*' * len(settings.PHONEPE_CLIENT_SECRET) if settings.PHONEPE_CLIENT_SECRET else 'Not set'),
            ('Client Version', settings.PHONEPE_CLIENT_VERSION),
            ('Redirect URL', settings.PHONEPE_REDIRECT_URL),
            ('Callback URL', settings.PHONEPE_CALLBACK_URL),
        ]
        
        for name, value in config_items:
            if value:
                self.stdout.write(f'✓ {name}: {value}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ {name}: Not configured')
                )

    def test_gateway_init(self):
        """Test gateway initialization"""
        self.stdout.write('\n--- Gateway Initialization Test ---')
        
        try:
            gateway = get_payment_gateway('phonepe')
            self.stdout.write('✓ PhonePe gateway initialized successfully')
            self.stdout.write(f'✓ Environment: {gateway.env}')
            self.stdout.write(f'✓ Client ID: {gateway.client_id}')
            return gateway
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Gateway initialization failed: {e}')
            )
            return None

    def test_status_check(self, gateway, merchant_id):
        """Test status check functionality"""
        self.stdout.write(f'\n--- Status Check Test for {merchant_id} ---')
        
        try:
            result = gateway.check_payment_status(merchant_id)
            self.stdout.write('✓ Status check successful')
            self.stdout.write(f'Status: {result.get("status")}')
            self.stdout.write(f'Response: {result}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Status check failed: {e}')
            )
