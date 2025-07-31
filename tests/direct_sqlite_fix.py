import sqlite3
import os
import sys

print("Starting direct SQLite test...")
print(f"Current directory: {os.getcwd()}")

db_path = 'db.sqlite3'
print(f"Looking for database at: {os.path.abspath(db_path)}")

if not os.path.exists(db_path):
    print(f"Error: Database file not found at {os.path.abspath(db_path)}")
    sys.exit(1)

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Connected to SQLite database!")
    
    # Check payment with id 27
    cursor.execute("SELECT id, user_id, cart_id, booking_id, amount, status FROM payment_payment WHERE id = 27")
    payment = cursor.fetchone()
    
    if payment:
        payment_id, user_id, cart_id, booking_id, amount, status = payment
        print(f"Payment found: ID={payment_id}, UserID={user_id}, CartID={cart_id}, BookingID={booking_id}, Amount={amount}, Status={status}")
        
        # Update status to SUCCESS (assuming SUCCESS=1)
        cursor.execute("UPDATE payment_payment SET status = 1 WHERE id = 27")
        conn.commit()
        print("Updated payment status to SUCCESS")
        
        # Get cart details
        cursor.execute("SELECT id, selected_date, selected_time FROM cart_cart WHERE id = ?", (cart_id,))
        cart = cursor.fetchone()
        if cart:
            cart_id, selected_date, selected_time = cart
            print(f"Cart found: ID={cart_id}, Date={selected_date}, Time={selected_time}")
        else:
            print("Error: Cart not found")
            
        # Find address
        cursor.execute("SELECT id FROM accounts_address WHERE user_id = ? LIMIT 1", (user_id,))
        address = cursor.fetchone()
        address_id = None
        
        if address:
            address_id = address[0]
            print(f"Found address ID: {address_id}")
        else:
            print("No address found, would need to create one")
        
        # Check if booking exists
        cursor.execute("SELECT id FROM booking_booking WHERE cart_id = ?", (cart_id,))
        existing_booking = cursor.fetchone()
        
        if existing_booking:
            booking_id = existing_booking[0]
            print(f"Booking already exists with ID: {booking_id}")
            
            # Update payment to link to booking
            cursor.execute("UPDATE payment_payment SET booking_id = ? WHERE id = 27", (booking_id,))
            conn.commit()
            print(f"Updated payment to link to booking ID {booking_id}")
        else:
            print("No booking exists, would need to create one")
            # In a full implementation, we would create the booking here
    else:
        print("Error: Payment with ID 27 not found")
        
    # Close connection
    cursor.close()
    conn.close()
    print("Database connection closed")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
print("Test complete")
