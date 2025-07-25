import requests
import json
import sys
import os
import django

# Set up Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payment.models import Payment, PaymentStatus

def test_webhook(payment_id=None):
    """
    Test the webhook functionality by simulating a PhonePe callback
    If payment_id is provided, uses that payment, otherwise uses the most recent pending payment
    """
    if payment_id:
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            print(f"❌ Payment with ID {payment_id} not found")
            return
    else:
        # Get the most recent pending payment
        payment = Payment.objects.filter(status=PaymentStatus.PENDING).order_by('-created_at').first()
        if not payment:
            print("❌ No pending payments found to test")
            return

    print(f"🔍 Testing webhook for payment: {payment.id}")
    print(f"Transaction ID: {payment.transaction_id}")
    print(f"Merchant Transaction ID: {payment.merchant_transaction_id}")
    print(f"Current Status: {payment.status}")
    print(f"Cart ID: {payment.cart_id}")
    
    # Simulate a successful payment webhook from PhonePe
    webhook_data = {
        "merchantId": "TAJFOOTWEARUAT",
        "merchantTransactionId": payment.merchant_transaction_id,
        "state": "COMPLETED",
        "responseCode": "SUCCESS",
        "paymentId": payment.phonepe_payment_id or "MOCK_PAYMENT_ID",
        "amount": int(payment.amount * 100),  # Convert to paisa
        "instrumentResponse": {
            "type": "UPI",
            "utr": "TEST12345678"
        }
    }
    
    # Call the webhook endpoint
    webhook_url = 'http://127.0.0.1:8000/api/payments/webhook/phonepe/'
    print(f"📤 Sending webhook to: {webhook_url}")
    print(f"📦 Webhook data: {json.dumps(webhook_data, indent=2)}")
    
    try:
        response = requests.post(
            webhook_url, 
            json=webhook_data,
            headers={
                'Content-Type': 'application/json',
                'X-VERIFY': 'mock-signature'
            }
        )
        
        print(f"📩 Webhook response status: {response.status_code}")
        print(f"📝 Webhook response body: {response.text}")
        
        # Check if payment was updated successfully
        payment.refresh_from_db()
        print(f"🔄 Payment status after webhook: {payment.status}")
        
        if payment.status == PaymentStatus.SUCCESS:
            print("✅ Payment successfully marked as successful")
            if payment.booking:
                print(f"✅ Booking created successfully: {payment.booking.id}")
            else:
                print("❌ Booking was not created after payment success")
        else:
            print("❌ Payment not marked as successful")
            
    except Exception as e:
        print(f"❌ Error sending webhook: {str(e)}")

if __name__ == "__main__":
    # Get payment ID from command line if provided
    payment_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    test_webhook(payment_id)
