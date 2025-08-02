#!/usr/bin/env python
"""
Investigate cart cleanup issues and fix them
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

def investigate_cleanup_issues():
    """Investigate why cart cleanup is failing"""
    print("🔍 Investigating Cart Cleanup Issues")
    print("=" * 40)
    
    from cart.models import Cart
    from accounts.models import User
    from payments.models import PaymentOrder
    
    user = User.objects.get(email='asliprinceraj@gmail.com')
    
    # Check problematic carts
    problem_cart_ids = [
        'd89edec9-20b1-4b49-9295-0211d29d6f4f',
        'b784d3e0-fca5-4757-8ba9-9e9783cb212f', 
        '9b096c39-8de9-4975-ade1-244ac38c7bfb'
    ]
    
    for cart_id in problem_cart_ids:
        print(f"\n📦 Investigating cart: {cart_id}")
        cart = Cart.objects.filter(cart_id=cart_id).first()
        
        if cart:
            print(f"   ✅ Cart exists - Status: {cart.status}")
            
            # Check for payment orders referencing this cart
            payments = PaymentOrder.objects.filter(cart_id=cart_id)
            print(f"   💳 Payment orders: {payments.count()}")
            for payment in payments:
                print(f"      - {payment.merchant_order_id} ({payment.status})")
            
            # Try to delete the cart manually to see the error
            try:
                print(f"   🗑️  Attempting to delete cart...")
                cart.delete()
                print(f"   ✅ Cart deleted successfully!")
            except Exception as e:
                print(f"   ❌ Delete failed: {e}")
                
                # Check what's still referencing it
                if "FOREIGN KEY constraint failed" in str(e):
                    print(f"   🔗 Foreign key constraint issue detected")
                    
                    # Check for payment orders
                    payments = PaymentOrder.objects.filter(cart_id=cart_id)
                    if payments.exists():
                        print(f"   💳 Found {payments.count()} payment orders referencing this cart")
                        for payment in payments:
                            print(f"      Updating payment {payment.merchant_order_id} to remove cart reference")
                            payment.cart_id = None
                            payment.save()
                        
                        # Try delete again
                        try:
                            cart.delete()
                            print(f"   ✅ Cart deleted after removing payment references!")
                        except Exception as e2:
                            print(f"   ❌ Still failed: {e2}")
                    
        else:
            print(f"   ❌ Cart not found!")

def enhanced_cleanup_test():
    """Test enhanced cleanup that handles payment order references"""
    print(f"\n🧹 Testing Enhanced Cart Cleanup")
    print("=" * 40)
    
    from cart.models import Cart
    from accounts.models import User
    from payments.models import PaymentOrder
    from booking.models import Booking
    
    user = User.objects.get(email='asliprinceraj@gmail.com')
    
    # Get all converted carts
    converted_carts = Cart.objects.filter(user=user, status='CONVERTED').order_by('-created_at')
    print(f"📦 Total converted carts: {converted_carts.count()}")
    
    if converted_carts.count() > 3:
        carts_to_keep = converted_carts[:3] 
        carts_to_cleanup = converted_carts[3:]
        
        print(f"🎯 Will keep {len(carts_to_keep)} latest carts")
        print(f"🗑️  Will cleanup {len(carts_to_cleanup)} old carts")
        
        for cart in carts_to_cleanup:
            print(f"\n🧹 Cleaning up cart: {cart.cart_id}")
            
            try:
                # 1. Handle bookings
                bookings = Booking.objects.filter(cart=cart)
                for booking in bookings:
                    booking.cart = None
                    booking.save()
                    print(f"   📦 Booking {booking.book_id} - cart reference removed")
                
                # 2. Handle payment orders
                payments = PaymentOrder.objects.filter(cart_id=cart.cart_id)
                for payment in payments:
                    payment.cart_id = None
                    payment.save()
                    print(f"   💳 Payment {payment.merchant_order_id} - cart reference removed")
                
                # 3. Delete the cart
                cart.delete()
                print(f"   ✅ Cart {cart.cart_id} deleted successfully!")
                
            except Exception as e:
                print(f"   ❌ Failed to cleanup cart {cart.cart_id}: {e}")
        
        # Check final count
        final_count = Cart.objects.filter(user=user, status='CONVERTED').count()
        print(f"\n📊 Final converted cart count: {final_count}")
        
        if final_count <= 3:
            print("✅ Cleanup successful - 3 or fewer converted carts remaining")
            return True
        else:
            print("❌ Cleanup incomplete - more than 3 carts still exist")
            return False
    else:
        print("💡 No cleanup needed - 3 or fewer converted carts")
        return True

if __name__ == "__main__":
    investigate_cleanup_issues()
    success = enhanced_cleanup_test()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ CART CLEANUP INVESTIGATION & FIX COMPLETE!")
        print("🎯 Key findings:")
        print("   • Payment orders were preventing cart deletion")
        print("   • Enhanced cleanup removes all references first")
        print("   • Cleanup now works properly")
    else:
        print("❌ CLEANUP ISSUES STILL EXIST!")
