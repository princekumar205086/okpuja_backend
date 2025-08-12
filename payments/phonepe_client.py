"""
Clean PhonePe Payment Gateway Client
Based on Official Postman Documentation
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class PhonePePaymentClient:
    """
    Clean PhonePe Payment Gateway Client
    Based on Official PhonePe Postman Documentation
    """
    
    def __init__(self, environment="uat"):
        """Initialize PhonePe client with environment settings"""
        self.environment = environment
        self.access_token = None
        self.token_expires_at = None
        
        # Set environment URLs based on Postman documentation
        if environment == "production":
            # Production environment
            self.oauth_base_url = "https://api.phonepe.com/apis/identity-manager"
            self.pg_base_url = "https://api.phonepe.com/apis/pg"
            self.client_id = getattr(settings, 'PHONEPE_CLIENT_ID', '')
            self.client_secret = getattr(settings, 'PHONEPE_CLIENT_SECRET', '')
        else:
            # UAT environment (default)
            self.oauth_base_url = "https://api-preprod.phonepe.com/apis/identity-manager"
            self.pg_base_url = "https://api-preprod.phonepe.com/apis/pg-sandbox"
            self.client_id = getattr(settings, 'PHONEPE_CLIENT_ID', '')
            self.client_secret = getattr(settings, 'PHONEPE_CLIENT_SECRET', '')
        
        self.client_version = getattr(settings, 'PHONEPE_CLIENT_VERSION', '1')
        self.merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', '')
        
        # API Endpoints based on Postman documentation
        self.oauth_url = f"{self.oauth_base_url}/v1/oauth/token"
        self.payment_url = f"{self.pg_base_url}/checkout/v2/pay"
        self.status_url = f"{self.pg_base_url}/checkout/v2/order"
        self.refund_url = f"{self.pg_base_url}/payments/v2/refund"
        self.refund_status_url = f"{self.pg_base_url}/payments/v2/refund"
        
        logger.info(f"PhonePe Client initialized for {environment} environment")
        logger.info(f"OAuth URL: {self.oauth_url}")
        logger.info(f"Payment URL: {self.payment_url}")
    
    def get_access_token(self):
        """
        Get OAuth access token using client credentials
        Based on Postman: POST /apis/pg-sandbox/v1/oauth/token
        """
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expires_at:
                if timezone.now() < self.token_expires_at:
                    return self.access_token
            
            # Request new token
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'client_id': self.client_id,
                'client_version': self.client_version,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            
            logger.info(f"Requesting OAuth token from: {self.oauth_url}")
            
            response = requests.post(
                self.oauth_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = timezone.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("OAuth token obtained successfully")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OAuth request failed: {e}")
            raise Exception(f"Failed to get access token: {e}")
        except Exception as e:
            logger.error(f"OAuth error: {e}")
            raise Exception(f"OAuth failed: {e}")
    
    def create_payment_url(self, merchant_order_id, amount, redirect_url, timeout_minutes=5, **kwargs):
        """
        Create payment URL using PhonePe Checkout API with professional timeout management
        Based on Postman: POST /apis/pg-sandbox/checkout/v2/pay
        
        Args:
            merchant_order_id (str): Unique order ID
            amount (int): Amount in paisa (₹1 = 100 paisa)
            redirect_url (str): URL to redirect after payment
            timeout_minutes (int): Professional timeout in minutes (default: 5)
            **kwargs: Additional optional parameters
        
        Returns:
            dict: Response containing payment URL
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {access_token}'
            }
            
            # Calculate professional expiry time (in seconds)
            expire_after_seconds = timeout_minutes * 60
            
            # Prepare payload based on Postman documentation with professional timeout
            payload = {
                "merchantOrderId": merchant_order_id,
                "amount": amount,
                "expireAfter": expire_after_seconds,  # Professional timeout
                "paymentFlow": {
                    "type": "PG_CHECKOUT",
                    "message": kwargs.get('payment_message', f"Payment for order {merchant_order_id}"),
                    "merchantUrls": {
                        "redirectUrl": redirect_url
                    }
                }
            }
            
            # Add optional metadata
            if kwargs.get('meta_info'):
                payload["metaInfo"] = kwargs['meta_info']
            
            logger.info(f"Creating payment URL with {timeout_minutes}min timeout for order: {merchant_order_id}")
            
            response = requests.post(
                self.payment_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Payment URL created successfully with professional timeout for order: {merchant_order_id}")
            
            # Extract the payment URL from response
            payment_url = result.get('redirectUrl') or result.get('url')
            
            return {
                'success': True,
                'data': result,
                'payment_url': payment_url,  # The checkout URL for redirect
                'order_id': merchant_order_id,
                'timeout_minutes': timeout_minutes,
                'expires_after_seconds': expire_after_seconds
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment URL creation failed: {e}")
            return {
                'success': False,
                'error': f"Failed to create payment URL: {e}"
            }
        except Exception as e:
            logger.error(f"Payment URL creation error: {e}")
            return {
                'success': False,
                'error': f"Payment URL creation failed: {e}"
            }
    
    def check_payment_status(self, merchant_order_id):
        """
        Check payment status
        Based on Postman: GET /apis/pg-sandbox/checkout/v2/order/{merchantOrderId}/status
        
        Args:
            merchant_order_id (str): Order ID to check status for
        
        Returns:
            dict: Payment status response
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {access_token}'
            }
            
            status_endpoint = f"{self.status_url}/{merchant_order_id}/status"
            
            logger.info(f"Checking payment status for order: {merchant_order_id}")
            
            response = requests.get(
                status_endpoint,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Payment status retrieved for order: {merchant_order_id}")
            return {
                'success': True,
                'data': result,
                'order_id': merchant_order_id
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment status check failed: {e}")
            return {
                'success': False,
                'error': f"Failed to check payment status: {e}"
            }
        except Exception as e:
            logger.error(f"Payment status check error: {e}")
            return {
                'success': False,
                'error': f"Payment status check failed: {e}"
            }
    
    def create_refund(self, merchant_refund_id, original_merchant_order_id, amount):
        """
        Create refund
        Based on Postman: POST /apis/pg-sandbox/payments/v2/refund
        
        Args:
            merchant_refund_id (str): Unique refund ID
            original_merchant_order_id (str): Original order ID
            amount (int): Refund amount in paisa
        
        Returns:
            dict: Refund response
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {access_token}'
            }
            
            # Prepare payload
            payload = {
                "merchantRefundId": merchant_refund_id,
                "originalMerchantOrderId": original_merchant_order_id,
                "amount": amount
            }
            
            logger.info(f"Creating refund: {merchant_refund_id} for order: {original_merchant_order_id}")
            
            response = requests.post(
                self.refund_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Refund created successfully: {merchant_refund_id}")
            return {
                'success': True,
                'data': result,
                'refund_id': merchant_refund_id
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Refund creation failed: {e}")
            return {
                'success': False,
                'error': f"Failed to create refund: {e}"
            }
        except Exception as e:
            logger.error(f"Refund creation error: {e}")
            return {
                'success': False,
                'error': f"Refund creation failed: {e}"
            }
    
    def check_refund_status(self, merchant_refund_id):
        """
        Check refund status
        Based on Postman: GET /apis/pg-sandbox/payments/v2/refund/{merchantRefundId}/status
        
        Args:
            merchant_refund_id (str): Refund ID to check status for
        
        Returns:
            dict: Refund status response
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'O-Bearer {access_token}'
            }
            
            refund_status_endpoint = f"{self.refund_status_url}/{merchant_refund_id}/status"
            
            logger.info(f"Checking refund status: {merchant_refund_id}")
            
            response = requests.get(
                refund_status_endpoint,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Refund status retrieved: {merchant_refund_id}")
            return {
                'success': True,
                'data': result,
                'refund_id': merchant_refund_id
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Refund status check failed: {e}")
            return {
                'success': False,
                'error': f"Failed to check refund status: {e}"
            }
        except Exception as e:
            logger.error(f"Refund status check error: {e}")
            return {
                'success': False,
                'error': f"Refund status check failed: {e}"
            }
