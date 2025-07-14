"""
Simple API test for PhonePe payment integration
Usage: python api_test.py
"""

import requests
import json
from decimal import Decimal

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def test_payment_api():
    """Test payment API endpoints"""
    
    # First, you need to be authenticated and have a booking
    # This is a basic test structure
    
    print("=== PhonePe Payment API Test ===")
    
    # Test payment creation (this will require authentication and a valid booking)
    payment_data = {
        "booking": 1,  # Replace with actual booking ID
        "amount": "100.00",
        "method": "PHONEPE",
        "redirect_url": "http://localhost:3000/confirmbooking/"
    }
    
    # You would need to add authentication headers here
    headers = {
        "Content-Type": "application/json",
        # "Authorization": "Bearer your_token_here"
    }
    
    print("Payment creation endpoint: POST /api/payments/payments/")
    print("Sample payload:", json.dumps(payment_data, indent=2))
    print()
    
    # Test status check endpoint
    print("Payment status check endpoint: GET /api/payments/payments/{id}/status/")
    print()
    
    # Test webhook endpoint
    print("Webhook endpoint: POST /api/payments/webhook/phonepe/")
    print("This endpoint receives callbacks from PhonePe")
    print()
    
    print("Note: To test these endpoints properly, you need:")
    print("1. A running Django server (python manage.py runserver)")
    print("2. Valid authentication token")
    print("3. Existing booking records")
    print("4. PhonePe dashboard configuration")

if __name__ == "__main__":
    test_payment_api()
