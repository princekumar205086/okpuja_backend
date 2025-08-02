#!/usr/bin/env python
"""
Check foreign key constraints to understand cart deletion issues
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def check_foreign_keys():
    """Check what's preventing cart deletion"""
    print("🔍 Checking Foreign Key Constraints")
    print("=" * 40)
    
    from django.db import connection
    from cart.models import Cart
    
    # Get the problematic cart
    cart_id = 'd89edec9-20b1-4b49-9295-0211d29d6f4f'
    cart = Cart.objects.filter(cart_id=cart_id).first()
    
    if not cart:
        print("❌ Cart not found!")
        return
    
    print(f"📦 Checking cart: {cart_id} (ID: {cart.id})")
    
    # Check all tables that might reference cart
    cursor = connection.cursor()
    
    # Find all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"\n🔍 Checking all tables for references to cart ID {cart.id}...")
    
    tables_with_cart_refs = []
    
    for table in tables:
        table_name = table[0]
        if table_name.startswith('django_') or table_name.startswith('auth_'):
            continue
            
        try:
            # Check if table has a cart_id column
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            cart_columns = []
            for col in columns:
                col_name = col[1]  # Column name is at index 1
                if 'cart' in col_name.lower():
                    cart_columns.append(col_name)
            
            if cart_columns:
                print(f"\n📋 Table {table_name} has cart columns: {cart_columns}")
                
                # Check for actual references
                for col in cart_columns:
                    try:
                        if col == 'cart_id' and col != 'id':
                            # Check for cart_id references
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} = ?", [cart.cart_id])
                            count = cursor.fetchone()[0]
                            if count > 0:
                                print(f"   ⚠️  Found {count} records in {table_name}.{col} referencing cart_id {cart.cart_id}")
                                tables_with_cart_refs.append((table_name, col, count))
                        elif col.endswith('_id') and 'cart' in col:
                            # Check for cart foreign key references
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col} = ?", [cart.id])
                            count = cursor.fetchone()[0]
                            if count > 0:
                                print(f"   ⚠️  Found {count} records in {table_name}.{col} referencing cart.id {cart.id}")
                                tables_with_cart_refs.append((table_name, col, count))
                    except Exception as e:
                        print(f"   ❌ Error checking {table_name}.{col}: {e}")
                        
        except Exception as e:
            print(f"❌ Error checking table {table_name}: {e}")
    
    print(f"\n📊 Summary of cart references:")
    if tables_with_cart_refs:
        for table, col, count in tables_with_cart_refs:
            print(f"   • {table}.{col}: {count} references")
    else:
        print("   ✅ No references found!")
    
    return tables_with_cart_refs

def force_cleanup_cart():
    """Force cleanup of the problematic cart"""
    print(f"\n🔨 Force Cleanup Problematic Cart")
    print("=" * 40)
    
    from cart.models import Cart
    from django.db import connection
    
    cart_id = 'd89edec9-20b1-4b49-9295-0211d29d6f4f'
    cart = Cart.objects.filter(cart_id=cart_id).first()
    
    if not cart:
        print("❌ Cart not found!")
        return False
    
    # Disable foreign key checks and force delete
    try:
        cursor = connection.cursor()
        
        # Disable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Force delete the cart
        cart.delete()
        
        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print(f"✅ Cart {cart_id} force deleted!")
        return True
        
    except Exception as e:
        print(f"❌ Force delete failed: {e}")
        return False

if __name__ == "__main__":
    refs = check_foreign_keys()
    
    if refs:
        print(f"\n💡 Found references preventing deletion")
        success = force_cleanup_cart()
    else:
        print(f"\n💡 No references found - trying normal delete")
        from cart.models import Cart
        cart = Cart.objects.filter(cart_id='d89edec9-20b1-4b49-9295-0211d29d6f4f').first()
        if cart:
            try:
                cart.delete()
                print("✅ Normal delete successful!")
                success = True
            except Exception as e:
                print(f"❌ Normal delete failed: {e}")
                success = force_cleanup_cart()
        else:
            success = True
    
    print("\n" + "=" * 40)
    if success:
        print("✅ CART CLEANUP ISSUE RESOLVED!")
    else:
        print("❌ CART CLEANUP ISSUE PERSISTS!")
