import logging
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

class PhonePeGatewayV2:
    """
    PhonePe Payment Gateway V2 Implementation
    Based on official PhonePe V2 API documentation
    """
    
    def __init__(self):
        """Initialize PhonePe Gateway V2 with OAuth2 authentication"""
        self.client_id = settings.PHONEPE_CLIENT_ID
        self.client_secret = settings.PHONEPE_CLIENT_SECRET
        self.client_version = settings.PHONEPE_CLIENT_VERSION
        
        # V2 API URLs
        self.auth_base_url = settings.PHONEPE_AUTH_BASE_URL
        self.payment_base_url = settings.PHONEPE_PAYMENT_BASE_URL
        
        # Connection settings
        self.timeout = int(getattr(settings, 'PHONEPE_TIMEOUT', 180))
        self.max_retries = int(getattr(settings, 'PHONEPE_MAX_RETRIES', 7))
        self.ssl_verify = getattr(settings, 'PHONEPE_SSL_VERIFY', 'True').lower() == 'true'
        
        # Environment detection
        self.is_production = getattr(settings, 'PHONEPE_ENV', 'UAT') == 'PRODUCTION'
        
        # Access token cache
        self._access_token = None
        self._token_expires_at = None
        
        logger.info(f"PhonePe Gateway V2 initialized: client_id={self.client_id}, auth_url={self.auth_base_url}, timeout={self.timeout}s")
        
    def get_access_token(self):
        """
        Get OAuth2 access token for PhonePe V2 API
        Implements token caching to avoid unnecessary API calls
        
        Returns:
            str: Access token
        """
        try:
            # Check if we have a valid cached token
            if self._access_token and self._token_expires_at:
                current_time = datetime.datetime.now().timestamp()
                # Refresh token if it expires in next 5 minutes
                if current_time < (self._token_expires_at - 300):
                    logger.info("Using cached access token")
                    return self._access_token
            
            logger.info("Fetching new access token from PhonePe")
            
            # Prepare OAuth2 request
            auth_url = f"{self.auth_base_url}/v1/oauth/token"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'User-Agent': 'okpuja-backend/1.0'
            }
            
            data = {
                'client_id': self.client_id,
                'client_version': self.client_version,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            
            logger.info(f"Making OAuth2 request to: {auth_url}")
            logger.info(f"Request data: client_id={self.client_id}, client_version={self.client_version}")
            
            response = requests.post(
                auth_url,
                headers=headers,
                data=data,
                timeout=self.timeout,
                verify=self.ssl_verify
            )
            
            logger.info(f"OAuth2 Response Status: {response.status_code}")
            logger.info(f"OAuth2 Response: {response.text[:500]}...")
            
            if response.status_code == 200:
                token_data = response.json()
                
                self._access_token = token_data.get('access_token')
                self._token_expires_at = token_data.get('expires_at')
                
                if not self._access_token:
                    raise PhonePeException("No access token received from PhonePe")
                
                logger.info(f"✅ Access token obtained successfully (expires at: {self._token_expires_at})")
                return self._access_token
                
            else:
                error_msg = f"OAuth2 failed with status {response.status_code}: {response.text}"
                logger.error(f"❌ {error_msg}")
                raise PhonePeException(error_msg)
                
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Cannot connect to PhonePe OAuth2 endpoint: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise PhonePeException(error_msg)
        except Exception as e:
            error_msg = f"OAuth2 authentication failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise PhonePeException(error_msg)

    def generate_merchant_order_id(self):
        """Generate a unique merchant order ID"""
        uuid_part = str(uuid.uuid4()).split('-')[0].upper()
        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        return f"TX{now}{uuid_part}"

    def initiate_payment(self, payment):
        """
        Initiate payment using PhonePe V2 API
        
        Args:
            payment: Payment model instance
            
        Returns:
            dict: Response containing checkout URL and payment details
        """
        try:
            logger.info(f"🚀 Starting PhonePe V2 payment initiation")
            logger.info(f"Payment ID: {payment.id}, Amount: ₹{payment.amount}")
            
            # Get access token
            access_token = self.get_access_token()
            
            # Prepare merchant order ID
            merchant_order_id = self.generate_merchant_order_id()
            payment.merchant_transaction_id = merchant_order_id
            payment.save()
            
            logger.info(f"Generated merchant order ID: {merchant_order_id}")
            
            # Prepare redirect URL
            redirect_url = f"{settings.PHONEPE_SUCCESS_REDIRECT_URL}?payment_id={payment.id}"
            
            # Create payment payload according to V2 API spec
            payload = {
                "merchantOrderId": merchant_order_id,
                "amount": int(float(payment.amount) * 100),  # Convert to paisa
                "expireAfter": 1200,  # 20 minutes
                "paymentFlow": {
                    "type": "PG_CHECKOUT",
                    "message": f"Payment for OkPuja booking - Order #{payment.id}",
                    "merchantUrls": {
                        "redirectUrl": redirect_url
                    }
                },
                "metaInfo": {
                    "udf1": f"payment_id_{payment.id}",
                    "udf2": f"user_id_{payment.user.id}",
                    "udf3": f"cart_id_{getattr(payment, 'cart_id', '')}",
                    "udf4": "okpuja_booking",
                    "udf5": f"amount_{payment.amount}"
                }
            }
            
            # Validate payload
            if payload["amount"] <= 0:
                raise PhonePeException(f"Invalid payment amount: {payment.amount}")
            
            logger.info(f"Payment payload prepared: {json.dumps(payload, indent=2)}")
            
            # Prepare request headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {access_token}',
                'Accept': 'application/json',
                'User-Agent': 'okpuja-backend/1.0'
            }
            
            # API endpoint for payment creation
            payment_url = f"{self.payment_base_url}/checkout/v2/pay"
            
            logger.info(f"Making payment request to: {payment_url}")
            
            # Make payment request with retry logic
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Payment attempt {attempt + 1}/{self.max_retries}")
                    
                    response = requests.post(
                        payment_url,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout,
                        verify=self.ssl_verify
                    )
                    
                    logger.info(f"Payment API Status: {response.status_code}")
                    logger.info(f"Payment API Response: {response.text[:500]}...")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        
                        # Check if payment was created successfully
                        if response_data.get('orderId') and response_data.get('redirectUrl'):
                            checkout_url = response_data['redirectUrl']
                            order_id = response_data['orderId']
                            
                            # Update payment with gateway response
                            payment.gateway_response = response_data
                            payment.phonepe_payment_id = order_id
                            payment.save()
                            
                            logger.info(f"✅ PhonePe V2 payment created successfully!")
                            logger.info(f"Order ID: {order_id}")
                            logger.info(f"Checkout URL: {checkout_url}")
                            
                            return {
                                'success': True,
                                'payment_url': checkout_url,
                                'checkout_url': checkout_url,
                                'transaction_id': payment.transaction_id,
                                'merchant_transaction_id': merchant_order_id,
                                'phonepe_order_id': order_id,
                                'order_id': order_id
                            }
                        else:
                            error_msg = response_data.get('message', 'Payment creation failed')
                            error_code = response_data.get('code', 'UNKNOWN')
                            logger.error(f"PhonePe payment creation failed: {error_msg} (Code: {error_code})")
                            
                            # Don't retry for business logic errors
                            if error_code in ['BAD_REQUEST', 'INVALID_MERCHANT', 'AMOUNT_LIMIT_EXCEEDED']:
                                raise PhonePeException(f"PhonePe Error: {error_msg} (Code: {error_code})")
                            
                            if attempt == self.max_retries - 1:
                                raise PhonePeException(f"PhonePe Error: {error_msg} (Code: {error_code})")
                                
                    elif response.status_code == 401:
                        logger.warning("Access token expired, refreshing...")
                        # Clear cached token and retry
                        self._access_token = None
                        self._token_expires_at = None
                        access_token = self.get_access_token()
                        headers['Authorization'] = f'O-Bearer {access_token}'
                        continue
                        
                    else:
                        logger.error(f"PhonePe API HTTP Error: {response.status_code} - {response.text}")
                        if attempt == self.max_retries - 1:
                            raise PhonePeException(f"PhonePe API HTTP Error: {response.status_code}")
                        continue
                        
                except requests.exceptions.ConnectionError as e:
                    error_msg = str(e)
                    logger.error(f"PhonePe API Connection Error (attempt {attempt + 1}): {error_msg}")
                    
                    if "Connection refused" in error_msg:
                        logger.error("🚨 Connection refused - checking network connectivity")
                        
                        # Test connectivity to PhonePe domains
                        test_connectivity_results = self.test_connectivity()
                        logger.info(f"Connectivity test results: {test_connectivity_results}")
                    
                    if attempt == self.max_retries - 1:
                        troubleshooting_msg = (
                            f"Cannot connect to PhonePe V2 API. "
                            f"Error: {error_msg}. "
                            f"Please check: 1) Internet connectivity, "
                            f"2) Firewall settings, "
                            f"3) DNS resolution for {self.payment_base_url}"
                        )
                        raise PhonePeException(troubleshooting_msg)
                        
                    # Exponential backoff
                    import time
                    backoff_time = min(30, 2 ** attempt)
                    logger.info(f"⏰ Backing off for {backoff_time} seconds")
                    time.sleep(backoff_time)
                    continue
                    
                except requests.exceptions.Timeout as e:
                    logger.error(f"PhonePe API Timeout (attempt {attempt + 1}): {str(e)}")
                    if attempt == self.max_retries - 1:
                        raise PhonePeException(f"PhonePe API timeout: {str(e)}")
                    continue
                    
                except Exception as e:
                    logger.error(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
                    if attempt == self.max_retries - 1:
                        raise PhonePeException(f"Unexpected error: {str(e)}")
                    continue
                    
        except PhonePeException:
            raise
        except Exception as e:
            logger.error(f"Critical error in PhonePe V2 payment initiation: {str(e)}")
            raise PhonePeException(f"Critical payment system error: {str(e)}")

    def test_connectivity(self):
        """Test connectivity to PhonePe V2 API endpoints"""
        connectivity_results = []
        
        test_endpoints = [
            self.auth_base_url,
            self.payment_base_url,
            "https://api-preprod.phonepe.com",
            "https://api.phonepe.com"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(endpoint, timeout=10, verify=self.ssl_verify)
                connectivity_results.append({
                    'endpoint': endpoint,
                    'status': 'connected',
                    'response_code': response.status_code
                })
                logger.info(f"✅ {endpoint}: Connected (Status: {response.status_code})")
            except requests.exceptions.ConnectionError:
                connectivity_results.append({
                    'endpoint': endpoint,
                    'status': 'connection_refused',
                    'error': 'Connection refused'
                })
                logger.error(f"❌ {endpoint}: Connection refused")
            except Exception as e:
                connectivity_results.append({
                    'endpoint': endpoint,
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"❌ {endpoint}: {str(e)}")
        
        return connectivity_results

    def check_payment_status(self, merchant_order_id):
        """
        Check payment status using PhonePe V2 API
        
        Args:
            merchant_order_id: Merchant order ID
            
        Returns:
            dict: Payment status response
        """
        try:
            access_token = self.get_access_token()
            
            # Status check endpoint
            status_url = f"{self.payment_base_url}/checkout/v2/status/{merchant_order_id}"
            
            headers = {
                'Authorization': f'O-Bearer {access_token}',
                'Accept': 'application/json',
                'User-Agent': 'okpuja-backend/1.0'
            }
            
            response = requests.get(status_url, headers=headers, timeout=self.timeout)
            response_data = response.json()
            
            logger.info(f"PhonePe V2 status check response: {response_data}")
            return response_data
            
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            raise PhonePeException(f"Status check failed: {str(e)}")

    def process_webhook(self, headers, callback_body_string):
        """
        Process PhonePe V2 webhook callback
        
        Args:
            headers: Request headers
            callback_body_string: Raw callback body
            
        Returns:
            Payment: Updated payment object
        """
        from .models import Payment, PaymentStatus
        
        try:
            logger.info(f"🔔 Processing PhonePe V2 webhook callback")
            logger.info(f"📝 Raw callback: {callback_body_string[:200]}...")
            
            # Parse callback data
            if not callback_body_string:
                raise Exception("Empty webhook callback")
            
            try:
                callback_data = json.loads(callback_body_string)
            except json.JSONDecodeError:
                # Try form data parsing
                from urllib.parse import parse_qs
                form_data = parse_qs(callback_body_string)
                callback_data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}
            
            # Extract merchant order ID
            merchant_order_id = (
                callback_data.get('merchantOrderId') or
                callback_data.get('data', {}).get('merchantOrderId') or
                callback_data.get('merchantTransactionId') or # Check alternative field names
                callback_data.get('transactionId')
            )
            
            if not merchant_order_id:
                # Try to parse nested structures that PhonePe might send
                if 'response' in callback_data and callback_data['response']:
                    try:
                        import base64
                        decoded_data = json.loads(base64.b64decode(callback_data['response']).decode('utf-8'))
                        merchant_order_id = decoded_data.get('merchantOrderId') or decoded_data.get('merchantTransactionId')
                        logger.info(f"Found merchant ID in base64 response: {merchant_order_id}")
                    except Exception as decode_err:
                        logger.error(f"Failed to decode base64 response: {str(decode_err)}")
            
            if not merchant_order_id:
                logger.error(f"No merchant order ID found in webhook data: {callback_data}")
                raise Exception("No merchant order ID found in webhook")
            
            logger.info(f"🔍 Processing webhook for order: {merchant_order_id}")
            
            # Find payment
            try:
                payment = Payment.objects.get(merchant_transaction_id=merchant_order_id)
            except Payment.DoesNotExist:
                raise Exception(f"Payment not found for order ID: {merchant_order_id}")
            
            # Extract payment state - CHECK MULTIPLE POSSIBLE FIELD NAMES
            state = None
            
            # Check various possible field locations based on PhonePe webhook format
            possible_state_locations = [
                callback_data.get('state'),
                callback_data.get('status'),
                callback_data.get('code'),
                callback_data.get('transactionStatus'),
                callback_data.get('data', {}).get('state') if isinstance(callback_data.get('data'), dict) else None,
                callback_data.get('data', {}).get('status') if isinstance(callback_data.get('data'), dict) else None,
                callback_data.get('data', {}).get('code') if isinstance(callback_data.get('data'), dict) else None,
            ]
            
            # PhonePe V2 uses checkout specific status codes
            for potential_state in possible_state_locations:
                if potential_state:
                    state = potential_state
                    break
            
            # For PhonePe V2, try to check if the state is encoded in any field
            if not state and 'response' in callback_data:
                try:
                    import base64
                    decoded_data = json.loads(base64.b64decode(callback_data['response']).decode('utf-8'))
                    state = decoded_data.get('code') or decoded_data.get('state')
                    logger.info(f"Found state in base64 response: {state}")
                except:
                    pass
            
            logger.info(f"📊 Payment state extracted from webhook: {state}")
            
            # Update payment status - Handle PhonePe V2 state mappings
            old_status = payment.status
            
            # Map PhonePe V2 status codes to our payment states
            v2_success_states = [
                'COMPLETED', 'SUCCESS', 'PAYMENT_SUCCESS', 
                'AUTHORIZED', 'CHECKOUT_ORDER_COMPLETED',
                'PAYMENT_AUTHORIZED', 'PAYMENT_CAPTURED'
            ]
            
            v2_failure_states = [
                'FAILED', 'FAILURE', 'ERROR', 'DECLINED', 
                'CHECKOUT_ORDER_FAILED', 'PAYMENT_FAILED',
                'PAYMENT_ERROR', 'PAYMENT_DECLINED', 
                'CHECKOUT_TRANSACTION_ATTEMPT_FAILED'
            ]
            
            if state and any(success_state in state.upper() for success_state in v2_success_states):
                payment.status = PaymentStatus.SUCCESS
                logger.info(f"💰 Payment marked as SUCCESS based on state: {state}")
            elif state and any(failure_state in state.upper() for failure_state in v2_failure_states):
                payment.status = PaymentStatus.FAILED
                logger.info(f"❌ Payment marked as FAILED based on state: {state}")
            elif state and 'PENDING' in state.upper():
                payment.status = PaymentStatus.PENDING
                logger.info(f"⏳ Payment remains PENDING based on state: {state}")
            
            # Update gateway response
            payment.gateway_response = payment.gateway_response or {}
            payment.gateway_response.update({
                'v2_webhook_callback': {
                    'callback_data': callback_data,
                    'state': state,
                    'timestamp': str(timezone.now()),
                    'status_changed': old_status != payment.status
                }
            })
            
            # Save payment to update status
            payment.save()
            
            # If payment is now successful, create booking
            if payment.status == PaymentStatus.SUCCESS and not payment.booking:
                try:
                    booking = payment.create_booking_from_cart()
                    logger.info(f"✅ Created booking {booking.id} from successful payment {payment.id}")
                except Exception as booking_error:
                    logger.error(f"❌ Failed to create booking from payment {payment.id}: {str(booking_error)}")
            
            logger.info(f"✅ PhonePe V2 webhook processed: {old_status} → {payment.status}")
            return payment
            
        except Exception as e:
            logger.error(f"💥 V2 webhook processing failed: {str(e)}")
            raise Exception(f"V2 webhook processing failed: {str(e)}")


def get_payment_gateway_v2(name='phonepe'):
    """
    Factory function to get PhonePe V2 payment gateway instance
    
    Args:
        name: Gateway name (default: 'phonepe')
        
    Returns:
        Gateway instance
    """
    gateways = {
        'phonepe': PhonePeGatewayV2,
    }
    
    gateway_class = gateways.get(name.lower())
    if not gateway_class:
        raise ValueError(f"Unknown payment gateway: {name}")
    
    return gateway_class()
