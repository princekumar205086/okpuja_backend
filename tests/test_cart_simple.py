#!/usr/bin/env python
"""
Test cart creation specifically
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_cart_creation():
    """Test creating a cart"""
    try:
        from django.contrib.auth import get_user_model
        from cart.models import Cart
        from puja.models import PujaService, Package
        from datetime import date
        
        User = get_user_model()
        
        # Get test user (asliprinceraj@gmail.com)
        user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        if not user:
            print("❌ Test user 'asliprinceraj@gmail.com' not found")
            print("   Please create this user first")
            return False
        puja_service = PujaService.objects.first()
        package = Package.objects.filter(puja_service=puja_service).first()
        
        if not all([user, puja_service, package]):
            print("❌ Missing test data")
            return False
        
        print(f"Using:")
        print(f"  User: {user.email}")
        print(f"  Puja: {puja_service.title}")
        print(f"  Package: {package.get_package_type_display()} - ₹{package.price}")
        
        # Try to create cart
        cart = Cart(
            user=user,
            puja_service=puja_service,
            package=package,
            selected_date=date.today(),
            selected_time="10:00 AM",
            cart_id=f"TEST-SIMPLE-{user.id}",
            status=Cart.StatusChoices.ACTIVE
        )
        
        # Test validation before saving
        cart.full_clean()
        print("✅ Cart validation passed")
        
        # Test properties
        total_price = cart.total_price
        print(f"✅ Cart total price: ₹{total_price}")
        
        # Test methods that use payments
        can_delete = cart.can_be_deleted()
        print(f"✅ can_be_deleted: {can_delete}")
        
        deletion_info = cart.get_deletion_info()
        print(f"✅ get_deletion_info: {deletion_info}")
        
        print("✅ All cart operations successful!")
        return True
        
    except Exception as e:
        print(f"❌ Cart test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🛒 Testing Cart Creation\n")
    success = test_cart_creation()
    
    if success:
        print("\n🎉 Cart creation test passed!")
    else:
        print("\n❌ Cart creation test failed!")
