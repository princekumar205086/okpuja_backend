#!/usr/bin/env python
"""
Run migrations and prepare database
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def run_migrations():
    """Run all pending migrations"""
    try:
        print("🔄 Creating migrations for payments app...")
        execute_from_command_line(['manage.py', 'makemigrations', 'payments'])
        
        print("🔄 Running all migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def check_database():
    """Check database tables exist"""
    try:
        from django.db import connection
        
        cursor = connection.cursor()
        
        # Check if key tables exist
        tables_to_check = [
            'payments_paymentorder',
            'cart_cart',
            'puja_pujaservice',
            'puja_package',
            'booking_booking'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print("📋 Database Tables:")
        for table in tables_to_check:
            if table in existing_tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} (missing)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    print("🗄️ Setting up Database\n")
    
    migration_success = run_migrations()
    if migration_success:
        check_success = check_database()
        
        if check_success:
            print("\n🎉 Database setup completed!")
            print("Ready to test cart and payments integration.")
        else:
            print("\n❌ Database check failed!")
    else:
        print("\n❌ Migration failed!")
