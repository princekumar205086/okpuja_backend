#!/usr/bin/env python
"""
PhonePe Webhook Fix
This script fixes the webhook to handle empty bodies and provides better debugging
"""

import os
import django
import json
import base64

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def create_webhook_fix():
    """Create improved webhook handling"""
    
    webhook_fix_code = '''    def post(self, request, gateway_name):
        """
        Handle PhonePe webhook callback with enhanced error handling
        FIXED: Better handling of empty request bodies and JSON parsing
        """
        try:
            logger.info(f"🔔 Webhook received for gateway: {gateway_name}")
            logger.info(f"📋 Headers: {dict(request.headers)}")
            logger.info(f"📝 Raw body length: {len(request.body) if request.body else 0}")
            logger.info(f"📄 Content type: {request.content_type}")
            
            # Handle empty request body - FIXED
            if not request.body:
                logger.warning("⚠️ Empty webhook request body received")
                
                # For development/testing: return helpful message
                if settings.DEBUG:
                    return Response(
                        {
                            'error': 'Empty webhook request body',
                            'success': False,
                            'message': 'No data received in webhook callback',
                            'help': 'This usually means PhonePe is not sending data to the webhook. Check PhonePe dashboard configuration.',
                            'webhook_url': request.build_absolute_uri(),
                            'expected_format': {
                                'response': 'base64_encoded_response',
                                'merchantId': 'your_merchant_id',
                                'merchantTransactionId': 'transaction_id'
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # For production: simpler response
                    return Response(
                        {
                            'error': 'Empty webhook request body',
                            'success': False
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Get raw callback body as string
            try:
                callback_body_string = request.body.decode('utf-8')
                logger.info(f"✅ Decoded request body successfully: {len(callback_body_string)} characters")
                
                # FIXED: Handle empty string after decoding
                if not callback_body_string.strip():
                    logger.warning("⚠️ Empty webhook callback body after decoding")
                    return Response(
                        {
                            'error': 'Empty webhook callback body after decoding',
                            'success': False,
                            'message': 'Webhook body is empty after UTF-8 decoding',
                            'help': 'PhonePe might be sending empty data or wrong encoding'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # FIXED: Validate JSON before processing
                try:
                    test_json = json.loads(callback_body_string)
                    logger.info(f"✅ Valid JSON received with keys: {list(test_json.keys()) if isinstance(test_json, dict) else 'non-dict'}")
                except json.JSONDecodeError as json_err:
                    logger.error(f"❌ Invalid JSON in webhook body: {str(json_err)}")
                    logger.error(f"📝 Raw body that failed JSON parsing: {callback_body_string[:200]}...")
                    
                    return Response(
                        {
                            'error': f'Invalid JSON in webhook body: {str(json_err)}',
                            'success': False,
                            'json_error': str(json_err),
                            'body_preview': callback_body_string[:100],
                            'help': 'The webhook body is not valid JSON. Check PhonePe webhook configuration.'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except UnicodeDecodeError as e:
                logger.error(f"❌ Failed to decode request body: {str(e)}")
                return Response(
                    {
                        'error': 'Invalid request body encoding',
                        'success': False,
                        'details': str(e),
                        'help': 'Request body is not UTF-8 encoded'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get authorization header (X-VERIFY from PhonePe)
            authorization_header = request.headers.get('X-VERIFY', '')
            if not authorization_header:
                # Try alternative header names
                authorization_header = (
                    request.headers.get('Authorization', '') or
                    request.headers.get('x-verify', '') or
                    request.headers.get('verify', '')
                )
                
                if not authorization_header:
                    logger.warning("⚠️ Missing X-VERIFY header")
                    if not settings.DEBUG:
                        return Response(
                            {
                                'error': 'Missing X-VERIFY header for webhook authentication',
                                'success': False,
                                'available_headers': list(request.headers.keys())
                            },
                            status=status.HTTP_401_UNAUTHORIZED
                        )
            
            # Process with PhonePe gateway
            try:
                gateway = get_payment_gateway(gateway_name)
                logger.info(f"✅ Got {gateway_name} gateway instance")
                
                payment = gateway.process_webhook(request.headers, callback_body_string)
                logger.info(f"✅ Webhook processed successfully for payment {payment.id}")
                
                return Response(
                    {
                        'success': True,
                        'message': 'Webhook processed successfully',
                        'payment_id': payment.id,
                        'transaction_id': payment.transaction_id,
                        'merchant_transaction_id': payment.merchant_transaction_id,
                        'status': payment.status
                    },
                    status=status.HTTP_200_OK
                )
                
            except Exception as gateway_error:
                logger.error(f"❌ Gateway processing failed: {str(gateway_error)}")
                logger.error(f"🔍 Gateway error type: {type(gateway_error).__name__}")
                
                return Response(
                    {
                        'error': f'Gateway processing failed: {str(gateway_error)}',
                        'success': False,
                        'gateway': gateway_name,
                        'error_type': type(gateway_error).__name__,
                        'help': 'Check payment exists and webhook data is valid'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            logger.error(f"💥 Critical webhook processing error: {str(e)}")
            logger.error(f"🔍 Error type: {type(e).__name__}")
            import traceback
            logger.error(f"📚 Traceback: {traceback.format_exc()}")
            
            return Response(
                {
                    'error': f'Webhook processing failed: {str(e)}',
                    'success': False,
                    'error_type': type(e).__name__
                },
                status=status.HTTP_400_BAD_REQUEST
            )'''
    
    print("📋 FIXED WEBHOOK CODE:")
    print("=" * 60)
    print("Key improvements:")
    print("1. ✅ Better empty body handling")
    print("2. ✅ JSON validation before processing")
    print("3. ✅ More helpful error messages")
    print("4. ✅ Development vs production responses")
    print("5. ✅ Header validation improvements")
    
    return webhook_fix_code

def check_phonepe_settings():
    """Check PhonePe configuration"""
    print("\n🔍 CHECKING PHONEPE CONFIGURATION:")
    print("=" * 50)
    
    required_settings = [
        'PHONEPE_MERCHANT_ID',
        'PHONEPE_MERCHANT_KEY', 
        'PHONEPE_SALT_INDEX',
        'PHONEPE_CALLBACK_URL',
        'PHONEPE_SUCCESS_REDIRECT_URL',
        'PHONEPE_BASE_URL'
    ]
    
    missing_settings = []
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if value:
            if 'KEY' in setting or 'CALLBACK' in setting:
                print(f"✅ {setting}: {'*' * (len(str(value)) - 10) + str(value)[-10:]}")
            else:
                print(f"✅ {setting}: {value}")
        else:
            missing_settings.append(setting)
            print(f"❌ {setting}: NOT SET")
    
    if missing_settings:
        print(f"\n⚠️ Missing settings: {', '.join(missing_settings)}")
    else:
        print("\n✅ All required PhonePe settings are configured")
    
    # Check webhook URL accessibility
    callback_url = getattr(settings, 'PHONEPE_CALLBACK_URL', '')
    print(f"\n🌐 WEBHOOK URL: {callback_url}")
    
    if 'localhost' in callback_url or '127.0.0.1' in callback_url:
        print("⚠️ WARNING: Using localhost URL - PhonePe cannot reach this in production!")
        print("💡 SOLUTION: Use ngrok for testing or deploy to production server")
    elif callback_url.startswith('https://'):
        print("✅ Using HTTPS webhook URL - Good for production")
    else:
        print("⚠️ WARNING: Not using HTTPS - PhonePe requires HTTPS for production")

def create_test_endpoint():
    """Create a test endpoint for webhook debugging"""
    
    test_code = '''@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def debug_webhook(request):
    """
    Debug endpoint to test webhook without processing
    URL: /api/payments/webhook/debug/
    """
    if request.method == 'GET':
        return Response({
            'message': 'PhonePe Webhook Debug Endpoint',
            'timestamp': timezone.now().isoformat(),
            'webhook_url': '/api/payments/webhook/phonepe/',
            'test_instructions': {
                'step1': 'POST to this endpoint with sample data',
                'step2': 'Check response and logs',
                'step3': 'Test actual webhook endpoint'
            }
        })
    
    # Debug POST requests
    try:
        logger.info("🔍 DEBUG WEBHOOK TEST")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Body: {request.body}")
        logger.info(f"Content-Type: {request.content_type}")
        
        if not request.body:
            return Response({
                'debug': 'empty_body',
                'message': 'No request body received',
                'help': 'PhonePe webhooks should include JSON body'
            })
        
        try:
            body_str = request.body.decode('utf-8')
            parsed_json = json.loads(body_str)
            
            return Response({
                'debug': 'success',
                'message': 'Valid JSON received',
                'body_length': len(body_str),
                'json_keys': list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'not_dict',
                'sample_data': parsed_json
            })
            
        except json.JSONDecodeError as e:
            return Response({
                'debug': 'json_error',
                'message': f'Invalid JSON: {str(e)}',
                'body_preview': body_str[:100] if 'body_str' in locals() else 'decode_failed'
            })
            
    except Exception as e:
        return Response({
            'debug': 'error',
            'message': f'Debug failed: {str(e)}'
        })'''
    
    print("\n🛠️ DEBUG ENDPOINT CODE:")
    print("Add this to your views.py for testing webhooks")
    
    return test_code

if __name__ == "__main__":
    print("🚀 PhonePe Webhook Fix Generator")
    print("=" * 50)
    
    check_phonepe_settings()
    
    webhook_fix = create_webhook_fix()
    test_endpoint = create_test_endpoint()
    
    print("\n" + "=" * 60)
    print("🎯 IMMEDIATE FIXES:")
    print("1. The JSON error occurs when webhook receives empty body")
    print("2. This happens when testing with Postman without request body")
    print("3. In production, check PhonePe dashboard webhook configuration")
    print("4. Ensure webhook URL is publicly accessible (not localhost)")
    
    print("\n📋 NEXT STEPS:")
    print("1. Apply the webhook fix code to payment/views.py")
    print("2. Add the debug endpoint for testing")
    print("3. Test with proper JSON payload in Postman")
    print("4. Check PhonePe dashboard webhook settings")
    print("5. For production: ensure HTTPS webhook URL is configured")
