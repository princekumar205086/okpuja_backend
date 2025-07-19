from django.core.management.base import BaseCommand
from django.db import transaction
from cart.models import Cart
from payment.models import Payment, PaymentStatus
from booking.models import BookingStatus


class Command(BaseCommand):
    help = 'Clean up converted carts and fix payment-cart relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup even for carts with pending payments',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write("Starting cart cleanup process...")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Find converted carts with successful bookings
        converted_carts = Cart.objects.filter(status='CONVERTED')
        cleaned_count = 0
        
        for cart in converted_carts:
            payments = Payment.objects.filter(cart=cart)
            successful_payments = payments.filter(status=PaymentStatus.SUCCESS)
            
            if successful_payments.exists():
                booking = successful_payments.first().booking
                if booking and booking.status in [BookingStatus.CONFIRMED, BookingStatus.COMPLETED]:
                    self.stdout.write(f"Cart {cart.cart_id}: Has successful booking, clearing cart reference...")
                    
                    if not dry_run:
                        with transaction.atomic():
                            # Clear cart reference from payments
                            payments.update(cart=None)
                            cleaned_count += 1
                    else:
                        cleaned_count += 1
            
            elif force and not payments.filter(status=PaymentStatus.PENDING).exists():
                # If force is enabled and no pending payments, clear references
                self.stdout.write(f"Cart {cart.cart_id}: Force cleaning (no pending payments)...")
                
                if not dry_run:
                    with transaction.atomic():
                        payments.update(cart=None)
                        cleaned_count += 1
                else:
                    cleaned_count += 1
        
        # Handle carts with only failed/cancelled payments
        failed_payment_carts = []
        for cart in Cart.objects.exclude(status='CONVERTED'):
            payments = Payment.objects.filter(cart=cart)
            if payments.exists():
                failed_statuses = [PaymentStatus.FAILED, PaymentStatus.CANCELLED]
                if all(p.status in failed_statuses for p in payments):
                    failed_payment_carts.append(cart)
        
        if failed_payment_carts:
            self.stdout.write(f"Found {len(failed_payment_carts)} carts with only failed/cancelled payments")
            
            for cart in failed_payment_carts:
                self.stdout.write(f"Cart {cart.cart_id}: Clearing failed payment references...")
                
                if not dry_run:
                    Payment.objects.filter(cart=cart).update(cart=None)
                    cleaned_count += 1
                else:
                    cleaned_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"DRY RUN: Would clean {cleaned_count} cart references")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully cleaned {cleaned_count} cart references")
            )
        
        # Summary
        remaining_protected = Cart.objects.filter(
            payments__isnull=False,
            payments__status=PaymentStatus.PENDING
        ).distinct().count()
        
        if remaining_protected > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"{remaining_protected} carts still have pending payments and cannot be deleted"
                )
            )
        
        self.stdout.write("Cart cleanup process completed!")
