#!/usr/bin/env python
"""
API Connectivity Test Script for OkPuja Backend
This script tests connectivity to OkPuja API endpoints without browser CORS restrictions
"""

import os
import sys
import requests
import json
from urllib.parse import urljoin

def test_api_connectivity(base_url="https://api.okpuja.com"):
    """
    Test connectivity to key OkPuja API endpoints
    This will help determine if the issue is with CORS or the API itself
    """
    print("\n========== OKPUJA API CONNECTIVITY TEST ==========\n")
    print(f"Testing API connectivity to: {base_url}\n")
    
    # List of API endpoints to test
    endpoints = [
        "/api/puja/services/",
        "/api/puja/categories/",
        "/api/blog/posts/",
        "/api/gallery/items/",
    ]
    
    all_successful = True
    
    for endpoint in endpoints:
        url = urljoin(base_url, endpoint)
        print(f"Testing endpoint: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Try to parse JSON response
                try:
                    data = response.json()
                    item_count = len(data) if isinstance(data, list) else "N/A"
                    print(f"✅ SUCCESS - Status: {response.status_code}, Items: {item_count}")
                    
                    # Sample of response data
                    if isinstance(data, list) and data:
                        print(f"  Sample item: {json.dumps(data[0], indent=2)[:200]}...")
                except json.JSONDecodeError:
                    print(f"✅ SUCCESS - Status: {response.status_code}, but response is not valid JSON")
                    print(f"  Response preview: {response.text[:100]}...")
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"  Error: {response.text[:200]}")
                all_successful = False
                
        except Exception as e:
            print(f"❌ ERROR - {str(e)}")
            all_successful = False
            
        print("")  # Empty line for readability
    
    # Print diagnostics summary
    print("--- SUMMARY ---")
    
    if all_successful:
        print("✅ All API endpoints are accessible!")
        print("\nThis indicates your API is working correctly from server-to-server.")
        print("If your frontend still has issues, it's likely due to CORS configuration.")
    else:
        print("❌ Some API endpoints failed!")
        print("\nThis indicates there might be issues with the API itself, not just CORS.")
        print("Check your server logs for more details.")
    
    print("\n--- RECOMMENDATIONS ---")
    print("1. If all endpoints work here but fail in the browser: Fix CORS settings")
    print("2. If endpoints fail here: Check API server, network connectivity, or firewall rules")
    print("3. For frontend issues: Use the browser Network tab to inspect actual requests")
    
    print("\n========== TEST COMPLETE ==========")

if __name__ == "__main__":
    # Allow custom base URL if provided as command-line argument
    if len(sys.argv) > 1:
        test_api_connectivity(sys.argv[1])
    else:
        test_api_connectivity()
