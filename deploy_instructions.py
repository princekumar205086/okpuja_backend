#!/usr/bin/env python
"""
Quick fix deployment - uploads the fixed payment gateway code
"""

import os
import sys

def show_deployment_instructions():
    print("🚀 PHONEPE FIX DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    print()
    print("The payment is still failing because the fixed code")
    print("needs to be uploaded to your server.")
    print()
    print("STEP 1: Upload the fixed gateway file")
    print("---------------------------------------")
    print("From your local machine, run:")
    print()
    print("scp payment/gateways.py root@srv882943:/opt/api.okpuja.com/payment/")
    print()
    print("STEP 2: Restart services on server")
    print("----------------------------------")
    print("SSH to your server and run:")
    print()
    print("cd /opt/api.okpuja.com")
    print("sudo systemctl restart gunicorn_api_okpuja")
    print("sudo systemctl restart nginx")
    print()
    print("STEP 3: Test the fix")
    print("-------------------")
    print("python simple_phonepe_test.py")
    print()
    print("STEP 4: Verify in Swagger")
    print("------------------------")
    print("Try the same payment request in Swagger again.")
    print("It should now work without 'Connection refused' error.")
    print()
    print("="*60)
    print("📋 QUICK CHECKLIST:")
    print("□ Upload payment/gateways.py to server")
    print("□ Restart gunicorn service")
    print("□ Restart nginx service") 
    print("□ Test with simple_phonepe_test.py")
    print("□ Verify payment works in Swagger")
    print("="*60)

if __name__ == "__main__":
    show_deployment_instructions()
