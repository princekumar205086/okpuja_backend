import os
import sys
import django
import logging
import traceback

# Set up Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    try:
        from payment.models import Payment, PaymentStatus
        
        # Check if any payments exist
        payment_count = Payment.objects.count()
        print(f"Total payments in database: {payment_count}")
        
        if payment_count == 0:
            print("No payments found in database.")
            return
        
        # Get the payment
        payment_id = 27
        try:
            payment = Payment.objects.get(id=payment_id)
            print(f"Found payment: ID={payment.id}, Status={payment.status}")
            print(f"Transaction ID: {payment.transaction_id}")
            print(f"User: {payment.user.email}")
            print(f"Amount: {payment.amount} {payment.currency}")
            print(f"Has cart: {'Yes' if payment.cart else 'No'}")
            print(f"Has booking: {'Yes' if payment.booking else 'No'}")
            
            # Update payment status
            old_status = payment.status
            payment.status = PaymentStatus.SUCCESS
            payment.save()
            print(f"Changed status from {old_status} to {payment.status}")
            
            # Refresh payment
            payment.refresh_from_db()
            print(f"After saving, status is: {payment.status}")
            print(f"Has booking now: {'Yes' if payment.booking else 'No'}")
            
            if not payment.booking:
                print("No booking was created automatically, creating manually...")
                if payment.cart:
                    print(f"Cart ID: {payment.cart.id}")
                    print(f"Cart status: {payment.cart.status}")
                    print(f"Selected date: {payment.cart.selected_date}")
                    print(f"Selected time: {payment.cart.selected_time}")
                    
                    booking = payment.create_booking_from_cart()
                    print(f"Manually created booking ID: {booking.id}")
                else:
                    print("Cannot create booking - no cart associated with payment")
        
        except Payment.DoesNotExist:
            print(f"Payment with ID {payment_id} not found")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
