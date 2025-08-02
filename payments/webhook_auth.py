"""
PhonePe V2 Webhook Authentication
Handles SHA256(username:password) authentication as per PhonePe official docs
"""

import hashlib
import logging
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


def authenticate_webhook(request):
    """
    Authenticate webhook request using PhonePe V2 SHA256 authentication
    
    PhonePe sends: Authorization: SHA256(username:password)
    We calculate: SHA256("okpuja_webhook_user:Okpuja2025")
    
    Returns tuple: (is_authenticated, error_response)
    """
    try:
        # Get Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning("Webhook request missing Authorization header")
            return False, JsonResponse({
                'success': False,
                'error': 'Authorization header required'
            }, status=401)
        
        # Get configured credentials
        webhook_username = getattr(settings, 'PHONEPE_WEBHOOK_USERNAME', 'okpuja_webhook_user')
        webhook_password = getattr(settings, 'PHONEPE_WEBHOOK_PASSWORD', 'Okpuja2025')
        
        # Calculate expected SHA256 hash
        credentials_string = f"{webhook_username}:{webhook_password}"
        expected_hash = hashlib.sha256(credentials_string.encode('utf-8')).hexdigest()
        
        # PhonePe might send with or without "SHA256" prefix
        received_hash = auth_header.replace('SHA256 ', '').replace('SHA256:', '').strip()
        
        if received_hash.lower() != expected_hash.lower():
            logger.warning(f"Invalid webhook authentication. Expected: {expected_hash}, Received: {received_hash}")
            return False, JsonResponse({
                'success': False,
                'error': 'Invalid authentication'
            }, status=401)
        
        logger.info("PhonePe webhook authentication successful")
        return True, None
        
    except Exception as e:
        logger.error(f"Webhook authentication error: {e}")
        return False, JsonResponse({
            'success': False,
            'error': 'Authentication error'
        }, status=500)


def webhook_auth_decorator(view_func):
    """
    Decorator to add webhook authentication to view functions
    """
    def wrapper(request, *args, **kwargs):
        is_authenticated, error_response = authenticate_webhook(request)
        if not is_authenticated:
            return error_response
        return view_func(request, *args, **kwargs)
    return wrapper
