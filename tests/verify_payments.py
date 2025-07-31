import sqlite3
import os

print("Starting payment/booking verification...")
print(f"Current directory: {os.getcwd()}")

db_path = 'db.sqlite3'
print(f"Using database at: {os.path.abspath(db_path)}")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Connected to SQLite database!")
    
    # Get all payments
    cursor.execute("""
        SELECT 
            p.id, p.user_id, p.cart_id, p.booking_id, p.amount, p.status, 
            c.status as cart_status, 
            c.selected_date, c.selected_time
        FROM payment_payment p
        JOIN cart_cart c ON p.cart_id = c.id
        ORDER BY p.id DESC
        LIMIT 10
    """)
    
    payments = cursor.fetchall()
    print(f"Found {len(payments)} recent payments")
    
    for payment in payments:
        payment_id, user_id, cart_id, booking_id, amount, status, cart_status, selected_date, selected_time = payment
        
        print(f"\n--- Payment ID: {payment_id} ---")
        print(f"User ID: {user_id}")
        print(f"Cart ID: {cart_id} (Status: {cart_status})")
        print(f"Amount: {amount}")
        print(f"Selected Date: {selected_date}")
        print(f"Selected Time: {selected_time}")
        
        if booking_id:
            # Get booking details
            cursor.execute("SELECT id, status FROM booking_booking WHERE id = ?", (booking_id,))
            booking = cursor.fetchone()
            if booking:
                booking_id, booking_status = booking
                print(f"✅ Linked to Booking ID: {booking_id} (Status: {booking_status})")
            else:
                print(f"⚠️ Warning: Booking ID {booking_id} referenced but not found!")
        else:
            # Check if there's a booking for this cart
            cursor.execute("SELECT id, status FROM booking_booking WHERE cart_id = ?", (cart_id,))
            booking = cursor.fetchone()
            if booking:
                booking_id, booking_status = booking
                print(f"⚠️ Warning: Booking exists (ID: {booking_id}) but not linked to payment!")
            else:
                print(f"❌ ERROR: No booking found for this successful payment!")
    
    # Check payment statuses
    cursor.execute("SELECT DISTINCT status FROM payment_payment")
    statuses = cursor.fetchall()
    print("\n\nPayment status values in database:")
    for status in statuses:
        print(f"- {status[0]}")
        
    # Check payment table structure
    cursor.execute("PRAGMA table_info(payment_payment)")
    columns = cursor.fetchall()
    print("\nPayment table columns:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
        
    # Close connection
    cursor.close()
    conn.close()
    print("\nDatabase connection closed")
    print("Verification complete")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
