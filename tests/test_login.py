#!/usr/bin/env python
import requests
import json

# Test login endpoint
url = "http://127.0.0.1:8000/api/auth/login/"
data = {
    'email': 'admin@okpuja.com',
    'password': 'admin@123'
}

print(f"Testing login at: {url}")
print(f"Data: {data}")

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        try:
            json_response = response.json()
            print(f"JSON Keys: {list(json_response.keys())}")
        except:
            print("Response is not valid JSON")
except Exception as e:
    print(f"Error: {e}")
