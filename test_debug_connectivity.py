#!/usr/bin/env python3
"""
Test production connectivity for payment gateway using debug-connectivity endpoint.
"""
import requests
import sys

DEBUG_ENDPOINT = "https://api.okpuja.com/api/payments/payments/debug-connectivity/"


def test_debug_connectivity():
    """
    Call debug-connectivity endpoint to test PhonePe connectivity.
    """
    payload = {"test_payment": True}
    try:
        resp = requests.post(DEBUG_ENDPOINT, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"❌ Connectivity test failed: {e}")
        sys.exit(1)
    print(f"📊 Status Code: {resp.status_code}")
    try:
        data = resp.json()
    except ValueError:
        print("📄 Non-JSON response:", resp.text)
        sys.exit(1)
    print("📋 Debug Info:")
    import json
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    print("🚀 Testing debug-connectivity endpoint")
    test_debug_connectivity()
