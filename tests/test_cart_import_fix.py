#!/usr/bin/env python
"""
Test script to verify that cart import issues are fixed
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_cart_imports():
    """Test that cart models can import payments correctly"""
    try:
        # Try importing cart models
        from cart.models import Cart
        print("✅ Cart model imported successfully")
        
        # Try creating a cart instance (without saving)
        from django.contrib.auth import get_user_model
        from datetime import date, time
        
        User = get_user_model()
        
        # Get a test user (first user in database)
        user = User.objects.first()
        if not user:
            print("❌ No users found in database for testing")
            return False
            
        # Create cart instance without saving
        cart = Cart(
            user=user,
            selected_date=date.today(),
            selected_time="10:00 AM",
            cart_id="TEST-CART-123"
        )
        
        print("✅ Cart instance created successfully")
        
        # Test cart methods that use payments imports
        print(f"✅ can_be_deleted method accessible: {hasattr(cart, 'can_be_deleted')}")
        print(f"✅ get_deletion_info method accessible: {hasattr(cart, 'get_deletion_info')}")
        print(f"✅ auto_cleanup_old_payments method accessible: {hasattr(cart, 'auto_cleanup_old_payments')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing cart import fixes...")
    success = test_cart_imports()
    
    if success:
        print("\n🎉 All cart import tests passed!")
        print("Cart creation should now work without 'No module named payment' errors.")
    else:
        print("\n❌ Cart import tests failed!")
        
    sys.exit(0 if success else 1)
