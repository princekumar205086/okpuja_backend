"""
PhonePe V2 Standard Checkout Implementation Summary
Based on official documentation: https://developer.phonepe.com/v1/reference/woocommerce-plugin-2

Key Points from Documentation:
1. OAuth2 Authentication is required for V2 API
2. Use client_credentials grant type
3. Base URL for UAT: https://api-preprod.phonepe.com
4. Base URL for Production: https://api.phonepe.com

Test Credentials (UAT):
- clientId: TAJFOOTWEARUAT_2503031838273556894438
- clientSecret: NTY5NjExODAtZTlkNy00ZWM3LThlZWEtYWQ0NGJkMGMzMjkz
- clientVersion: 1
- grantType: client_credentials

API Endpoints:
- OAuth Token: /apis/hermes/v1/oauth/token (POST)
- Payment Initiation: /apis/hermes/pg/v1/pay (POST)  
- Payment Status: /apis/hermes/pg/v1/status/{merchantId}/{merchantTransactionId} (GET)
- Refund: /apis/hermes/pg/v1/refund (POST)

Flow:
1. Get OAuth2 access token
2. Create payment request with Standard Checkout
3. Get redirect URL for customer
4. Handle webhook callback
5. Verify payment status
"""

# Test the OAuth endpoint with curl equivalent
import requests
import json

def test_phonepe_oauth():
    """Test PhonePe OAuth with different endpoint variations"""
    base_urls = [
        "https://api-preprod.phonepe.com",
        "https://mercury-t2.phonepe.com"
    ]
    
    oauth_paths = [
        "/apis/hermes/v1/oauth/token",
        "/v1/oauth/token", 
        "/oauth/token",
        "/apis/v1/oauth/token"
    ]
    
    credentials = {
        'client_id': 'TAJFOOTWEARUAT_2503031838273556894438',
        'client_secret': 'NTY5NjExODAtZTlkNy00ZWM3LThlZWEtYWQ0NGJkMGMzMjkz',
        'client_version': '1',
        'grant_type': 'client_credentials'
    }
    
    print("🔍 Testing PhonePe OAuth Endpoints...")
    
    for base_url in base_urls:
        for oauth_path in oauth_paths:
            url = f"{base_url}{oauth_path}"
            
            try:
                print(f"\n📍 Testing: {url}")
                
                # Try form data
                response = requests.post(
                    url,
                    data=credentials,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept': 'application/json'
                    },
                    timeout=10
                )
                
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS with {url}")
                    data = response.json()
                    if 'access_token' in data:
                        print(f"   🎫 Token received: {data['access_token'][:20]}...")
                        return url, data
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                continue
    
    print("\n❌ No working OAuth endpoint found")
    return None, None

if __name__ == "__main__":
    working_url, token_data = test_phonepe_oauth()
    
    if working_url:
        print(f"\n✅ Working OAuth URL: {working_url}")
        print(f"✅ Token Data: {json.dumps(token_data, indent=2)}")
    else:
        print("\n❌ OAuth testing failed - may need to check PhonePe documentation or credentials")
