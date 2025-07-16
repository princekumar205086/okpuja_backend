#!/usr/bin/env python3
from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import socket
import json
from urllib.parse import urlparse


class Command(BaseCommand):
    help = 'Debug PhonePe API connectivity and configuration from production server'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 PHONEPE CONNECTIVITY DIAGNOSTIC TOOL')
        )
        self.stdout.write("=" * 60)
        
        # 1. Test basic connectivity
        self.stdout.write("\n1. 🌐 TESTING BASIC NETWORK CONNECTIVITY")
        self.stdout.write("-" * 40)
        
        test_urls = [
            ('Google', 'https://google.com'),
            ('PhonePe Root', 'https://api.phonepe.com'),
            ('PhonePe API', 'https://api.phonepe.com/apis/hermes')
        ]
        
        connectivity_ok = True
        for name, url in test_urls:
            try:
                parsed_url = urlparse(url)
                ip = socket.gethostbyname(parsed_url.hostname)
                response = requests.get(url, timeout=10)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {name}: IP={ip}, Status={response.status_code}")
                )
            except socket.gaierror as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ {name}: DNS resolution failed - {str(e)}")
                )
                connectivity_ok = False
            except requests.exceptions.ConnectionError as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ {name}: Connection failed - {str(e)}")
                )
                connectivity_ok = False
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ {name}: Test failed - {str(e)}")
                )
                connectivity_ok = False
        
        # 2. Test PhonePe configuration
        self.stdout.write("\n2. ⚙️  CHECKING PHONEPE CONFIGURATION")
        self.stdout.write("-" * 40)
        
        config_items = [
            ('PHONEPE_MERCHANT_ID', getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT_SET')),
            ('PHONEPE_BASE_URL', getattr(settings, 'PHONEPE_BASE_URL', 'NOT_SET')),
            ('PHONEPE_SALT_INDEX', getattr(settings, 'PHONEPE_SALT_INDEX', 'NOT_SET')),
            ('PHONEPE_TIMEOUT', getattr(settings, 'PHONEPE_TIMEOUT', '60')),
            ('PHONEPE_MAX_RETRIES', getattr(settings, 'PHONEPE_MAX_RETRIES', '3')),
            ('PHONEPE_SSL_VERIFY', getattr(settings, 'PHONEPE_SSL_VERIFY', 'True')),
        ]
        
        config_ok = True
        for key, value in config_items:
            if value == 'NOT_SET':
                self.stdout.write(
                    self.style.ERROR(f"❌ {key}: NOT_SET")
                )
                config_ok = False
            else:
                display_value = value if 'KEY' not in key else f"{value[:10]}..."
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {key}: {display_value}")
                )
        
        # 3. Test PhonePe gateway initialization
        self.stdout.write("\n3. 🔧 TESTING PHONEPE GATEWAY")
        self.stdout.write("-" * 40)
        
        try:
            from payment.gateways import PhonePeGateway
            gateway = PhonePeGateway()
            self.stdout.write(
                self.style.SUCCESS("✅ PhonePe Gateway initialized successfully")
            )
            self.stdout.write(f"   Merchant ID: {gateway.merchant_id}")
            self.stdout.write(f"   Base URL: {gateway.base_url}")
            self.stdout.write(f"   Timeout: {gateway.timeout}s")
            self.stdout.write(f"   Max Retries: {gateway.max_retries}")
            self.stdout.write(f"   SSL Verify: {gateway.ssl_verify}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ PhonePe Gateway initialization failed: {str(e)}")
            )
            config_ok = False
        
        # 4. Test PhonePe API endpoint specifically
        self.stdout.write("\n4. 🎯 TESTING PHONEPE API ENDPOINT")
        self.stdout.write("-" * 40)
        
        try:
            phonepe_api_url = f"{getattr(settings, 'PHONEPE_BASE_URL', 'https://api.phonepe.com/apis/hermes')}/pg/v1/pay"
            self.stdout.write(f"Testing endpoint: {phonepe_api_url}")
            
            # Try a simple HEAD request first
            response = requests.head(phonepe_api_url, timeout=30)
            self.stdout.write(
                self.style.SUCCESS(f"✅ PhonePe API endpoint reachable: {response.status_code}")
            )
            
        except requests.exceptions.ConnectionError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Cannot reach PhonePe API endpoint: {str(e)}")
            )
            connectivity_ok = False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ PhonePe API test failed: {str(e)}")
            )
            connectivity_ok = False
        
        # 5. Final diagnosis
        self.stdout.write("\n5. 🎯 DIAGNOSIS & RECOMMENDATIONS")
        self.stdout.write("-" * 40)
        
        if connectivity_ok and config_ok:
            self.stdout.write(
                self.style.SUCCESS("✅ ALL TESTS PASSED! PhonePe should work correctly.")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ ISSUES DETECTED:")
            )
            
            if not connectivity_ok:
                self.stdout.write("   🌐 Network connectivity issues detected:")
                self.stdout.write("      - Check firewall rules for outbound HTTPS")
                self.stdout.write("      - Verify DNS resolution works")
                self.stdout.write("      - Contact hosting provider about blocked connections")
                
            if not config_ok:
                self.stdout.write("   ⚙️  Configuration issues detected:")
                self.stdout.write("      - Check .env file has all PhonePe settings")
                self.stdout.write("      - Verify environment variables are loaded correctly")
                
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS("🏁 DIAGNOSTIC COMPLETE")
        )
