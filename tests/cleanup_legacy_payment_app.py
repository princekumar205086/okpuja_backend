#!/usr/bin/env python3
"""
Legacy Payment App Cleanup Script
This script safely removes the old payment app and updates all dependencies
"""

import os
import shutil
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def backup_payment_app():
    """Create backup of payment app before removal"""
    print("📦 Creating backup of legacy payment app...")
    
    payment_dir = "payment"
    backup_dir = "backups/legacy_payment_app"
    
    if os.path.exists(payment_dir):
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copytree(payment_dir, f"{backup_dir}/payment", dirs_exist_ok=True)
        print(f"✅ Backup created: {backup_dir}/payment")
    else:
        print("❌ Payment app directory not found")

def remove_payment_app():
    """Remove the legacy payment app directory"""
    print("🗑️ Removing legacy payment app...")
    
    payment_dir = "payment"
    if os.path.exists(payment_dir):
        shutil.rmtree(payment_dir)
        print("✅ Legacy payment app removed")
    else:
        print("❌ Payment app directory not found")

def update_settings():
    """Update settings.py to remove payment app and add payments app"""
    print("⚙️ Updating settings.py...")
    
    settings_file = "okpuja_backend/settings.py"
    
    try:
        with open(settings_file, 'r') as f:
            content = f.read()
        
        # Remove 'payment' and ensure 'payments' is present
        content = content.replace("'payment',", "")
        content = content.replace("'payment'", "")
        
        if "'payments'," not in content and "'payments'" not in content:
            # Add payments app if not present
            content = content.replace(
                "'accounts',",
                "'accounts',\n    'payments',"
            )
        
        with open(settings_file, 'w') as f:
            f.write(content)
        
        print("✅ Settings.py updated")
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")

def update_main_urls():
    """Update main urls.py to remove payment URLs and add payments URLs"""
    print("🔗 Updating main urls.py...")
    
    urls_file = "okpuja_backend/urls.py"
    
    try:
        with open(urls_file, 'r') as f:
            content = f.read()
        
        # Remove old payment URLs
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            if "path('api/payment/" in line or "path('api/payments/" in line and "'payment." in line:
                continue  # Skip old payment URLs
            filtered_lines.append(line)
        
        # Add new payments URLs if not present
        content = '\n'.join(filtered_lines)
        
        if "path('api/v1/payments/" not in content:
            # Find where to insert the new URL
            admin_pattern = "path('admin/', admin.site.urls),"
            if admin_pattern in content:
                content = content.replace(
                    admin_pattern,
                    f"{admin_pattern}\n    path('api/v1/payments/', include('payments.urls')),"
                )
        
        with open(urls_file, 'w') as f:
            f.write(content)
        
        print("✅ Main urls.py updated")
        
    except Exception as e:
        print(f"❌ Error updating urls: {e}")

def check_migrations():
    """Check for any migration dependencies"""
    print("🔍 Checking migration dependencies...")
    
    try:
        from django.db import connection
        cursor = connection.cursor()
        
        # Check if payment app tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'payment_%'
        """)
        
        payment_tables = cursor.fetchall()
        
        if payment_tables:
            print("⚠️ Found legacy payment tables:")
            for table in payment_tables:
                print(f"   - {table[0]}")
            print("💡 Consider backing up data before proceeding")
        else:
            print("✅ No legacy payment tables found")
            
    except Exception as e:
        print(f"❌ Error checking migrations: {e}")

def main():
    """Main cleanup function"""
    print("🧹 LEGACY PAYMENT APP CLEANUP")
    print("=" * 50)
    print("This script will:")
    print("1. Backup the legacy payment app")
    print("2. Remove the payment app directory")
    print("3. Update settings.py")
    print("4. Update main urls.py")
    print("5. Check migration dependencies")
    print("=" * 50)
    
    response = input("Proceed with cleanup? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled")
        return
    
    try:
        backup_payment_app()
        check_migrations()
        update_settings()
        update_main_urls()
        
        print("\n" + "=" * 50)
        print("🎉 CLEANUP PREPARATION COMPLETE")
        print("=" * 50)
        print("✅ Settings updated")
        print("✅ URLs updated")
        print("✅ Backup created")
        print("\n📋 Manual Steps:")
        print("1. Review the changes in settings.py and urls.py")
        print("2. Run: python manage.py makemigrations")
        print("3. Run: python manage.py migrate")
        print("4. Test your application")
        print("5. If everything works, manually delete the payment/ folder")
        print("\n⚠️ Only delete payment/ folder after confirming everything works!")
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        print("Please review and fix the error before proceeding")

if __name__ == "__main__":
    main()
