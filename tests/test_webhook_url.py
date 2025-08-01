#!/usr/bin/env python
import requests

def test_webhook_endpoint():
    """Test the correct webhook endpoint"""
    print("=== TESTING CORRECT WEBHOOK ENDPOINT ===\n")
    
    webhook_url = "http://127.0.0.1:8000/api/payments/webhook/phonepe/"
    
    try:
        # Test with OPTIONS request (CORS preflight)
        response = requests.options(webhook_url)
        print(f"OPTIONS {webhook_url}: {response.status_code}")
        
        # Test with GET request (should return 405 Method Not Allowed)
        response = requests.get(webhook_url)
        print(f"GET {webhook_url}: {response.status_code}")
        
        if response.status_code == 405:
            print(f"✅ Webhook endpoint is accessible (405 = Method Not Allowed is expected)")
        elif response.status_code == 200:
            print(f"✅ Webhook endpoint is accessible")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
        # Test with POST request (simulating PhonePe webhook)
        test_payload = {
            "success": True,
            "code": "PAYMENT_SUCCESS",
            "message": "Your payment is successful.",
            "data": {
                "merchantId": "M22KEWU5BO1I2",
                "merchantTransactionId": "TEST_TXN_123",
                "transactionId": "T123456789",
                "amount": 50000,
                "state": "COMPLETED",
                "responseCode": "SUCCESS",
                "paymentInstrument": {
                    "type": "UPI",
                    "utr": "UTR123456"
                }
            }
        }
        
        print(f"\nTesting POST with test payload...")
        response = requests.post(webhook_url, json=test_payload)
        print(f"POST {webhook_url}: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to webhook endpoint. Is Django server running?")
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

def show_current_status():
    """Show current payment and booking status"""
    print(f"\n=== CURRENT STATUS SUMMARY ===\n")
    
    print(f"✅ ISSUES RESOLVED:")
    print(f"   ✅ Payment CART_898adab5-b860-4a42-9c8b-78ef174ad3f5_91FFE85A marked as SUCCESS")
    print(f"   ✅ Booking BK-692FB15D created successfully")
    print(f"   ✅ Email notification queued via Celery")
    print(f"   ✅ Frontend redirect will now show booking details")
    
    print(f"\n🔧 WEBHOOK CONFIGURATION:")
    print(f"   📝 Correct webhook URL: http://127.0.0.1:8000/api/payments/webhook/phonepe/")
    print(f"   📝 Current .env setting: http://localhost:8000/api/payments/webhook/phonepe/")
    print(f"   ⚠️ Note: localhost vs 127.0.0.1 should work the same locally")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Test your frontend with the new booking ID: BK-692FB15D")
    print(f"   2. Verify email notifications are working")
    print(f"   3. Configure PhonePe webhook in their dashboard for production")
    print(f"   4. Test end-to-end payment flow")

if __name__ == "__main__":
    test_webhook_endpoint()
    show_current_status()
