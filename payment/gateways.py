import requests
import json
import hashlib
import base64
from django.conf import settings
from django.urls import reverse
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class PhonePeGateway:
    def __init__(self):
        self.salt_key = settings.PHONEPE_SALT_KEY
        self.merchant_id = settings.PHONEPE_MERCHANT_ID
        self.base_url = settings.PHONEPE_BASE_URL
        self.callback_url = settings.BASE_URL + reverse('payment-webhook', args=['phonepay'])

    def generate_checksum(self, payload):
        payload_str = json.dumps(payload)
        base64_payload = base64.b64encode(payload_str.encode('utf-8')).decode('utf-8')
        string_to_hash = base64_payload + "/pg/v1/pay" + self.salt_key
        sha256_hash = hashlib.sha256(string_to_hash.encode('utf-8')).hexdigest()
        return sha256_hash + "###1"

    def initiate_payment(self, payment):
        payload = {
            "merchantId": self.merchant_id,
            "merchantTransactionId": payment.merchant_transaction_id,
            "merchantUserId": str(payment.booking.user.id),
            "amount": int(payment.amount * 100),  # PhonePe expects amount in paise
            "redirectUrl": payment.redirect_url or self.callback_url,
            "redirectMode": "POST",
            "callbackUrl": self.callback_url,
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-VERIFY": self.generate_checksum(payload),
            "accept": "application/json"
        }

        base64_payload = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')

        try:
            response = requests.post(
                urljoin(self.base_url, "/pg/v1/pay"),
                json={"request": base64_payload},
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"PhonePe payment initiation failed: {str(e)}")
            raise

    def check_payment_status(self, merchant_transaction_id):
        string_to_hash = f"/pg/v1/status/{self.merchant_id}/{merchant_transaction_id}{self.salt_key}"
        sha256_hash = hashlib.sha256(string_to_hash.encode('utf-8')).hexdigest()
        checksum = sha256_hash + "###1"

        headers = {
            "Content-Type": "application/json",
            "X-VERIFY": checksum,
            "X-MERCHANT-ID": self.merchant_id,
            "accept": "application/json"
        }

        try:
            response = requests.get(
                urljoin(self.base_url, f"/pg/v1/status/{self.merchant_id}/{merchant_transaction_id}"),
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"PhonePe status check failed: {str(e)}")
            raise

    def process_webhook(self, data):
        from .models import Payment, PaymentStatus
        try:
            merchant_transaction_id = data.get('merchantTransactionId')
            payment = Payment.objects.get(merchant_transaction_id=merchant_transaction_id)
            
            # Verify checksum
            received_checksum = data.get('header', {}).get('signature')
            expected_checksum = self.generate_checksum(data.get('response', {}))
            
            if received_checksum != expected_checksum:
                raise ValueError("Invalid checksum in webhook")
            
            # Update payment status
            payment_status = data.get('response', {}).get('state')
            
            status_mapping = {
                'COMPLETED': PaymentStatus.SUCCESS,
                'FAILED': PaymentStatus.FAILED,
                'PENDING': PaymentStatus.PENDING
            }
            
            payment.status = status_mapping.get(payment_status, PaymentStatus.PENDING)
            payment.gateway_response = data
            payment.save()
            
            # Send notification
            payment.send_payment_notification()
            
            return payment
        except Exception as e:
            logger.error(f"PhonePe webhook processing failed: {str(e)}")
            raise

def get_payment_gateway(name):
    gateways = {
        'phonepay': PhonePeGateway,
    }
    return gateways.get(name.lower())()