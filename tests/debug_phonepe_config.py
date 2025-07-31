"""
Debug PhonePe Configuration
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.phonepe_v2_simple import PhonePeV2ClientSimplified

def debug_phonepe_config():
    print("🔍 PhonePe Configuration Debug")
    print("=" * 40)
    
    # Check settings
    print("📋 Django Settings:")
    print(f"   PHONEPE_MERCHANT_ID: '{getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT_SET')}'")
    print(f"   PHONEPE_CLIENT_SECRET: '{getattr(settings, 'PHONEPE_CLIENT_SECRET', 'NOT_SET')}'")
    print(f"   PHONEPE_SALT_KEY: '{getattr(settings, 'PHONEPE_SALT_KEY', 'NOT_SET')}'")
    print(f"   PHONEPE_SALT_INDEX: '{getattr(settings, 'PHONEPE_SALT_INDEX', 'NOT_SET')}'")
    
    # Check environment variables
    print("\n🌍 Environment Variables:")
    print(f"   PHONEPE_MERCHANT_ID: '{os.getenv('PHONEPE_MERCHANT_ID', 'NOT_SET')}'")
    print(f"   PHONEPE_CLIENT_SECRET: '{os.getenv('PHONEPE_CLIENT_SECRET', 'NOT_SET')}'")
    print(f"   PHONEPE_SALT_KEY: '{os.getenv('PHONEPE_SALT_KEY', 'NOT_SET')}'")
    print(f"   PHONEPE_SALT_INDEX: '{os.getenv('PHONEPE_SALT_INDEX', 'NOT_SET')}'")
    
    # Test client initialization
    print("\n🔧 Client Configuration:")
    client = PhonePeV2ClientSimplified(env="sandbox")
    print(f"   merchant_id: '{client.merchant_id}'")
    print(f"   salt_key: '{client.salt_key}'")
    print(f"   salt_index: '{client.salt_index}'")
    print(f"   base_url: '{client.base_url}'")
    
    # Test checksum generation
    print("\n🔐 Checksum Test:")
    test_payload = "eyJ0ZXN0IjoidmFsdWUifQ=="
    test_endpoint = "/apis/hermes/pg/v1/pay"
    checksum = client.generate_checksum(test_payload, test_endpoint)
    print(f"   Test payload: {test_payload}")
    print(f"   Test endpoint: {test_endpoint}")
    print(f"   Generated checksum: {checksum}")
    
    # Test with official UAT credentials
    print("\n✅ Official UAT Credentials Test:")
    print("   Merchant ID: PGTESTPAYUAT86")
    print("   Salt Key: 96434309-7796-489d-8924-ab56988a6076")
    print("   Salt Index: 1")
    
    # Manual checksum test
    test_string = test_payload + test_endpoint + "96434309-7796-489d-8924-ab56988a6076"
    import hashlib
    manual_checksum = hashlib.sha256(test_string.encode()).hexdigest() + "###1"
    print(f"   Manual checksum: {manual_checksum}")

if __name__ == "__main__":
    debug_phonepe_config()
