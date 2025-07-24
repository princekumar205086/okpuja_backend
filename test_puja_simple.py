"""
Simple Puja App Functionality Test
"""

def test_puja_imports():
    """Test if all puja components can be imported"""
    try:
        # Setup Django first
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
        django.setup()
        
        from puja.models import PujaCategory, PujaService, Package, PujaBooking
        print("✅ Models imported successfully")
        
        from puja.serializers import PujaCategorySerializer, PujaServiceSerializer
        print("✅ Serializers imported successfully")
        
        from puja.views import PujaCategoryListView, PujaServiceListView
        print("✅ Views imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic puja functionality"""
    import os
    import django
    from pathlib import Path
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
    django.setup()
    
    from puja.models import PujaCategory
    
    # Test database connection
    try:
        count = PujaCategory.objects.count()
        print(f"✅ Database connection successful. Current categories: {count}")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing Puja App Components...")
    
    success = True
    
    if not test_puja_imports():
        success = False
    
    if not test_basic_functionality():
        success = False
    
    if success:
        print("🎉 All basic tests passed!")
    else:
        print("❌ Some tests failed!")
