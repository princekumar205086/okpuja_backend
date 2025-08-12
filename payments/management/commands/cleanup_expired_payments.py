"""
Professional Payment Cleanup Management Command
Automatically expires payments that have exceeded their timeout
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from payments.models import PaymentOrder
from payments.services import PaymentService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cleanup expired payment orders professionally'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without actually updating',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        """Clean up expired payment orders"""
        
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write('🧹 Starting professional payment cleanup...')
        
        if dry_run:
            self.stdout.write('🔍 DRY RUN MODE - No changes will be made')
        
        expired_count = 0
        checked_count = 0
        
        # Find all pending payments
        pending_orders = PaymentOrder.objects.filter(
            status__in=['PENDING', 'INITIATED']
        ).order_by('created_at')
        
        self.stdout.write(f'📊 Found {pending_orders.count()} pending payment orders to check')
        
        for order in pending_orders:
            checked_count += 1
            
            # Check if this payment should be expired
            if PaymentService.is_payment_expired(order):
                expired_count += 1
                
                if verbose:
                    timeout_minutes = order.metadata.get('payment_timeout_minutes', 5)
                    age_minutes = int((timezone.now() - order.created_at).total_seconds() / 60)
                    self.stdout.write(
                        f'  ⏰ Expiring {order.merchant_order_id} '
                        f'(Age: {age_minutes}min, Timeout: {timeout_minutes}min)'
                    )
                
                if not dry_run:
                    # Update the order
                    order.status = 'EXPIRED'
                    order.metadata['expired_at'] = datetime.now().isoformat()
                    order.metadata['expired_by_cleanup'] = True
                    order.metadata['cleanup_run_at'] = datetime.now().isoformat()
                    order.save()
                    
                    logger.info(f'Expired payment order: {order.merchant_order_id}')
            elif verbose:
                remaining_seconds = PaymentService.get_payment_remaining_time(order)
                remaining_minutes = int(remaining_seconds / 60)
                self.stdout.write(
                    f'  ✅ {order.merchant_order_id} still valid '
                    f'(Remaining: {remaining_minutes}min {remaining_seconds % 60}sec)'
                )
        
        # Summary
        self.stdout.write('\n📈 CLEANUP SUMMARY:')
        self.stdout.write(f'   Checked: {checked_count} orders')
        self.stdout.write(f'   Expired: {expired_count} orders')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'🔍 DRY RUN: {expired_count} orders would be expired')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully expired {expired_count} payment orders')
            )
        
        # Additional stats
        if verbose:
            self.stdout.write('\n📊 ADDITIONAL STATS:')
            
            # Count by status
            status_counts = {}
            for status in ['PENDING', 'INITIATED', 'SUCCESS', 'FAILED', 'EXPIRED']:
                count = PaymentOrder.objects.filter(status=status).count()
                if count > 0:
                    status_counts[status] = count
            
            for status, count in status_counts.items():
                self.stdout.write(f'   {status}: {count} orders')
            
            # Recent activity (last 24 hours)
            recent_time = timezone.now() - timedelta(hours=24)
            recent_count = PaymentOrder.objects.filter(
                created_at__gte=recent_time
            ).count()
            self.stdout.write(f'   Recent (24h): {recent_count} new orders')
        
        logger.info(f'Payment cleanup completed - expired {expired_count} orders')
        self.stdout.write('🎉 Cleanup completed!')
