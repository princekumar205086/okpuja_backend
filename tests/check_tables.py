import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
all_tables = [row[0] for row in cursor.fetchall()]
print("All tables:")
for table in sorted(all_tables):
    print(f"  {table}")

# Find payment and cart related tables
payment_tables = [t for t in all_tables if 'payment' in t.lower()]
cart_tables = [t for t in all_tables if 'cart' in t.lower()]

print(f"\nPayment related tables: {payment_tables}")
print(f"Cart related tables: {cart_tables}")

# Check the specific tables we're dealing with
for table_name in payment_tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE cart_id = 37;")
        count = cursor.fetchone()[0]
        print(f"\n{table_name} has {count} records with cart_id=37")
        
        if count > 0:
            cursor.execute(f"SELECT id, cart_id FROM {table_name} WHERE cart_id = 37 LIMIT 5;")
            records = cursor.fetchall()
            print(f"Sample records: {records}")
    except Exception as e:
        print(f"Error checking {table_name}: {e}")

# Check if cart with id=37 exists
for table_name in cart_tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id = 37;")
        count = cursor.fetchone()[0]
        print(f"\n{table_name} has {count} records with id=37")
    except Exception as e:
        print(f"Error checking {table_name}: {e}")

cursor.close()
