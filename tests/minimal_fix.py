import os
import sys
import django
import traceback

print("Starting script...")

# Set up Django environment
print("Setting up Django environment...")
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()
print("Django setup complete!")

try:
    # Import models
    print("Importing models...")
    from payment.models import Payment, PaymentStatus
    from booking.models import Booking, BookingStatus
    from accounts.models import Address
    from datetime import datetime
    print("Models imported successfully!")

    # Get the specific payment (ID 27)
    print("Fetching payment with ID 27...")
    payment = Payment.objects.get(id=27)
    print(f"Found payment: ID={payment.id}, Status={payment.status}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    # Update status
    print("Updating payment status to SUCCESS...")
    payment.status = PaymentStatus.SUCCESS
    payment.save()
    print("Updated payment status to SUCCESS")

    # Get address
    print("Finding address for user...")
    address = Address.objects.filter(user=payment.user).first()
    if not address:
        print("No address found, creating default address...")
        address = Address.objects.create(
            user=payment.user,
            address_line_1="Default Address",
            city="Unknown", state="Unknown", pincode="000000"
        )
        print("Created default address")
    else:
        print(f"Found address: {address}")

    # Parse time
    print("Parsing selected time...")
    try:
        selected_time = payment.cart.selected_time
        print(f"Raw selected_time: {selected_time}, type: {type(selected_time)}")
        
        if isinstance(selected_time, str) and ":" in selected_time:
            if "AM" in selected_time or "PM" in selected_time:
                parsed_time = datetime.strptime(selected_time, '%I:%M %p').time()
            else:
                parsed_time = datetime.strptime(selected_time, '%H:%M').time()
        else:
            print("Using default time 10:00")
            parsed_time = datetime.strptime("10:00", '%H:%M').time()
    except Exception as e:
        print(f"Error parsing time: {e}")
        print("Using default time 10:00")
        parsed_time = datetime.strptime("10:00", '%H:%M').time()
    
    print(f"Final parsed_time: {parsed_time}")

    # Create booking
    print("Creating booking...")
    booking = Booking.objects.create(
        user=payment.user,
        cart=payment.cart,
        selected_date=payment.cart.selected_date,
        selected_time=parsed_time,
        address=address,
        status=BookingStatus.CONFIRMED
    )
    print(f"Created booking: ID={booking.id}")

    # Link payment to booking
    print("Linking payment to booking...")
    payment.booking = booking
    payment.save()
    print("Linked payment to booking")

    # Update cart
    print("Updating cart status...")
    payment.cart.status = 'CONVERTED'
    payment.cart.save()
    print("Updated cart status to CONVERTED")

    print("DONE - Payment fixed and booking created!")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
    print("Script failed!")
    sys.exit(1)
