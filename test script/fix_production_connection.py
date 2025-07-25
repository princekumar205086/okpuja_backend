#!/usr/bin/env python
"""
Production Server PhonePe Fix
Addresses connection issues on production servers
"""

import os
import django
import requests
import json
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def test_production_specific_issues():
    """Test production-specific connection issues"""
    print("🏭 PRODUCTION SERVER CONNECTION ISSUES")
    print("=" * 50)
    
    # Test with different user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'okpuja-backend/1.0',
        'Python-requests/' + requests.__version__
    ]
    
    endpoint = "https://api.phonepe.com/apis/hermes/pg/v1/pay"
    
    for ua in user_agents:
        try:
            headers = {'User-Agent': ua}
            response = requests.get(endpoint, headers=headers, timeout=30)
            print(f"✅ User-Agent '{ua[:30]}...': {response.status_code}")
        except Exception as e:
            print(f"❌ User-Agent '{ua[:30]}...': {str(e)}")

def create_enhanced_phonepe_gateway():
    """Create enhanced PhonePe gateway with better error handling"""
    
    enhanced_code = '''
# Enhanced PhonePe Gateway with Production Fixes
class EnhancedPhonePeGateway:
    def __init__(self):
        self.merchant_id = settings.PHONEPE_MERCHANT_ID
        self.merchant_key = settings.PHONEPE_MERCHANT_KEY
        self.salt_index = settings.PHONEPE_SALT_INDEX
        self.timeout = getattr(settings, 'PHONEPE_TIMEOUT', 120)
        self.max_retries = getattr(settings, 'PHONEPE_MAX_RETRIES', 5)
        
        # Enhanced endpoint configuration
        self.api_endpoints = [
            "https://api.phonepe.com/apis/hermes/pg/v1/pay",
            "https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay",
            "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
        ]
        
        # Enhanced request configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'okpuja-backend/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        # Connection pooling and retry configuration
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def initiate_payment_enhanced(self, payment):
        """Enhanced payment initiation with better error handling"""
        import base64
        import hashlib
        import json
        
        try:
            # Prepare callback URLs
            callback_url = settings.PHONEPE_CALLBACK_URL
            redirect_url = f"{settings.PHONEPE_SUCCESS_REDIRECT_URL}?payment_id={payment.id}"
            
            # Create payload
            payload = {
                "merchantId": self.merchant_id,
                "merchantTransactionId": payment.merchant_transaction_id,
                "merchantUserId": f"USR{payment.user.id}",
                "amount": int(float(payment.amount) * 100),
                "redirectUrl": redirect_url,
                "redirectMode": "POST",
                "callbackUrl": callback_url,
                "mobileNumber": getattr(payment.user, 'phone_number', '9000000000'),
                "paymentInstrument": {"type": "PAY_PAGE"}
            }
            
            # Encode and sign
            data = base64.b64encode(json.dumps(payload).encode()).decode()
            string_to_hash = data + "/pg/v1/pay" + self.merchant_key
            checksum = hashlib.sha256(string_to_hash.encode()).hexdigest()
            final_checksum = f"{checksum}###{self.salt_index}"
            
            final_payload = {"request": data}
            headers = {
                'Content-Type': 'application/json',
                'X-VERIFY': final_checksum,
                'X-Source-Platform': 'web'
            }
            
            # Try multiple endpoints with enhanced error handling
            last_error = None
            
            for endpoint_idx, api_url in enumerate(self.api_endpoints):
                logger.info(f"Trying PhonePe endpoint {endpoint_idx + 1}: {api_url}")
                
                for attempt in range(self.max_retries):
                    try:
                        # Progressive timeout
                        timeout = self.timeout + (attempt * 30)
                        
                        response = self.session.post(
                            api_url,
                            headers=headers,
                            json=final_payload,
                            timeout=timeout,
                            verify=True
                        )
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            if response_data.get('success'):
                                payment_url = response_data['data']['instrumentResponse']['redirectInfo']['url']
                                
                                # Update payment
                                payment.gateway_response = response_data
                                payment.phonepe_payment_id = response_data.get('data', {}).get('transactionId')
                                payment.save()
                                
                                return {
                                    'success': True,
                                    'payment_url': payment_url,
                                    'transaction_id': payment.transaction_id,
                                    'merchant_transaction_id': payment.merchant_transaction_id
                                }
                        
                        # Log response for debugging
                        logger.warning(f"PhonePe API returned {response.status_code}: {response.text[:200]}")
                        
                    except requests.exceptions.ConnectionError as e:
                        last_error = f"Connection Error: {str(e)}"
                        logger.error(f"PhonePe Connection Error (attempt {attempt + 1}): {str(e)}")
                        
                        if "Connection refused" in str(e):
                            # Specific handling for connection refused
                            if attempt == self.max_retries - 1 and endpoint_idx == len(self.api_endpoints) - 1:
                                raise Exception(f"PhonePe API connection refused from all endpoints. This might be a server-side firewall or network issue. Last error: {str(e)}")
                        
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                        
                    except requests.exceptions.Timeout as e:
                        last_error = f"Timeout Error: {str(e)}"
                        logger.error(f"PhonePe Timeout (attempt {attempt + 1}): {str(e)}")
                        time.sleep(2 ** attempt)
                        continue
                        
                    except Exception as e:
                        last_error = f"Request Error: {str(e)}"
                        logger.error(f"PhonePe Request Error (attempt {attempt + 1}): {str(e)}")
                        time.sleep(2 ** attempt)
                        continue
            
            # If we get here, all attempts failed
            raise Exception(f"All PhonePe endpoints failed. Last error: {last_error}")
            
        except Exception as e:
            logger.error(f"PhonePe payment initiation failed: {str(e)}")
            raise e
'''
    
    print("📋 ENHANCED PHONEPE GATEWAY CODE:")
    print("Copy this enhanced code to your gateway implementation")
    
    return enhanced_code

def create_production_fixes():
    """Create production-specific fixes"""
    
    print("\n🔧 PRODUCTION FIXES TO APPLY:")
    print("=" * 50)
    
    fixes = [
        "1. Add connection pooling and retry logic",
        "2. Use session-based requests for better connection management", 
        "3. Implement exponential backoff for retries",
        "4. Add multiple PhonePe endpoint fallbacks",
        "5. Enhanced error categorization",
        "6. Better timeout handling",
        "7. User-Agent and header optimization"
    ]
    
    for fix in fixes:
        print(f"✅ {fix}")
    
    # Environment-specific settings
    env_settings = '''
# Add these to your .env file for production optimization
PHONEPE_TIMEOUT=180
PHONEPE_MAX_RETRIES=5
PHONEPE_CONNECTION_POOL_SIZE=10
PHONEPE_SSL_VERIFY=True
PHONEPE_USER_AGENT=okpuja-backend/1.0
'''
    
    print(f"\n📝 ENVIRONMENT SETTINGS:\n{env_settings}")

def test_with_curl_equivalent():
    """Test what curl would do"""
    print("\n🔧 CURL EQUIVALENT TEST:")
    print("=" * 50)
    
    # This mimics what production servers often need
    try:
        headers = {
            'User-Agent': 'curl/7.68.0',
            'Accept': '*/*',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            "https://api.phonepe.com/apis/hermes/pg/v1/pay",
            headers=headers,
            timeout=30
        )
        
        print(f"✅ Curl-like request: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Curl-like request failed: {str(e)}")

def main():
    print("🏭 PRODUCTION PHONEPE CONNECTION FIXER")
    print("=" * 60)
    
    test_production_specific_issues()
    test_with_curl_equivalent()
    
    enhanced_code = create_enhanced_phonepe_gateway()
    create_production_fixes()
    
    print("\n" + "=" * 60)
    print("🎯 IMMEDIATE ACTION ITEMS:")
    print("=" * 60)
    print("1. The API works locally but fails on production server")
    print("2. This suggests a server-side networking issue")
    print("3. Contact your hosting provider about outbound HTTPS connections")
    print("4. Check if your server's IP is blocked by PhonePe")
    print("5. Implement the enhanced gateway code above")
    print("6. Consider using a reverse proxy or CDN")
    
    print("\n📞 HOSTING PROVIDER QUESTIONS:")
    print("- Are outbound HTTPS connections to api.phonepe.com allowed?")
    print("- Is there a firewall blocking connections to payment gateways?") 
    print("- Can you whitelist PhonePe API endpoints?")
    print("- Is there a proxy or NAT configuration affecting connections?")

if __name__ == "__main__":
    main()
