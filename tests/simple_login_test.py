import requests
import json

# Test with simple curl-like requests
def test_login():
    url = "http://localhost:8000/api/accounts/auth/login/"
    data = {
        "email": "asliprinceraj@gmail.com",
        "password": "testpass123"
    }
    
    try:
        print("Testing login...")
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Login successful!")
            return result.get('access')
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_login()
