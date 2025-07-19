from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from cart.models import Cart
from payment.models import Payment, PaymentStatus


class Command(BaseCommand):
    help = 'Auto-cleanup pending payments older than 30 minutes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--minutes',
            type=int,
            default=30,
            help='Age threshold in minutes for pending payments (default: 30)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        minutes_threshold = options['minutes']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        self.stdout.write(f"Cleaning up pending payments older than {minutes_threshold} minutes...")
        
        cutoff_time = timezone.now() - timedelta(minutes=minutes_threshold)
        
        # Find old pending payments
        old_pending_payments = Payment.objects.filter(
            status=PaymentStatus.PENDING,
            created_at__lt=cutoff_time
        ).select_related('cart')
        
        if not old_pending_payments.exists():
            self.stdout.write(self.style.SUCCESS("No old pending payments found"))
            return
        
        self.stdout.write(f"Found {old_pending_payments.count()} old pending payments")
        
        cancelled_count = 0
        carts_affected = set()
        
        for payment in old_pending_payments:
            age_minutes = int((timezone.now() - payment.created_at).total_seconds() / 60)
            self.stdout.write(
                f"  Payment {payment.transaction_id}: {age_minutes} minutes old, "
                f"Cart: {payment.cart.cart_id if payment.cart else 'None'}"
            )
            
            if payment.cart:
                carts_affected.add(payment.cart.cart_id)
            
            if not dry_run:
                payment.status = PaymentStatus.CANCELLED
                payment.updated_at = timezone.now()
                payment.save()
                cancelled_count += 1
            else:
                cancelled_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN: Would cancel {cancelled_count} payments affecting {len(carts_affected)} carts"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cancelled {cancelled_count} old pending payments affecting {len(carts_affected)} carts"
                )
            )
        
        # Show affected carts
        if carts_affected:
            self.stdout.write("\nAffected carts:")
            for cart_id in sorted(carts_affected):
                try:
                    cart = Cart.objects.get(cart_id=cart_id)
                    deletion_info = cart.get_deletion_info()
                    self.stdout.write(
                        f"  Cart {cart_id}: Can delete: {deletion_info['can_delete']}"
                    )
                except Cart.DoesNotExist:
                    self.stdout.write(f"  Cart {cart_id}: Not found")
        
        self.stdout.write("\nCleanup completed!")
