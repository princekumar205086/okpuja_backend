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

def fix_payment_and_create_booking():
    """
    Fix payment ID 27 (the one from PhonePe) and create a booking
    """
    try:
        print("\n\n==== FIXING PAYMENT AND CREATING BOOKING ====\n")
        
        from payment.models import Payment, PaymentStatus
        from booking.models import Booking, BookingStatus
        from django.utils import timezone
        
        # Get the payment with ID 27 (the one from PhonePe)
        payment_id = 27
        
        try:
            payment = Payment.objects.get(id=payment_id)
            print(f"Found payment: ID={payment.id}, Status={payment.status}")
            print(f"Transaction ID: {payment.transaction_id}")
            print(f"Merchant Transaction ID: {payment.merchant_transaction_id}")
            print(f"User: {payment.user.email}")
            print(f"Amount: {payment.amount} {payment.currency}")
            
            # Check if payment already has a booking
            if payment.booking:
                print(f"Payment already has a booking: {payment.booking.id}")
                return
            
            # Check if payment has a cart
            if not payment.cart:
                print("Payment does not have a cart. Cannot create booking.")
                return
            
            print(f"Cart ID: {payment.cart.id}")
            print(f"Cart selected date: {payment.cart.selected_date}")
            print(f"Cart selected time: {payment.cart.selected_time}")
            
            # Update payment status to SUCCESS
            if payment.status != PaymentStatus.SUCCESS:
                payment.status = PaymentStatus.SUCCESS
                payment.save()
                print(f"Updated payment status to SUCCESS")
            
            # Try automatic booking creation via the model method
            try:
                print("Attempting to create booking using model method...")
                
                # Print the create_booking_from_cart method for debugging
                if hasattr(payment, 'create_booking_from_cart'):
                    print("Payment has create_booking_from_cart method")
                    booking = payment.create_booking_from_cart()
                    print(f"✅ Successfully created booking ID: {booking.id}")
                    return booking
                else:
                    print("❌ Payment object doesn't have create_booking_from_cart method!")
                    # Let's continue to manual creation
            except Exception as e:
                print(f"❌ Error in automatic booking creation: {str(e)}")
                print(traceback.format_exc())
            
            # If automatic creation fails, try manual booking creation
            print("Trying manual booking creation...")
            
            # Find default address or first address for the user
            from accounts.models import Address
            address = Address.objects.filter(user=payment.user, is_default=True).first()
            if not address:
                address = Address.objects.filter(user=payment.user).first()
                if not address:
                    print("User has no addresses. Creating a default one...")
                    address = Address.objects.create(
                        user=payment.user,
                        address_line_1="Default Address",
                        city="Unknown",
                        state="Unknown",
                        pincode="000000",
                        is_default=True
                    )
            
            # Parse time from cart's selected_time
            from datetime import datetime
            selected_time = payment.cart.selected_time
            parsed_time = None
            
            if isinstance(selected_time, str):
                try:
                    if ":" in selected_time:
                        if "AM" in selected_time or "PM" in selected_time:
                            parsed_time = datetime.strptime(selected_time, '%I:%M %p').time()
                        else:
                            parsed_time = datetime.strptime(selected_time, '%H:%M').time()
                    else:
                        parsed_time = datetime.strptime(f"{selected_time}:00", '%H:%M').time()
                except ValueError:
                    parsed_time = datetime.strptime("10:00", '%H:%M').time()
            else:
                parsed_time = datetime.strptime("10:00", '%H:%M').time()
            
            # Create booking manually
            booking = Booking.objects.create(
                user=payment.user,
                cart=payment.cart,
                selected_date=payment.cart.selected_date,
                selected_time=parsed_time,
                address=address,
                status=BookingStatus.CONFIRMED,
                created_at=timezone.now()
            )
            
            # Update payment with booking reference
            payment.booking = booking
            payment.save()
            
            # Update cart status
            payment.cart.status = 'CONVERTED'
            payment.cart.save()
            
            print(f"✅ Manually created booking ID: {booking.id}")
            return booking
            
        except Payment.DoesNotExist:
            print(f"Payment with ID {payment_id} not found")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    result = fix_payment_and_create_booking()
    if result:
        print(f"\n✅ SUCCESS! Booking {result.id} created successfully from payment 27")
    else:
        print(f"\n❌ FAILED to create booking from payment 27")
