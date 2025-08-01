#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from cart.models import Cart
from booking.models import Booking

def debug_redirect_parameters():
    """Debug what parameters PhonePe is actually sending in the redirect"""
    print("=== DEBUGGING REDIRECT PARAMETERS ===\n")
    
    print("The issue is that PhonePe is not sending the merchant order ID in the redirect URL.")
    print("This happens when PhonePe V2 Standard Checkout doesn't include order parameters.\n")
    
    print("SOLUTION: We need to modify the redirect handler to handle this case.\n")
    
    # Check recent payments to understand the flow
    recent_payments = PaymentOrder.objects.filter(cart_id__isnull=False).order_by('-created_at')[:3]
    
    print("Recent cart payments:")
    for payment in recent_payments:
        print(f"  - Order ID: {payment.merchant_order_id}")
        print(f"    Status: {payment.status}")
        print(f"    Cart ID: {payment.cart_id}")
        
        if payment.cart_id:
            try:
                cart = Cart.objects.get(cart_id=payment.cart_id)
                booking = Booking.objects.filter(cart=cart).first()
                print(f"    Booking: {'YES - ' + booking.book_id if booking else 'NO'}")
            except:
                print(f"    Booking: ERROR")
        print()

def show_solution():
    """Show the solution for handling PhonePe V2 redirects without order ID"""
    print("=== SOLUTION FOR PHONEPE V2 REDIRECTS ===\n")
    
    print("PhonePe V2 Standard Checkout often doesn't send order ID in redirect URL.")
    print("We need to implement a different strategy:\n")
    
    print("1. USE SIMPLE REDIRECT HANDLER")
    print("   - PhonePe redirects to: /api/payments/redirect/simple/")
    print("   - Handler checks for latest successful payment for user")
    print("   - Creates booking if needed")
    print("   - Redirects with booking ID\n")
    
    print("2. UPDATE PAYMENT CREATION")
    print("   - Use simple redirect URL in payment creation")
    print("   - Store user session to identify payments\n")
    
    print("3. FRONTEND HANDLING")
    print("   - Handle both scenarios:")
    print("     a) With book_id parameter")
    print("     b) Without book_id (fetch latest booking)\n")

if __name__ == "__main__":
    debug_redirect_parameters()
    show_solution()
