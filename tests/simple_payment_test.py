import requests
import json

def simple_test():
    try:
        # Test local API
        print("Testing local API...")
        response = requests.get("http://localhost:8000/admin/", timeout=5)
        print(f"Local API response: {response.status_code}")
        
        # Test authentication
        print("Testing authentication...")
        login_data = {"email": "asliprinceraj@gmail.com", "password": "Testpass@123"}
        auth_response = requests.post("http://localhost:8000/api/accounts/auth/login/", json=login_data, timeout=10)
        print(f"Auth response: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            token = token_data.get('access')
            print(f"Token received: {bool(token)}")
            
            if token:
                # Test payment endpoint
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                payment_data = {"cart_id": 19, "method": "PHONEPE"}
                payment_response = requests.post(
                    "http://localhost:8000/api/payments/payments/process-cart/",
                    json=payment_data,
                    headers=headers,
                    timeout=30
                )
                print(f"Payment response: {payment_response.status_code}")
                if payment_response.status_code in [200, 201, 400]:
                    result = payment_response.json()
                    print(f"Payment result keys: {list(result.keys()) if isinstance(result, dict) else 'Not dict'}")
                    
                    if payment_response.status_code == 201:
                        print("SUCCESS: Payment initiated!")
                        print(f"Payment URL: {result.get('payment_url', 'N/A')}")
                    else:
                        print(f"Payment failed: {result.get('error', 'Unknown error')}")
                        print(f"Message: {result.get('user_message', 'N/A')}")
                else:
                    print(f"Payment error: {payment_response.text[:200]}")
        else:
            print(f"Auth failed: {auth_response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    simple_test()
