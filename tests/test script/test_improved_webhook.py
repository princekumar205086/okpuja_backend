import requests
import json

# Test the improved webhook
webhook_url = "http://127.0.0.1:8000/api/payments/webhook/phonepe/"

print("Testing improved webhook...")

# Test 1: Empty body (should give helpful error)
print("\n1. Testing empty body:")
try:
    response = requests.post(webhook_url, data="", headers={'Content-Type': 'application/json'})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Valid PhonePe-like payload
print("\n2. Testing with sample PhonePe payload:")
sample_payload = {
    "response": "eyJzdWNjZXNzIjp0cnVlLCJjb2RlIjoiUEFZTUVOVF9TVUNDRVNTIiwibWVzc2FnZSI6IlBheW1lbnQgc3VjY2Vzc2Z1bCIsImRhdGEiOnsibWVyY2hhbnRJZCI6Ik9LUFVKQSIsIm1lcmNoYW50VHJhbnNhY3Rpb25JZCI6IlRYTjEyMzQ1Njc4OTAiLCJzdGF0ZSI6IkNPTVBMRVRFRCJ9fQ==",
    "merchantId": "OKPUJA",
    "merchantTransactionId": "TXN1234567890"
}

headers = {
    'Content-Type': 'application/json',
    'X-VERIFY': 'test_signature_here'
}

try:
    response = requests.post(webhook_url, json=sample_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Debug endpoint
print("\n3. Testing debug endpoint:")
debug_url = "http://127.0.0.1:8000/api/payments/webhook/debug/"

try:
    response = requests.get(debug_url)
    print(f"GET Status: {response.status_code}")
    print(f"GET Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"GET Error: {e}")

try:
    response = requests.post(debug_url, json=sample_payload, headers=headers)
    print(f"POST Status: {response.status_code}")
    print(f"POST Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"POST Error: {e}")
