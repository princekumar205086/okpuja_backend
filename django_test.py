import os
import sys
import django

print("Starting Django setup test...")
print(f"Current directory: {os.getcwd()}")
print(f"Python version: {sys.version}")

try:
    sys.path.append('.')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
    print("About to setup Django...")
    django.setup()
    print("Django setup successful!")
    
    from django.conf import settings
    print(f"DEBUG setting: {settings.DEBUG}")
    print(f"INSTALLED_APPS: {settings.INSTALLED_APPS[:5]}...")  # Show first 5 apps
    
    # Test importing a model
    print("Testing model import...")
    from payment.models import Payment
    print("Payment model imported successfully")
    
    # Test DB connection
    print("Testing database connection...")
    count = Payment.objects.count()
    print(f"Payment count: {count}")
    
    print("All tests passed!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
print("Test complete")
