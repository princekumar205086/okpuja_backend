#!/usr/bin/env python
import requests

def test_redirect_flow():
    print("🔗 TESTING REDIRECT FLOW")
    print("="*50)
    
    try:
        response = requests.get(
            'http://127.0.0.1:8000/api/payments/redirect/simple/',
            allow_redirects=False,
            timeout=10
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', 'None')
            print(f"🔗 Redirect URL: {location}")
            
            # Extract cart_id from redirect URL
            if 'cart_id=' in location:
                start = location.find('cart_id=') + 8
                end = location.find('&', start)
                if end == -1:
                    cart_id = location[start:]
                else:
                    cart_id = location[start:end]
                print(f"📦 Cart ID in redirect: {cart_id}")
                
                # Check which cart this is
                new_cart_id = '33dd806a-6989-47f5-a840-e588a73e11eb'
                old_cart_id = '5c4dad97-f37f-4afb-85e5-3d87075cf2ac'
                
                if cart_id == new_cart_id:
                    print("   ✅ Redirecting to NEW cart (correct!)")
                elif cart_id == old_cart_id:
                    print("   ⚠️ Redirecting to OLD cart (issue!)")
                else:
                    print("   ❓ Redirecting to different cart")
            else:
                print("   ❌ No cart_id in redirect URL")
        else:
            print(f"❌ Unexpected status code")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_redirect_flow()
