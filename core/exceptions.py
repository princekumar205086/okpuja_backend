from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides better error messages for common exceptions
    """
    # Call REST framework's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)
    
    # Handle IntegrityError specifically
    if isinstance(exc, IntegrityError):
        logger.error(f"IntegrityError in {context.get('view', 'unknown view')}: {exc}")
        
        error_message = str(exc)
        custom_response_data = {}
        
        if 'accounts_user.phone' in error_message:
            custom_response_data = {
                'error': 'Validation Error',
                'message': 'A user with this phone number already exists.',
                'field_errors': {
                    'phone': ['A user with this phone number already exists.']
                }
            }
        elif 'accounts_user.email' in error_message:
            custom_response_data = {
                'error': 'Validation Error', 
                'message': 'A user with this email address already exists.',
                'field_errors': {
                    'email': ['A user with this email address already exists.']
                }
            }
        else:
            custom_response_data = {
                'error': 'Data Integrity Error',
                'message': 'The operation could not be completed due to a data conflict. Please check your information and try again.',
                'details': 'Some of the information you provided conflicts with existing data.'
            }
        
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # For other exceptions, return the default response
    if response is not None:
        # Log the error for debugging
        logger.error(f"Exception in {context.get('view', 'unknown view')}: {exc}")
    
    return response
