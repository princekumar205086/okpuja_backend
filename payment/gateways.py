import logging
import hashlib
import base64
import json
import uuid
import datetime
import requests
import requests.adapters
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
        self.base_url = getattr(settings, 'PHONEPE_BASE_URL', 'https://api.phonepe.com/apis/hermes')
        
        # Connection settings for production server issues
        self.timeout = int(getattr(settings, 'PHONEPE_TIMEOUT', 60))
        self.max_retries = int(getattr(settings, 'PHONEPE_MAX_RETRIES', 3))
        self.ssl_verify = getattr(settings, 'PHONEPE_SSL_VERIFY', 'True').lower() == 'true'
        
        logger.info(f"PhonePe Gateway initialized: merchant_id={self.merchant_id}, base_url={self.base_url}, timeout={self.timeout}s, retries={self.max_retries}")
        
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
        Initiate payment using PhonePe direct API with enhanced production resilience
        
        Args:
            payment: Payment model instance
            
        Returns:
            dict: Response containing checkout URL and payment details
        """
        try:
            # Prepare callback URLs with better fallback handling
            try:
                callback_url = f"{settings.PHONEPE_CALLBACK_URL}"
                redirect_url = f"{settings.PHONEPE_SUCCESS_REDIRECT_URL}?payment_id={payment.id}"
            except AttributeError:
                # Fallback for missing settings
                callback_url = "https://api.okpuja.com/api/payments/webhook/phonepe/"
                redirect_url = f"https://api.okpuja.com/payment/success?payment_id={payment.id}"
                logger.warning("Using fallback URLs for PhonePe callbacks")
            
            # Enhanced user phone handling
            user_phone = None
            if hasattr(payment.user, 'phone_number') and payment.user.phone_number:
                user_phone = payment.user.phone_number
            elif hasattr(payment.user, 'phone') and payment.user.phone:
                user_phone = payment.user.phone
            else:
                user_phone = "9000000000"  # Default fallback
            
            # Create payload with enhanced validation
            payload = {
                "merchantId": self.merchant_id,
                "merchantTransactionId": payment.merchant_transaction_id,
                "merchantUserId": f"USR{payment.user.id}",
                "amount": int(float(payment.amount) * 100),  # Convert to paisa with explicit float conversion
                "redirectUrl": redirect_url,
                "redirectMode": "POST",
                "callbackUrl": callback_url,
                "mobileNumber": user_phone,
                "paymentInstrument": {
                    "type": "PAY_PAGE"
                }
            }
            
            # Validate payload before encoding
            if payload["amount"] <= 0:
                raise PhonePeException(f"Invalid payment amount: {payment.amount}")
            
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
                'User-Agent': 'OkPuja-Backend/1.0',
                'Accept': 'application/json'
            }
            
            # Multiple API endpoint fallbacks for production resilience
            # Add IP-based endpoints as fallback for DNS issues
            api_endpoints = [
                f"{self.base_url}/pg/v1/pay",
                "https://api.phonepe.com/apis/hermes/pg/v1/pay",
                "https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay",  # Alternative domain
                "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"  # Preprod as last resort
            ]
            
            logger.info(f"Starting PhonePe payment initiation for transaction: {payment.merchant_transaction_id}")
            logger.info(f"Amount: ₹{payment.amount} (₹{payload['amount']/100})")
            logger.info(f"User: {payment.user.email} (ID: {payment.user.id})")
            
            # Try multiple endpoints and attempts
            for endpoint_idx, api_url in enumerate(api_endpoints):
                logger.info(f"Trying endpoint {endpoint_idx + 1}/{len(api_endpoints)}: {api_url}")
                
                for attempt in range(self.max_retries):
                    try:
                        # Progressive timeout increase for retries
                        timeout = self.timeout + (attempt * 30)
                        logger.info(f"PhonePe API attempt {attempt + 1}/{self.max_retries} with timeout {timeout}s")
                        
                        # Enhanced session configuration for production
                        session = requests.Session()
                        session.verify = self.ssl_verify
                        
                        # Production-specific connection settings
                        if hasattr(settings, 'PRODUCTION_SERVER') and settings.PRODUCTION_SERVER:
                            # More aggressive timeouts and connection settings for production
                            adapter = requests.adapters.HTTPAdapter(
                                pool_connections=10,
                                pool_maxsize=20,
                                max_retries=0,  # We handle retries manually
                                pool_block=False
                            )
                        else:
                            # Standard settings for local/development
                            adapter = requests.adapters.HTTPAdapter(
                                pool_connections=1,
                                pool_maxsize=1,
                                max_retries=0
                            )
                        
                        session.mount('https://', adapter)
                        session.mount('http://', adapter)
                        
                        # Add custom headers for production servers
                        production_headers = headers.copy()
                        production_headers.update({
                            'Connection': 'close',  # Force connection close to avoid keep-alive issues
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'
                        })
                        
                        logger.info(f"Making request to: {api_url}")
                        logger.info(f"Request headers: {list(production_headers.keys())}")
                        
                        response = session.post(
                            api_url, 
                            headers=production_headers, 
                            json=final_payload,
                            timeout=timeout,
                            allow_redirects=True
                        )
                        
                        logger.info(f"PhonePe API Status: {response.status_code}")
                        logger.info(f"PhonePe API Response: {response.text[:500]}...")  # Log first 500 chars
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            
                            if response_data.get('success'):
                                payment_url = response_data['data']['instrumentResponse']['redirectInfo']['url']
                                
                                # Update payment with gateway response
                                payment.gateway_response = response_data
                                payment.phonepe_payment_id = response_data.get('data', {}).get('transactionId')
                                payment.save()
                                
                                logger.info(f"✅ PhonePe payment initiated successfully!")
                                logger.info(f"Payment URL: {payment_url}")
                                
                                return {
                                    'success': True,
                                    'payment_url': payment_url,
                                    'checkout_url': payment_url,  # Alternative key name
                                    'transaction_id': payment.transaction_id,
                                    'merchant_transaction_id': payment.merchant_transaction_id,
                                    'phonepe_transaction_id': response_data.get('data', {}).get('transactionId')
                                }
                            else:
                                error_msg = response_data.get('message', 'Payment initiation failed')
                                error_code = response_data.get('code', 'UNKNOWN')
                                logger.error(f"PhonePe payment failed: {error_msg} (Code: {error_code})")
                                logger.error(f"Full response: {response_data}")
                                
                                # Don't retry for business logic errors
                                if error_code in ['BAD_REQUEST', 'INVALID_MERCHANT', 'AMOUNT_LIMIT_EXCEEDED']:
                                    raise PhonePeException(f"PhonePe Error: {error_msg} (Code: {error_code})")
                                
                                # Retry for other errors
                                if attempt == self.max_retries - 1:
                                    raise PhonePeException(f"PhonePe Error: {error_msg} (Code: {error_code})")
                                continue
                        else:
                            logger.error(f"PhonePe API HTTP Error: {response.status_code} - {response.text}")
                            if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                                raise PhonePeException(f"PhonePe API HTTP Error: {response.status_code}")
                            continue  # Retry
                            
                    except requests.exceptions.ConnectionError as e:
                        logger.error(f"PhonePe API Connection Error (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {str(e)}")
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            raise PhonePeException(f"Cannot connect to PhonePe API after trying all endpoints. Network issue detected. Error: {str(e)}")
                        continue  # Retry
                        
                    except requests.exceptions.Timeout as e:
                        logger.error(f"PhonePe API Timeout (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {str(e)}")
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            raise PhonePeException(f"PhonePe API timeout after trying all endpoints. Error: {str(e)}")
                        continue  # Retry
                        
                    except requests.exceptions.SSLError as e:
                        logger.error(f"PhonePe API SSL Error (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {str(e)}")
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            raise PhonePeException(f"SSL connection error to PhonePe API. Error: {str(e)}")
                        continue  # Retry
                        
                    except requests.RequestException as e:
                        logger.error(f"PhonePe API Request Error (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {str(e)}")
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            raise PhonePeException(f"Network error connecting to PhonePe API: {str(e)}")
                        continue  # Retry
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"PhonePe API Invalid JSON Response (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {str(e)}")
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            raise PhonePeException(f"Invalid response from PhonePe API: {str(e)}")
                        continue  # Retry
                        
                    except Exception as e:
                        logger.error(f"Unexpected error during PhonePe API call (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {str(e)}")
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            raise PhonePeException(f"Unexpected error during payment initiation: {str(e)}")
                        continue  # Retry
                        
        except PhonePeException:
            # Re-raise PhonePe specific exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Critical error in PhonePe payment initiation: {str(e)}")
            raise PhonePeException(f"Critical payment system error: {str(e)}")

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