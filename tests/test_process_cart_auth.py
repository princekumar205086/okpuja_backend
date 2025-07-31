#!/usr/bin/env python3
"""
Test process-cart endpoint with authentication using provided credentials and cart ID.
"""

import requests
import sys

BASE_URL = "https://api.okpuja.com"
LOGIN_ENDPOINT = f"{BASE_URL}/api/auth/login/"
PROCESS_CART_ENDPOINT = f"{BASE_URL}/api/payments/payments/process-cart/"

# Credentials provided
EMAIL = "asliprinceraj@gmail.com"
PASSWORD = "Testpass@123"
CART_ID = 19


def get_token():
    """
    Obtain JWT access token from login endpoint.
    """
    data = {"email": EMAIL, "password": PASSWORD}
    try:
        resp = requests.post(LOGIN_ENDPOINT, json=data, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to log in: {e}")
        sys.exit(1)

    tokens = resp.json()
    access = tokens.get("access")
    if not access:
        print(f"❌ No access token in login response: {tokens}")
        sys.exit(1)
    print("✅ Obtained access token successfully")
    return access


def test_process_cart():
    """
    Test the process-cart endpoint with the obtained token and print result.
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"cart_id": CART_ID, "method": "PHONEPE"}
    print(f"🔗 Calling {PROCESS_CART_ENDPOINT} with payload: {payload}")

    try:
        resp = requests.post(PROCESS_CART_ENDPOINT, json=payload, headers=headers, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        sys.exit(1)

    print(f"📊 Status Code: {resp.status_code}")
    try:
        data = resp.json()
        print("📄 Response JSON:", data)
    except ValueError:
        print("📄 Response Text:", resp.text)

    if resp.status_code not in (200, 201):
        print("❌ Endpoint returned error status. Please check backend logs for details.")
    else:
        print("🎉 process-cart endpoint works as expected!")


if __name__ == "__main__":
    print("🚀 Testing process-cart endpoint")
    test_process_cart()
