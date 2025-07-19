from django.core.management.base import BaseCommand
from django.db import transaction
from cart.models import Cart
from accounts.models import User


class Command(BaseCommand):
    help = 'Enforce single active cart per user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        fixed_users = 0
        total_deactivated = 0
        
        for user in User.objects.all():
            active_carts = Cart.objects.filter(user=user, status='ACTIVE').order_by('-created_at')
            
            if active_carts.count() > 1:
                self.stdout.write(f"User {user.email} has {active_carts.count()} active carts")
                
                # Keep the most recent cart, deactivate others
                carts_to_deactivate = active_carts[1:]  # All except the first (most recent)
                
                for cart in carts_to_deactivate:
                    self.stdout.write(f"  Deactivating cart {cart.cart_id}")
                    
                    if not dry_run:
                        cart.status = Cart.StatusChoices.INACTIVE
                        cart.save()
                    
                    total_deactivated += 1
                
                fixed_users += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN: Would fix {fixed_users} users, deactivating {total_deactivated} carts"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Fixed {fixed_users} users, deactivated {total_deactivated} carts"
                )
            )
