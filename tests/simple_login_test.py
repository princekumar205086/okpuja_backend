import requests
import json

def simple_test():
    print("🔍 Simple Login Test")
    print("=" * 30)
    
    # Test UAT credentials
    login_data = {
        "email": "asliprinceraj@gmail.com",
        "password": "testpass123"
    }
    
    try:
        print("Testing UAT login...")
        response = requests.post("http://127.0.0.1:8000/api/auth/login/", 
                               json=login_data, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ UAT Login successful!")
            print(f"Access token: {data.get('access', '')[:30]}...")
            
            # Test profile access
            headers = {'Authorization': f'Bearer {data.get("access")}'}
            profile_resp = requests.get("http://127.0.0.1:8000/api/auth/profile/", 
                                      headers=headers, timeout=5)
            
            if profile_resp.status_code == 200:
                print("✅ Profile access successful!")
                profile_data = profile_resp.json()
                print(f"User: {profile_data.get('email')}")
            else:
                print(f"❌ Profile access failed: {profile_resp.status_code}")
        else:
            print("❌ Login failed")
            print(f"Response: {response.text}")
            
            # Try production credentials
            print("\nTesting Production login...")
            login_data["password"] = "Testpass@123"
            response = requests.post("http://127.0.0.1:8000/api/auth/login/", 
                                   json=login_data, timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Production Login successful!")
                print(f"Access token: {data.get('access', '')[:30]}...")
            else:
                print("❌ Production login also failed")
                print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simple_test()
