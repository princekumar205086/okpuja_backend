import json
import hashlib
import base64
import requests
import uuid
import datetime
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Define a custom PhonePe exception
class PhonePeException(Exception):
    """Custom PhonePe exception for error handling"""
    pass

class PhonePeGateway:
    def __init__(self):
        """Initialize PhonePe Gateway with direct API approach"""
        self.merchant_id = settings.PHONEPE_MERCHANT_ID
        self.merchant_key = settings.PHONEPE_MERCHANT_KEY
        self.salt_index = settings.PHONEPE_SALT_INDEX
        self.base_url = settings.PHONEPE_BASE_URL
        
    def generate_transaction_id(self):
        """Generate a unique transaction ID"""
        uuid_part = str(uuid.uuid4()).split('-')[0].upper()
        now = datetime.datetime.now().strftime('%Y%m%d')
        return f"TRX{now}{uuid_part}"
    
    def generate_checksum(self, data, endpoint="/pg/v1/pay"):
        """Generate checksum for PhonePe API"""
        checksum_str = data + endpoint + self.merchant_key
        checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + '###' + str(self.salt_index)
        return checksum

    def initiate_payment(self, payment):
        """
        Initiate payment using PhonePe direct API
        
        Args:
            payment: Payment model instance
            
        Returns:
            dict: Response containing checkout URL and payment details
        """
        try:
            # Prepare callback URLs
            callback_url = f"{settings.PHONEPE_CALLBACK_URL}"
            redirect_url = f"{settings.PHONEPE_SUCCESS_REDIRECT_URL}?payment_id={payment.id}"
            
            # Create payload
            payload = {
                "merchantId": self.merchant_id,
                "merchantTransactionId": payment.merchant_transaction_id,
                "merchantUserId": f"USR{payment.user.id}",
                "amount": int(payment.amount * 100),  # Convert to paisa
                "redirectUrl": redirect_url,
                "redirectMode": "POST",
                "callbackUrl": callback_url,
                "mobileNumber": getattr(payment.user, 'phone_number', None) or "9000000000",
                "paymentInstrument": {
                    "type": "PAY_PAGE"
                }
            }
            
            # Encode payload
            data = base64.b64encode(json.dumps(payload).encode()).decode()
            checksum = self.generate_checksum(data)
            
            final_payload = {
                "request": data,
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-VERIFY': checksum,
                'X-MERCHANT-ID': self.merchant_id,
            }
            
            # Make API call
            api_url = f"{self.base_url}/pg/v1/pay"
            logger.info(f"Making PhonePe API call to: {api_url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Payload: {final_payload}")
            
            response = requests.post(api_url, headers=headers, json=final_payload)
            logger.info(f"PhonePe API Status: {response.status_code}")
            logger.info(f"PhonePe API Response Text: {response.text}")
            
            response_data = response.json()
            logger.info(f"PhonePe API Response: {response_data}")
            
            if response_data.get('success'):
                payment_url = response_data['data']['instrumentResponse']['redirectInfo']['url']
                
                # Update payment with gateway response
                payment.gateway_response = response_data
                payment.save()
                
                return {
                    'success': True,
                    'payment_url': payment_url,
                    'transaction_id': payment.transaction_id,
                    'merchant_transaction_id': payment.merchant_transaction_id
                }
            else:
                error_msg = response_data.get('message', 'Payment initiation failed')
                error_code = response_data.get('code', 'UNKNOWN')
                logger.error(f"PhonePe payment initiation failed: {error_msg} (Code: {error_code})")
                logger.error(f"Full response: {response_data}")
                raise PhonePeException(f"Payment initiation failed: {error_msg}")
                
        except requests.RequestException as e:
            logger.error(f"PhonePe API request failed: {str(e)}")
            raise PhonePeException(f"API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"PhonePe payment initiation error: {str(e)}")
            raise PhonePeException(f"Payment initiation failed: {str(e)}")

    def check_payment_status(self, merchant_transaction_id):
        """
        Check payment status using PhonePe API
        
        Args:
            merchant_transaction_id: Merchant transaction ID
            
        Returns:
            dict: Payment status response
        """
        try:
            endpoint = f"/pg/v1/status/{self.merchant_id}/{merchant_transaction_id}"
            checksum = self.generate_checksum("", endpoint)
            
            headers = {
                'Content-Type': 'application/json',
                'X-VERIFY': checksum,
                'X-MERCHANT-ID': self.merchant_id
            }
            
            api_url = f"{self.base_url}{endpoint}"
            response = requests.get(api_url, headers=headers)
            response_data = response.json()
            
            logger.info(f"PhonePe status check response: {response_data}")
            return response_data
            
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            raise Exception(f"Status check failed: {str(e)}")

    def process_webhook(self, headers, callback_body_string):
        """
        Process PhonePe webhook callback
        
        Args:
            headers: Full request headers from PhonePe
            callback_body_string: Raw callback body as string
            
        Returns:
            Payment: Updated payment object
        """
        from .models import Payment, PaymentStatus
        
        try:
            # Parse the callback data
            callback_data = json.loads(callback_body_string)
            
            # Extract checksum for validation
            x_verify_header = headers.get('X-VERIFY')
            if not x_verify_header:
                logger.error("Webhook validation failed: Missing X-VERIFY header")
                raise Exception("Invalid webhook callback: Missing X-VERIFY header")
            
            # Decode the response if it's base64 encoded
            if 'response' in callback_data:
                decoded_response = json.loads(base64.b64decode(callback_data['response']).decode('utf-8'))
            else:
                decoded_response = callback_data
            
            merchant_transaction_id = decoded_response.get('data', {}).get('merchantTransactionId')
            
            if not merchant_transaction_id:
                logger.error("No merchant transaction ID in callback")
                raise Exception("Invalid callback: No merchant transaction ID")
            
            # Find payment by merchant_transaction_id
            try:
                payment = Payment.objects.get(merchant_transaction_id=merchant_transaction_id)
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for merchant transaction ID: {merchant_transaction_id}")
                raise Exception(f"Payment not found for merchant transaction ID: {merchant_transaction_id}")
            
            # Update payment status based on callback
            transaction_data = decoded_response.get('data', {})
            state = transaction_data.get('state')
            
            if state == 'COMPLETED':
                payment.status = PaymentStatus.SUCCESS
            elif state in ['FAILED', 'DECLINED']:
                payment.status = PaymentStatus.FAILED
            elif state == 'PENDING':
                payment.status = PaymentStatus.PENDING
            
            # Update gateway response with callback data
            payment.gateway_response = payment.gateway_response or {}
            payment.gateway_response.update({
                'webhook_callback': {
                    'decoded_response': decoded_response,
                    'timestamp': str(timezone.now())
                }
            })
            
            # This save will trigger the booking creation via the overridden save method
            payment.save()
            
            logger.info(f"PhonePe webhook processed for merchant transaction: {merchant_transaction_id}, status: {payment.status}")
            
            return payment
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            raise Exception(f"Webhook processing failed: {str(e)}")

    def initiate_refund(self, refund):
        """
        Initiate refund using PhonePe API
        
        Args:
            refund: Refund model instance
            
        Returns:
            dict: Refund response
        """
        try:
            refund_payload = {
                "merchantId": self.merchant_id,
                "merchantTransactionId": refund.refund_id,
                "originalTransactionId": refund.payment.merchant_transaction_id,
                "amount": int(refund.amount * 100),  # Convert to paisa
                "callbackUrl": settings.PHONEPE_CALLBACK_URL
            }
            
            data = base64.b64encode(json.dumps(refund_payload).encode()).decode()
            checksum = self.generate_checksum(data, "/pg/v1/refund")
            
            final_payload = {
                "request": data,
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-VERIFY': checksum,
                'X-MERCHANT-ID': self.merchant_id,
            }
            
            api_url = f"{self.base_url}/pg/v1/refund"
            response = requests.post(api_url, headers=headers, json=final_payload)
            response_data = response.json()
            
            logger.info(f"PhonePe refund response: {response_data}")
            
            if response_data.get('success'):
                refund.gateway_response = response_data
                refund.save()
                return response_data
            else:
                error_msg = response_data.get('message', 'Refund initiation failed')
                raise PhonePeException(f"Refund failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"PhonePe refund error: {str(e)}")
            raise PhonePeException(f"Refund failed: {str(e)}")


def get_payment_gateway(name='phonepe'):
    """
    Factory function to get payment gateway instance
    
    Args:
        name: Gateway name (default: 'phonepe')
        
    Returns:
        Gateway instance
    """
    gateways = {
        'phonepe': PhonePeGateway,
    }
    
    gateway_class = gateways.get(name.lower())
    if not gateway_class:
        raise ValueError(f"Unknown payment gateway: {name}")
    
    return gateway_class()