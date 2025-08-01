#!/usr/bin/env python
"""
Simple model structure verification
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def check_models():
    """Check model structure and data"""
    try:
        # Import models
        from django.contrib.auth import get_user_model
        from cart.models import Cart
        from puja.models import PujaService, Package
        from payments.models import PaymentOrder
        from booking.models import Booking
        
        User = get_user_model()
        
        print("✅ All models imported successfully")
        
        # Check if we have test data
        user_count = User.objects.count()
        puja_count = PujaService.objects.count()
        package_count = Package.objects.count()
        
        print(f"📊 Database Status:")
        print(f"   Users: {user_count}")
        print(f"   Puja Services: {puja_count}")
        print(f"   Packages: {package_count}")
        
        if user_count == 0:
            print("❌ No users found - need to create test data")
            return False
            
        if puja_count == 0:
            print("❌ No puja services found - need to create test data")
            return False
            
        if package_count == 0:
            print("❌ No packages found - need to create test data")
            return False
        
        # Get sample data
        user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        if not user:
            user = User.objects.first()  # fallback to any user
            if not user:
                print("❌ No users found")
                return False
        puja = PujaService.objects.first()
        package = Package.objects.filter(puja_service=puja).first()
        
        print(f"\n📝 Sample Data:")
        print(f"   User: {user.email}")
        print(f"   Puja Service: {puja.title}")
        print(f"   Package: {package.get_package_type_display()} - ₹{package.price}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Checking Model Structure and Data\n")
    success = check_models()
    
    if success:
        print("\n✅ Models and data look good!")
        print("Ready to run the complete integration test.")
    else:
        print("\n❌ Need to set up test data first.")
