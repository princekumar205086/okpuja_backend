import sqlite3
import os
import sys
import argparse

def fix_payment(payment_id):
    print(f"Starting payment fix for Payment ID: {payment_id}")
    
    db_path = 'db.sqlite3'
    print(f"Using database at: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {os.path.abspath(db_path)}")
        sys.exit(1)
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Connected to SQLite database!")
        
        # Check if payment exists
        cursor.execute("""
            SELECT 
                p.id, p.user_id, p.cart_id, p.booking_id, p.amount, p.status
            FROM payment_payment p
            WHERE p.id = ?
        """, (payment_id,))
        
        payment = cursor.fetchone()
        if not payment:
            print(f"Error: Payment with ID {payment_id} not found!")
            return False
            
        payment_id, user_id, cart_id, booking_id, amount, status = payment
        print(f"Found payment: ID={payment_id}, UserID={user_id}, CartID={cart_id}, BookingID={booking_id}, Amount={amount}, Status={status}")
        
        # Check if already has booking
        if booking_id:
            cursor.execute("SELECT id, status FROM booking_booking WHERE id = ?", (booking_id,))
            booking = cursor.fetchone()
            if booking:
                booking_id, booking_status = booking
                print(f"Payment already linked to Booking ID: {booking_id} (Status: {booking_status})")
                print("No fix needed.")
                return True
                
        # Check if cart exists
        cursor.execute("""
            SELECT id, status, selected_date, selected_time 
            FROM cart_cart 
            WHERE id = ?
        """, (cart_id,))
        
        cart = cursor.fetchone()
        if not cart:
            print(f"Error: Cart with ID {cart_id} not found!")
            return False
            
        cart_id, cart_status, selected_date, selected_time = cart
        print(f"Found cart: ID={cart_id}, Status={cart_status}, Date={selected_date}, Time={selected_time}")
        
        # Check if booking already exists for this cart
        cursor.execute("SELECT id, status FROM booking_booking WHERE cart_id = ?", (cart_id,))
        existing_booking = cursor.fetchone()
        
        if existing_booking:
            booking_id, booking_status = existing_booking
            print(f"Booking already exists: ID={booking_id}, Status={booking_status}")
            
            # Update payment to link to booking
            cursor.execute("UPDATE payment_payment SET booking_id = ?, status = 1 WHERE id = ?", 
                          (booking_id, payment_id))
            conn.commit()
            print(f"Updated payment: linked to booking ID {booking_id} and set status to SUCCESS (1)")
        else:
            # Get address
            cursor.execute("SELECT id FROM accounts_address WHERE user_id = ? LIMIT 1", (user_id,))
            address = cursor.fetchone()
            
            if not address:
                print("No address found for user, creating default address...")
                cursor.execute("""
                    INSERT INTO accounts_address 
                    (user_id, address_line_1, city, state, pincode) 
                    VALUES (?, 'Default Address', 'Unknown', 'Unknown', '000000')
                """, (user_id,))
                conn.commit()
                
                cursor.execute("SELECT id FROM accounts_address WHERE user_id = ? LIMIT 1", (user_id,))
                address = cursor.fetchone()
                
            address_id = address[0]
            print(f"Using address ID: {address_id}")
            
            # Create booking
            print("Creating new booking...")
            cursor.execute("""
                INSERT INTO booking_booking 
                (user_id, cart_id, selected_date, selected_time, address_id, status) 
                VALUES (?, ?, ?, ?, ?, 'CONFIRMED')
            """, (user_id, cart_id, selected_date, selected_time, address_id))
            conn.commit()
            
            # Get new booking ID
            cursor.execute("SELECT last_insert_rowid()")
            new_booking_id = cursor.fetchone()[0]
            print(f"Created new booking with ID: {new_booking_id}")
            
            # Update payment to link to booking
            cursor.execute("UPDATE payment_payment SET booking_id = ?, status = 1 WHERE id = ?", 
                          (new_booking_id, payment_id))
            conn.commit()
            print(f"Updated payment: linked to booking ID {new_booking_id} and set status to SUCCESS (1)")
            
            # Update cart
            cursor.execute("UPDATE cart_cart SET status = 'CONVERTED' WHERE id = ?", (cart_id,))
            conn.commit()
            print(f"Updated cart status to CONVERTED")
        
        # Close connection
        cursor.close()
        conn.close()
        print("Database connection closed")
        print(f"Payment ID {payment_id} fixed successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix payment and create booking if needed')
    parser.add_argument('payment_id', type=int, help='Payment ID to fix')
    args = parser.parse_args()
    
    success = fix_payment(args.payment_id)
    if success:
        print("Script completed successfully")
    else:
        print("Script failed")
        sys.exit(1)
