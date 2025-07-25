import os
import sys
import django
import logging

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

from payment.models import Payment, PaymentStatus
from booking.models import Booking

def list_all_payments():
    """
    List all payments in the system
    """
    payments = Payment.objects.all().order_by('-created_at')
    print(f"📋 Found {payments.count()} total payments in the system")
    
    for i, payment in enumerate(payments[:10]):  # Show only the first 10
        print(f"\nPayment #{i+1}: ID={payment.id}")
        print(f"Transaction ID: {payment.transaction_id}")
        print(f"Merchant Transaction ID: {payment.merchant_transaction_id}")
        print(f"Status: {payment.status}")
        print(f"Amount: {payment.amount} {payment.currency}")
        print(f"User: {payment.user.email}")
        print(f"Created: {payment.created_at}")
        print(f"Has booking: {'Yes' if payment.booking else 'No'}")
        print(f"Has cart: {'Yes' if payment.cart else 'No'}")

def fix_pending_payment(payment_id=None):
    """
    Fix a pending payment by manually marking it as successful and creating a booking
    If payment_id is provided, fixes that specific payment
    Otherwise, attempts to fix the most recent pending payment
    """
    print(f"🔍 Starting fix_pending_payment with payment_id={payment_id}")
    
    if payment_id:
        try:
            payment = Payment.objects.get(id=payment_id)
            print(f"✅ Found payment with ID {payment_id}")
        except Payment.DoesNotExist:
            print(f"❌ Payment with ID {payment_id} not found")
            return
    else:
        # First check if we have any payments
        if Payment.objects.count() == 0:
            print("❌ No payments found in the system")
            return
            
        # Get the most recent pending payment
        payment = Payment.objects.filter(status=PaymentStatus.PENDING).order_by('-created_at').first()
        if not payment:
            print("❌ No pending payments found to fix")
            print("📋 Listing all payments instead:")
            list_all_payments()
            return
    
    print(f"🔍 Fixing payment: {payment.id}")
    print(f"Transaction ID: {payment.transaction_id}")
    print(f"Merchant Transaction ID: {payment.merchant_transaction_id}")
    print(f"Current Status: {payment.status}")
    print(f"Amount: {payment.amount} {payment.currency}")
    
    if payment.booking:
        print(f"ℹ️ This payment already has a booking: {payment.booking.id}")
        return
    
    if not payment.cart:
        print("❌ This payment has no cart associated with it. Cannot create booking.")
        return
    
    print(f"🛒 Cart ID: {payment.cart.id}")
    print(f"👤 User: {payment.user.email}")
    
    try:
        # Mark payment as successful
        old_status = payment.status
        payment.status = PaymentStatus.SUCCESS
        print(f"🔄 Updating payment status from {old_status} to {PaymentStatus.SUCCESS}")
        payment.save()
        
        print(f"✅ Changed payment status from {old_status} to {payment.status}")
        
        # Check if booking was created
        payment.refresh_from_db()
        if payment.booking:
            print(f"✅ Booking created successfully: {payment.booking.id}")
        else:
            print("⚠️ Booking was not created automatically. Attempting manual creation...")
            
            # Manual booking creation
            try:
                print(f"🛒 Creating booking from cart ID: {payment.cart.id if payment.cart else 'None'}")
                if not payment.cart:
                    print("❌ Cannot create booking: No cart associated with payment")
                    return
                
                booking = payment.create_booking_from_cart()
                print(f"✅ Manually created booking: {booking.id}")
            except Exception as e:
                print(f"❌ Failed to manually create booking: {str(e)}")
                import traceback
                print(f"📚 Traceback: {traceback.format_exc()}")
                
    except Exception as e:
        print(f"❌ Error fixing payment: {str(e)}")
        import traceback
        print(f"📚 Traceback: {traceback.format_exc()}")
        
if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            # List all payments
            list_all_payments()
        else:
            # Fix specific payment
            try:
                payment_id = int(sys.argv[1])
                fix_pending_payment(payment_id)
            except ValueError:
                print(f"❌ Invalid payment ID: {sys.argv[1]}")
                print("Usage: python fix_payment.py [payment_id|list]")
    else:
        # No arguments, try to fix most recent pending payment
        fix_pending_payment(None)
