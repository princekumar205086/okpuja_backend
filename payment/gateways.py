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
        """Initialize PhonePe Gateway with enhanced production server handling"""
        self.merchant_id = settings.PHONEPE_MERCHANT_ID
        self.merchant_key = settings.PHONEPE_MERCHANT_KEY
        self.salt_index = settings.PHONEPE_SALT_INDEX
        # Get base URL correctly from settings (without /pay endpoint)
        self.base_url = getattr(settings, 'PHONEPE_BASE_URL', 'https://api.phonepe.com/apis/hermes')
        
        # Enhanced connection settings for production server issues
        self.timeout = int(getattr(settings, 'PHONEPE_TIMEOUT', 180))  # Use .env settings
        self.max_retries = int(getattr(settings, 'PHONEPE_MAX_RETRIES', 7))  # Use .env settings
        self.ssl_verify = getattr(settings, 'PHONEPE_SSL_VERIFY', 'True').lower() == 'true'
        
        # Production server detection
        self.is_production = getattr(settings, 'PRODUCTION_SERVER', False)
        
        # Define multiple API endpoints for fallback with correct URLs
        self.api_endpoints = [
            'https://api.phonepe.com/apis/hermes/pg/v1/pay',
            'https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay',  # Alternative production endpoint
            'https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay',  # UAT fallback
        ]
        
        logger.info(f"PhonePe Gateway initialized: merchant_id={self.merchant_id}, base_url={self.base_url}, timeout={self.timeout}s, retries={self.max_retries}, production={self.is_production}")
        
    def test_connectivity(self):
        """Test connectivity to PhonePe API endpoints"""
        connectivity_results = []
        
        for endpoint_base in self.api_endpoints:
            test_url = f"{endpoint_base}/health" if "/apis/hermes" in endpoint_base else endpoint_base
            try:
                response = requests.get(test_url, timeout=10, verify=self.ssl_verify)
                connectivity_results.append({
                    'endpoint': endpoint_base,
                    'status': 'connected',
                    'response_code': response.status_code
                })
                logger.info(f"✅ {endpoint_base}: Connected (Status: {response.status_code})")
            except requests.exceptions.ConnectionError:
                connectivity_results.append({
                    'endpoint': endpoint_base,
                    'status': 'connection_refused',
                    'error': 'Connection refused'
                })
                logger.error(f"❌ {endpoint_base}: Connection refused")
            except Exception as e:
                connectivity_results.append({
                    'endpoint': endpoint_base,
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"❌ {endpoint_base}: {str(e)}")
        
        return connectivity_results
        
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
                'User-Agent': 'okpuja-backend/1.0',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
            
            # Enhanced session configuration for production
            session = requests.Session()
            
            # Configure connection pooling and retries
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            retry_strategy = Retry(
                total=3,
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"]
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=10)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            # Multiple API endpoint fallbacks for production resilience
            # Use all available endpoints and try each one
            api_endpoints = []
            
            # Add configured base URL first
            if self.base_url:
                api_endpoints.append(f"{self.base_url}/pg/v1/pay")
            
            # Add fallback endpoints - ENHANCED with more options
            fallback_endpoints = [
                "https://api.phonepe.com/apis/hermes/pg/v1/pay",
                "https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay",
                "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"  # UAT fallback
            ]
            
            # Add fallbacks that aren't already in the list
            for endpoint in fallback_endpoints:
                if endpoint not in api_endpoints:
                    api_endpoints.append(endpoint)
            
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
                        
                        # Enhanced request approach with session and error handling
                        logger.info(f"Making session request to: {api_url}")
                        logger.info(f"Request headers: {list(headers.keys())}")
                        logger.info(f"Timeout: {timeout}s")
                        
                        response = session.post(
                            api_url,
                            headers=headers,
                            json=final_payload,
                            timeout=timeout,
                            verify=True  # Always verify SSL in production
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
                        error_msg = str(e)
                        logger.error(f"PhonePe API Connection Error (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {error_msg}")
                        
                        # Enhanced connection error handling
                        if "Connection refused" in error_msg:
                            logger.error("🚨 Connection refused - likely server firewall or network issue")
                            logger.error("💡 Check hosting provider firewall settings")
                            logger.error("💡 Verify outbound HTTPS connections are allowed")
                            logger.error("💡 Contact hosting provider about PhonePe API access")
                        
                        # Exponential backoff for connection errors
                        import time
                        backoff_time = min(60, 2 ** attempt)
                        logger.info(f"⏰ Backing off for {backoff_time} seconds before retry")
                        time.sleep(backoff_time)
                        
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            # Final error with detailed troubleshooting info
                            troubleshooting_msg = (
                                f"Cannot connect to PhonePe API after trying all endpoints and retries. "
                                f"This is likely a server-side network issue. "
                                f"Error: {error_msg}. "
                                f"Troubleshooting: 1) Check firewall settings, "
                                f"2) Verify outbound HTTPS is allowed, "
                                f"3) Contact hosting provider, "
                                f"4) Check if server IP is blocked by PhonePe"
                            )
                            raise PhonePeException(troubleshooting_msg)
                        continue  # Retry
                        
                    except requests.exceptions.Timeout as e:
                        logger.error(f"PhonePe API Timeout (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {str(e)}")
                        
                        # Exponential backoff for timeouts too
                        import time
                        backoff_time = min(30, 2 ** attempt)
                        time.sleep(backoff_time)
                        
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            raise PhonePeException(f"PhonePe API timeout after trying all endpoints. This might indicate network congestion or server issues. Error: {str(e)}")
                        continue  # Retry
                        
                    except requests.exceptions.SSLError as e:
                        logger.error(f"PhonePe API SSL Error (endpoint {endpoint_idx + 1}, attempt {attempt + 1}): {str(e)}")
                        if attempt == self.max_retries - 1 and endpoint_idx == len(api_endpoints) - 1:
                            raise PhonePeException(f"SSL connection error to PhonePe API. Check SSL certificates and TLS configuration. Error: {str(e)}")
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
        Process PhonePe webhook callback with enhanced error handling
        
        Args:
            headers: Full request headers from PhonePe (can be string or dict)
            callback_body_string: Raw callback body as string
            
        Returns:
            Payment: Updated payment object
        """
        from .models import Payment, PaymentStatus
        
        try:
            logger.info(f"🔔 Processing PhonePe webhook callback")
            logger.info(f"📝 Raw callback body: {callback_body_string[:200]}...")
            logger.info(f"📋 Headers: {str(headers)[:200]}...")
            
            # Handle empty callback body
            if not callback_body_string or callback_body_string.strip() == '':
                logger.error("❌ Empty callback body received")
                raise Exception("Webhook processing failed: Empty callback body")
            
            # Parse the callback data - handle both JSON and URL-encoded
            try:
                callback_data = json.loads(callback_body_string)
                logger.info(f"✅ Parsed JSON callback data successfully")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Not JSON format: {str(e)}")
                
                # Try URL-encoded form data
                try:
                    from urllib.parse import parse_qs
                    if '=' in callback_body_string and ('&' in callback_body_string or len(callback_body_string.split('=')) == 2):
                        form_data = parse_qs(callback_body_string)
                        # Convert single-item lists to strings for easier processing
                        callback_data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}
                        logger.info(f"✅ Parsed URL-encoded callback data successfully")
                        logger.info(f"📋 Form data keys: {list(callback_data.keys())}")
                    else:
                        logger.error(f"❌ Data is neither JSON nor URL-encoded")
                        logger.error(f"📝 Raw body that failed to parse: {callback_body_string}")
                        raise Exception(f"Webhook processing failed: Invalid data format - {str(e)}")
                except Exception as parse_err:
                    logger.error(f"❌ Failed to parse URL-encoded data: {str(parse_err)}")
                    logger.error(f"📝 Raw body that failed to parse: {callback_body_string}")
                    raise Exception(f"Webhook processing failed: Invalid data format - {str(e)}")
            
            # Handle headers (can be string from Authorization header or dict from request.headers)
            x_verify_header = None
            if isinstance(headers, dict):
                x_verify_header = headers.get('X-VERIFY') or headers.get('x-verify')
            elif isinstance(headers, str):
                # If headers is the authorization string directly
                x_verify_header = headers
            
            if not x_verify_header:
                logger.warning("⚠️ Missing X-VERIFY header - proceeding without validation in development")
                if not settings.DEBUG:
                    raise Exception("Invalid webhook callback: Missing X-VERIFY header")
            
            # Decode the response if it's base64 encoded
            decoded_response = None
            if 'response' in callback_data:
                try:
                    decoded_response = json.loads(base64.b64decode(callback_data['response']).decode('utf-8'))
                    logger.info(f"✅ Decoded base64 response successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to decode base64 response: {str(e)}")
                    decoded_response = callback_data
            else:
                decoded_response = callback_data
                logger.info(f"📄 Using callback data directly (not base64 encoded)")
            
            # Extract merchant transaction ID
            merchant_transaction_id = None
            
            # Try different possible locations for merchant transaction ID
            possible_locations = [
                decoded_response.get('data', {}).get('merchantTransactionId'),
                decoded_response.get('merchantTransactionId'),
                callback_data.get('merchantTransactionId'),
                callback_data.get('data', {}).get('merchantTransactionId') if isinstance(callback_data.get('data'), dict) else None
            ]
            
            for location in possible_locations:
                if location:
                    merchant_transaction_id = location
                    break
            
            if not merchant_transaction_id:
                logger.error(f"❌ No merchant transaction ID found in callback")
                logger.error(f"📄 Decoded response: {decoded_response}")
                logger.error(f"📄 Callback data: {callback_data}")
                raise Exception("Invalid callback: No merchant transaction ID found")
            
            logger.info(f"🔍 Found merchant transaction ID: {merchant_transaction_id}")
            
            # Find payment by merchant_transaction_id
            try:
                payment = Payment.objects.get(merchant_transaction_id=merchant_transaction_id)
                logger.info(f"✅ Found payment: ID={payment.id}, Status={payment.status}")
            except Payment.DoesNotExist:
                logger.error(f"❌ Payment not found for merchant transaction ID: {merchant_transaction_id}")
                raise Exception(f"Payment not found for merchant transaction ID: {merchant_transaction_id}")
            
            # Update payment status based on callback
            transaction_data = decoded_response.get('data', {}) if isinstance(decoded_response.get('data'), dict) else decoded_response
            
            # Try different possible locations for state/status
            state = (
                transaction_data.get('state') or 
                transaction_data.get('status') or
                decoded_response.get('state') or
                decoded_response.get('status') or
                callback_data.get('state') or
                callback_data.get('status')
            )
            
            old_status = payment.status
            
            if state == 'COMPLETED':
                payment.status = PaymentStatus.SUCCESS
                logger.info(f"💰 Payment marked as SUCCESS")
            elif state in ['FAILED', 'DECLINED', 'FAILURE']:
                payment.status = PaymentStatus.FAILED
                logger.info(f"❌ Payment marked as FAILED")
            elif state == 'PENDING':
                payment.status = PaymentStatus.PENDING
                logger.info(f"⏳ Payment remains PENDING")
            else:
                logger.warning(f"⚠️ Unknown payment state: {state}")
                # Don't change status for unknown states
            
            # Update gateway response with callback data
            payment.gateway_response = payment.gateway_response or {}
            payment.gateway_response.update({
                'webhook_callback': {
                    'decoded_response': decoded_response,
                    'callback_data': callback_data,
                    'state': state,
                    'merchant_transaction_id': merchant_transaction_id,
                    'timestamp': str(timezone.now()),
                    'status_changed': old_status != payment.status
                }
            })
            
            # This save will trigger the booking creation via the overridden save method
            payment.save()
            
            logger.info(f"✅ PhonePe webhook processed successfully!")
            logger.info(f"🔄 Status change: {old_status} → {payment.status}")
            
            return payment
            
        except Exception as e:
            logger.error(f"💥 Webhook processing failed: {str(e)}")
            logger.error(f"📄 Callback body: {callback_body_string}")
            logger.error(f"📋 Headers: {headers}")
            raise Exception(f"Webhook processing failed: {str(e)}")
            
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