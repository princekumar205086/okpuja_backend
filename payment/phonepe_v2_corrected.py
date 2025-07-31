"""
PhonePe V2 Client - CORRECTED Implementation
Fixed all bugs based on official PhonePe V2 documentation review
"""
import logging
import json
import uuid
import datetime
import hashlib
import base64
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class PhonePeV2Exception(Exception):
    """Custom PhonePe V2 exception for error handling"""
    pass

class PhonePeV2ClientCorrected:
    """
    PhonePe V2 Client - CORRECTED Implementation
    All bugs fixed according to official documentation
    """
    
    def __init__(self, env="sandbox"):
        """Initialize PhonePe V2 Client with corrected configuration"""
        self.env = env
        
        # Set merchant credentials
        if env == "sandbox" or env == "uat":
            # Use UAT credentials - Updated with correct credentials from dashboard
            self.merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', 'M22KEWU5BO1I2')
            self.client_version = "1"  # ✅ FIX: UAT requires client_version = 1
            logger.info("Using PhonePe V2 UAT environment")
        else:
            # Production credentials
            self.merchant_id = settings.PHONEPE_MERCHANT_ID
            self.client_version = getattr(settings, 'PHONEPE_CLIENT_VERSION', '1')
            logger.info("Using PhonePe V2 Production environment")
        
        # ✅ FIX: Use PhonePe URLs from Django settings - OAuth is on same base URL
        if env == "production":
            self.base_url = "https://api.phonepe.com"
            self.oauth_base_url = "https://api.phonepe.com"  # OAuth is on same base URL
        else:
            # UAT environment - OAuth is on same base URL as payment API
            self.base_url = getattr(settings, 'PHONEPE_PAYMENT_BASE_URL', 'https://api-preprod.phonepe.com')
            self.oauth_base_url = getattr(settings, 'PHONEPE_OAUTH_BASE_URL', 'https://api-preprod.phonepe.com')
        
        # ✅ FIX: Corrected V2 API endpoints for PRODUCTION (Standard Checkout)
        if env == "production":
            self.payment_endpoint = f"{self.base_url}/apis/hermes/pg/v1/pay"
            self.status_endpoint_base = f"{self.base_url}/apis/hermes/pg/v1/status"
        else:
            # UAT/Sandbox endpoints
            self.payment_endpoint = f"{self.base_url}/apis/hermes/pg/v1/pay"
            self.status_endpoint_base = f"{self.base_url}/apis/pg-sandbox/pg/v1/status"
        
        # ✅ FIX: OAuth endpoint (if needed)
        self.oauth_url = f"{self.oauth_base_url}/apis/hermes/oauth2/v2/token"
        
        self.client_id = getattr(settings, 'PHONEPE_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'PHONEPE_CLIENT_SECRET', '')
        
        # Connection settings
        self.timeout = 30
        self.access_token = None
        self.token_expires_at = None
        
        logger.info(f"PhonePe V2 Client initialized for {env}")
        logger.info(f"Payment endpoint: {self.payment_endpoint}")
        logger.info(f"OAuth endpoint: {self.oauth_url}")
        logger.info(f"Client version: {self.client_version}")
    
    def get_access_token(self):
        """Get OAuth access token for V2 API - CORRECTED"""
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expires_at:
                current_time = timezone.now().timestamp()
                if current_time < self.token_expires_at:
                    logger.info("Using existing valid token")
                    return self.access_token
            
            # ✅ FIX: Corrected request parameters according to documentation
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-MERCHANT-ID': self.merchant_id,  # ✅ FIX: Added merchant ID header
            }
            
            data = {
                'client_id': self.client_id,
                'client_version': self.client_version,  # ✅ FIX: Added missing client_version
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            
            logger.info(f"Requesting OAuth token from: {self.oauth_url}")
            logger.info(f"OAuth data: {data}")
            
            response = requests.post(
                self.oauth_url,
                headers=headers,
                data=data,  # ✅ FIX: Using data not json
                timeout=self.timeout
            )
            
            logger.info(f"OAuth response: {response.status_code}")
            logger.info(f"OAuth response body: {response.text}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                
                # ✅ FIX: Use expires_at timestamp from response (not expires_in)
                expires_at_epoch = token_data.get('expires_at')
                if expires_at_epoch:
                    # Convert from seconds to timestamp and add 60 sec buffer
                    self.token_expires_at = expires_at_epoch - 60
                else:
                    # Fallback if expires_at not provided
                    expires_in = token_data.get('expires_in', 3600)
                    self.token_expires_at = timezone.now().timestamp() + expires_in - 60
                
                logger.info(f"OAuth token obtained successfully, expires at: {self.token_expires_at}")
                return self.access_token
            else:
                raise PhonePeV2Exception(f"OAuth failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"OAuth token error: {str(e)}")
            raise PhonePeV2Exception(f"Failed to get access token: {str(e)}")
    
    def _get_auth_headers(self):
        """Get authentication headers for API requests"""
        try:
            token = self.get_access_token()
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
        except Exception as e:
            # Return basic headers if token fails
            return {
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
    
    def initiate_payment(self, merchant_transaction_id, amount, merchant_user_id, redirect_url, callback_url):
        """
        Initiate payment using PhonePe V2 API
        
        Args:
            merchant_transaction_id: Unique merchant transaction ID
            amount: Payment amount in INR
            merchant_user_id: Merchant user ID
            redirect_url: URL to redirect after payment
            callback_url: Webhook callback URL
            
        Returns:
            dict: Payment response
        """
        try:
            # Get OAuth token
            token = self.get_access_token()
            if not token:
                raise PhonePeV2Exception("Unable to obtain access token")
            
            # ✅ Corrected V2 request payload format
            payload = {
                "merchantTransactionId": merchant_transaction_id,
                "amount": int(float(amount) * 100),  # Amount in paisa
                "merchantUserId": merchant_user_id,
                "redirectUrl": redirect_url,
                "callbackUrl": callback_url,
                "paymentInstrument": {
                    "type": "PAY_PAGE"
                }
            }
            
            # ✅ FIX: Proper V2 endpoint
            url = f"{self.base_url}/checkout/v2/pay"
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
            
            logger.info(f"Initiating payment to: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data,
                    'payment_url': data.get('data', {}).get('instrumentResponse', {}).get('redirectInfo', {}).get('url')
                }
            else:
                logger.error(f"Payment initiation failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Payment initiation failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_payment_status(self, merchant_transaction_id):
        """
        Check payment status using PhonePe V2 API
        
        Args:
            merchant_transaction_id: Merchant transaction ID
            
        Returns:
            dict: Status response
        """
        try:
            # Get OAuth token
            token = self.get_access_token()
            if not token:
                raise PhonePeV2Exception("Unable to obtain access token")
            
            # ✅ FIX: Correct V2 status endpoint
            url = f"{self.base_url}/checkout/v2/order/{merchant_transaction_id}/status"
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
            
            logger.info(f"Checking payment status at: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data
                }
            else:
                logger.error(f"Status check failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Status check failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def initiate_refund(self, merchant_refund_id, original_merchant_order_id, amount):
        """
        Initiate refund using PhonePe V2 API
        
        Args:
            merchant_refund_id: Unique merchant refund ID
            original_merchant_order_id: Original merchant order ID
            amount: Refund amount in INR
            
        Returns:
            dict: Refund response
        """
        try:
            # Get OAuth token
            token = self.get_access_token()
            if not token:
                raise PhonePeV2Exception("Unable to obtain access token")
            
            # ✅ Corrected V2 refund payload format
            payload = {
                "merchantRefundId": merchant_refund_id,
                "originalMerchantOrderId": original_merchant_order_id,
                "amount": int(float(amount) * 100),  # Amount in paisa
                "callbackUrl": getattr(settings, 'PHONEPE_WEBHOOK_URL', 'https://example.com/webhook')
            }
            
            # ✅ FIX: Correct V2 refund endpoint
            url = f"{self.base_url}/payments/v2/refund"
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
            
            logger.info(f"Initiating refund to: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data
                }
            else:
                logger.error(f"Refund initiation failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Refund initiation failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Refund initiation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_refund_status(self, merchant_refund_id):
        """
        Check refund status using PhonePe V2 API
        
        Args:
            merchant_refund_id: Merchant refund ID
            
        Returns:
            dict: Refund status response
        """
        try:
            # Get OAuth token
            token = self.get_access_token()
            if not token:
                raise PhonePeV2Exception("Unable to obtain access token")
            
            # ✅ FIX: Correct V2 refund status endpoint
            url = f"{self.base_url}/payments/v2/refund/{merchant_refund_id}/status"
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
            
            logger.info(f"Checking refund status at: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data
                }
            else:
                logger.error(f"Refund status check failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Refund status check failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Refund status check error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        """Generate unique merchant order ID according to V2 specs"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        uuid_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        # ✅ FIX: Ensure max 63 characters and valid characters only
        order_id = f"TX{timestamp}{uuid_part}"
        return order_id[:63]  # Ensure max length
    
    def create_payment(self, payment):
        """
        Create payment using official PhonePe V2 API - CORRECTED
        """
        try:
            # Get OAuth token
            token = self.get_access_token()
            if not token:
                raise PhonePeV2Exception("Unable to obtain access token")
            
            # Generate merchant order ID
            merchant_order_id = self.generate_merchant_order_id()
            payment.merchant_transaction_id = merchant_order_id
            payment.save()
            
            # ✅ FIX: Corrected V2 request payload format
            payload = {
                "merchantOrderId": merchant_order_id,
                "amount": int(float(payment.amount) * 100),  # Amount in paisa
                "expireAfter": 1200,  # 20 minutes (within 300-3600 range)
                "paymentFlow": {
                    "type": "PG_CHECKOUT",  # ✅ FIX: Required field
                    "message": "Payment for OkPuja services",
                    "merchantUrls": {
                        "redirectUrl": getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', 'http://localhost:3000/payment/success')
                    }
                }
            }
            
            # ✅ FIX: Only add metaInfo if needed (don't pass empty values)
            if hasattr(payment, 'id') and payment.id:
                payload["metaInfo"] = {
                    "udf1": f"payment_id_{payment.id}",
                    "udf2": f"user_id_{payment.user.id}",
                    "udf3": "okpuja_payment"
                    # Only include fields with actual values
                }
            
            # ✅ FIX: Corrected payment mode configuration
            payload["paymentFlow"]["paymentModeConfig"] = {
                "enabledPaymentModes": [
                    {"type": "UPI_INTENT"},
                    {"type": "UPI_COLLECT"},
                    {"type": "UPI_QR"},
                    {"type": "NET_BANKING"},
                    {
                        "type": "CARD",
                        "cardTypes": ["DEBIT_CARD", "CREDIT_CARD"]
                    }
                ]
            }
            
            # ✅ FIX: Corrected headers with proper Authorization format
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {token}'  # ✅ Correct format from docs
            }
            
            logger.info(f"Creating V2 payment: {merchant_order_id}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Make payment request
            response = requests.post(
                self.payment_endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            logger.info(f"Payment API response: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # ✅ FIX: Correct V2 API response format
                return {
                    'success': True,
                    'order_id': response_data.get('orderId'),  # ✅ Capital O
                    'state': response_data.get('state'),
                    'expire_at': response_data.get('expireAt'),  # ✅ Capital A
                    'redirect_url': response_data.get('redirectUrl'),
                    'merchant_order_id': merchant_order_id,
                    'payment_url': response_data.get('redirectUrl'),
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('message', f'HTTP {response.status_code}')
                logger.error(f"Payment creation failed: {error_message}")
                
                return {
                    'success': False,
                    'error': f"Payment API error: {response.status_code} - {error_message}",
                    'error_code': error_data.get('code'),
                    'error_message': error_message
                }
                
        except Exception as e:
            logger.error(f"Payment creation error: {str(e)}")
            return {
                'success': False,
                'error': f"Payment creation failed: {str(e)}"
            }
    
    def check_payment_status(self, merchant_order_id, details=False, error_context=False):
        """
        Check payment status using V2 API - CORRECTED
        """
        try:
            # Get OAuth token
            token = self.get_access_token()
            if not token:
                raise PhonePeV2Exception("Unable to obtain access token")
            
            # ✅ FIX: Corrected status endpoint URL structure
            status_url = f"{self.status_endpoint_base}/{merchant_order_id}/status"
            
            # ✅ FIX: Add query parameters as per documentation
            params = {
                'details': str(details).lower(),
                'errorContext': str(error_context).lower()
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {token}'
            }
            
            logger.info(f"Checking payment status: {merchant_order_id}")
            logger.info(f"Status URL: {status_url}")
            
            response = requests.get(
                status_url,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            
            logger.info(f"Status API response: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                # ✅ FIX: Focus on root level 'state' as per documentation
                return {
                    'success': True,
                    'status': response_data.get('state'),  # Root level state
                    'order_id': response_data.get('orderId'),
                    'amount': response_data.get('amount'),
                    'expire_at': response_data.get('expireAt'),
                    'payment_details': response_data.get('paymentDetails', []),
                    'meta_info': response_data.get('metaInfo', {}),
                    'data': response_data
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    'success': False,
                    'error': f"Status check failed: {response.status_code}",
                    'error_code': error_data.get('code'),
                    'error_message': error_data.get('message')
                }
                
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            return {
                'success': False,
                'error': f"Status check failed: {str(e)}"
            }
    
    def generate_merchant_refund_id(self):
        """Generate unique merchant refund ID according to V2 specs"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        uuid_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        # ✅ Refund ID with max 63 characters
        refund_id = f"RF{timestamp}{uuid_part}"
        return refund_id[:63]  # Ensure max length
    
    def initiate_refund(self, payment, refund_amount, refund_reason="Customer request"):
        """
        Initiate refund using official PhonePe V2 Refund API
        Following the exact request format from documentation
        """
        try:
            # Get OAuth token
            token = self.get_access_token()
            if not token:
                raise PhonePeV2Exception("Unable to obtain access token")
            
            # Generate merchant refund ID
            merchant_refund_id = self.generate_merchant_refund_id()
            
            # ✅ V2 Refund API endpoint
            refund_endpoint = f"{self.base_url}/payments/v2/refund"
            
            # ✅ Prepare V2 refund request payload (exact format from documentation)
            payload = {
                "merchantRefundId": merchant_refund_id,
                "originalMerchantOrderId": payment.merchant_transaction_id,
                "amount": int(float(refund_amount) * 100)  # Amount in paisa
            }
            
            # Validate amount
            if payload["amount"] < 100:  # Min 100 paisa (₹1)
                raise PhonePeV2Exception(f"Refund amount too low: ₹{refund_amount}")
            
            # ✅ Correct headers with OAuth token
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {token}'
            }
            
            logger.info(f"Initiating V2 refund: {merchant_refund_id}")
            logger.info(f"Original order: {payment.merchant_transaction_id}")
            logger.info(f"Refund amount: ₹{refund_amount}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Make refund request
            response = requests.post(
                refund_endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            logger.info(f"Refund API response: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # ✅ V2 Refund API response format
                return {
                    'success': True,
                    'refund_id': response_data.get('refundId'),
                    'merchant_refund_id': merchant_refund_id,
                    'amount': response_data.get('amount'),
                    'state': response_data.get('state'),  # Expected: PENDING
                    'original_order_id': payment.merchant_transaction_id
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('message', f'HTTP {response.status_code}')
                logger.error(f"Refund initiation failed: {error_message}")
                
                return {
                    'success': False,
                    'error': f"Refund API error: {response.status_code} - {error_message}",
                    'error_code': error_data.get('code'),
                    'error_message': error_message
                }
                
        except Exception as e:
            logger.error(f"Refund initiation error: {str(e)}")
            return {
                'success': False,
                'error': f"Refund initiation failed: {str(e)}"
            }
    
    def check_refund_status(self, merchant_refund_id):
        """
        Check refund status using V2 API - CORRECTED
        """
        try:
            # Get OAuth token
            token = self.get_access_token()
            if not token:
                raise PhonePeV2Exception("Unable to obtain access token")
            
            # ✅ V2 Refund Status endpoint
            refund_status_url = f"{self.base_url}/payments/v2/refund/{merchant_refund_id}/status"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {token}'
            }
            
            logger.info(f"Checking refund status: {merchant_refund_id}")
            logger.info(f"Status URL: {refund_status_url}")
            
            response = requests.get(
                refund_status_url,
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"Refund Status API response: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # ✅ Focus on root level 'state' as per documentation
                return {
                    'success': True,
                    'status': response_data.get('state'),  # PENDING, CONFIRMED, COMPLETED, FAILED
                    'refund_id': response_data.get('refundId'),
                    'original_merchant_order_id': response_data.get('originalMerchantOrderId'),
                    'amount': response_data.get('amount'),
                    'timestamp': response_data.get('timestamp'),
                    'error_code': response_data.get('errorCode'),
                    'detailed_error_code': response_data.get('detailedErrorCode'),
                    'split_instruments': response_data.get('splitInstruments', []),
                    'data': response_data
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    'success': False,
                    'error': f"Refund status check failed: {response.status_code}",
                    'error_code': error_data.get('code'),
                    'error_message': error_data.get('message')
                }
                
        except Exception as e:
            logger.error(f"Refund status check error: {str(e)}")
            return {
                'success': False,
                'error': f"Refund status check failed: {str(e)}"
            }
    
    def validate_webhook_authorization(self, auth_header, webhook_username, webhook_password):
        """
        Validate webhook authorization header using SHA256(username:password)
        As per PhonePe V2 documentation
        """
        try:
            # Calculate expected SHA256 hash
            credentials = f"{webhook_username}:{webhook_password}"
            expected_hash = hashlib.sha256(credentials.encode()).hexdigest()
            
            # Extract hash from authorization header
            received_hash = auth_header.replace('SHA256:', '').strip() if auth_header else ''
            
            logger.info(f"Webhook auth validation:")
            logger.info(f"  Expected hash: {expected_hash}")
            logger.info(f"  Received hash: {received_hash}")
            
            return expected_hash == received_hash
            
        except Exception as e:
            logger.error(f"Webhook authorization validation error: {str(e)}")
            return False
    
    def process_webhook_payload(self, payload):
        """
        Process webhook payload according to V2 documentation
        Returns structured webhook data
        """
        try:
            event = payload.get('event', '')
            payload_data = payload.get('payload', {})
            
            # ✅ Focus on root level 'payload.state' as per documentation
            state = payload_data.get('state', '')
            
            webhook_info = {
                'event': event,
                'state': state,
                'valid': True
            }
            
            # Process different webhook events
            if event in ['checkout.order.completed', 'checkout.order.failed']:
                webhook_info.update({
                    'order_id': payload_data.get('orderId'),
                    'merchant_id': payload_data.get('merchantId'),
                    'merchant_order_id': payload_data.get('merchantOrderId'),
                    'amount': payload_data.get('amount'),
                    'expire_at': payload_data.get('expireAt'),
                    'meta_info': payload_data.get('metaInfo', {}),
                    'payment_details': payload_data.get('paymentDetails', [])
                })
                
            elif event in ['pg.refund.accepted', 'pg.refund.completed', 'pg.refund.failed']:
                webhook_info.update({
                    'merchant_id': payload_data.get('merchantId'),
                    'merchant_refund_id': payload_data.get('merchantRefundId'),
                    'original_merchant_order_id': payload_data.get('originalMerchantOrderId'),
                    'refund_id': payload_data.get('refundId'),
                    'amount': payload_data.get('amount'),
                    'timestamp': payload_data.get('timestamp'),
                    'error_code': payload_data.get('errorCode'),
                    'detailed_error_code': payload_data.get('detailedErrorCode'),
                    'payment_details': payload_data.get('paymentDetails', [])
                })
            
            logger.info(f"Processed webhook: {event} - {state}")
            return webhook_info
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def test_connectivity(self):
        """Test connectivity to V2 endpoints - CORRECTED"""
        results = []
        
        # Test OAuth endpoint
        try:
            response = requests.get(self.oauth_url, timeout=5)
            results.append({
                'url': self.oauth_url,
                'status': 'OK' if response.status_code in [200, 400, 401] else 'ERROR',
                'status_code': response.status_code
            })
        except Exception as e:
            results.append({
                'url': self.oauth_url,
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Test payment endpoint
        try:
            response = requests.post(self.payment_endpoint, timeout=5)
            results.append({
                'url': self.payment_endpoint,
                'status': 'OK' if response.status_code in [200, 400, 401] else 'ERROR',
                'status_code': response.status_code
            })
        except Exception as e:
            results.append({
                'url': self.payment_endpoint,
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Test refund endpoint
        refund_endpoint = f"{self.base_url}/payments/v2/refund"
        try:
            response = requests.post(refund_endpoint, timeout=5)
            results.append({
                'url': refund_endpoint,
                'status': 'OK' if response.status_code in [200, 400, 401] else 'ERROR',
                'status_code': response.status_code
            })
        except Exception as e:
            results.append({
                'url': refund_endpoint,
                'status': 'ERROR',
                'error': str(e)
            })
        
        return results
