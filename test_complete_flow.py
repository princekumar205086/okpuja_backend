#!/usr/bin/env python3
"""
Test script to verify complete payment-first booking flow
This script tests the entire flow from cart creation to booking confirmation
"""

import requests
import json
import time
from datetime import datetime, timedelta

class OKPujaAPITester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
        
    def login(self, email="asliprinceraj@gmail.com", password="testpass123"):
        """Login and save authentication token"""
        url = f"{self.base_url}/api/auth/login/"
        data = {"email": email, "password": password}
        
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            self.token = result['access']
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print(f"✅ Login successful for {email}")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def create_test_address(self):
        """Create a default address for the user"""
        url = f"{self.base_url}/api/auth/addresses/"
        data = {
            "address_line1": "123 Test Street",
            "address_line2": "Near Test Station",
            "city": "Mumbai",
            "state": "Maharashtra", 
            "postal_code": "400001",
            "country": "India",
            "is_default": True
        }
        
        response = self.session.post(url, json=data)
        if response.status_code == 201:
            print("✅ Default address created")
            return response.json()
        else:
            print(f"⚠️  Address creation failed (might already exist): {response.text}")
            return None
    
    def create_cart(self):
        """Create a test cart with puja service"""
        url = f"{self.base_url}/api/cart/carts/"
        
        # Calculate a future date
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        data = {
            "service_type": "PUJA",
            "puja_service": 1,  # Assuming first puja service exists
            "package_id": 1,    # Assuming first package exists
            "selected_date": future_date,
            "selected_time": "10:00 AM"
        }
        
        response = self.session.post(url, json=data)
        if response.status_code == 201:
            cart = response.json()
            print(f"✅ Cart created with ID: {cart.get('id', 'Unknown')}")
            return cart
        else:
            print(f"❌ Cart creation failed: {response.text}")
            # Try to parse error details
            try:
                error_details = response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                pass
            return None
    
    def process_payment(self, cart_id):
        """Process payment for the cart"""
        url = f"{self.base_url}/api/payments/payments/process-cart/"
        data = {
            "cart_id": cart_id,
            "method": "PHONEPE"
        }
        
        response = self.session.post(url, json=data)
        if response.status_code == 201:
            payment = response.json()
            print(f"✅ Payment initiated with ID: {payment['payment_id']}")
            print(f"📱 Payment URL: {payment.get('payment_url', 'N/A')}")
            return payment
        else:
            print(f"❌ Payment processing failed: {response.text}")
            return None
    
    def simulate_payment_success(self, payment_id):
        """Simulate payment success (development only)"""
        url = f"{self.base_url}/api/payments/payments/{payment_id}/simulate-success/"
        data = {"simulate": True}
        
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Payment simulation successful!")
            print(f"💳 Payment status: {result.get('status')}")
            if result.get('booking_created'):
                print(f"📅 Booking created: {result.get('booking_reference')}")
            return result
        else:
            print(f"❌ Payment simulation failed: {response.text}")
            return None
    
    def check_booking_status(self, payment_id):
        """Check if booking was created from payment"""
        url = f"{self.base_url}/api/payments/payments/{payment_id}/check-booking/"
        
        response = self.session.get(url)
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('booking'):
                booking = result['booking']
                print(f"✅ Booking confirmed!")
                print(f"📋 Booking ID: {booking['book_id']}")
                print(f"📅 Date: {booking['selected_date']} at {booking['selected_time']}")
                print(f"💰 Amount: {booking.get('total_amount', 'N/A')}")
                return booking
            else:
                print(f"⚠️  No booking found: {result}")
                return None
        else:
            print(f"❌ Booking check failed: {response.text}")
            return None
    
    def get_all_bookings(self):
        """Get all user bookings"""
        url = f"{self.base_url}/api/booking/bookings/"
        
        response = self.session.get(url)
        if response.status_code == 200:
            bookings = response.json()
            print(f"📋 Total bookings: {len(bookings)}")
            for booking in bookings:
                print(f"  - {booking['book_id']}: {booking['status']} (Date: {booking['selected_date']})")
            return bookings
        else:
            print(f"❌ Failed to get bookings: {response.text}")
            return []
    
    def run_complete_test(self):
        """Run the complete payment-first booking flow test"""
        print("🚀 Starting Complete Payment-First Booking Flow Test")
        print("=" * 60)
        
        # Step 1: Login
        print("\n1️⃣  Testing Login...")
        if not self.login():
            print("❌ Test failed at login step")
            return False
        
        # Step 2: Create address
        print("\n2️⃣  Creating test address...")
        self.create_test_address()
        
        # Step 3: Create cart
        print("\n3️⃣  Creating cart...")
        cart = self.create_cart()
        if not cart:
            print("❌ Test failed at cart creation")
            return False
        
        # Step 4: Process payment
        print("\n4️⃣  Processing payment...")
        payment = self.process_payment(cart['id'])
        if not payment:
            print("❌ Test failed at payment processing")
            return False
        
        # Step 5: Simulate payment success
        print("\n5️⃣  Simulating payment success...")
        simulation = self.simulate_payment_success(payment['payment_id'])
        if not simulation:
            print("❌ Test failed at payment simulation")
            return False
        
        # Step 6: Verify booking creation
        print("\n6️⃣  Verifying booking creation...")
        time.sleep(1)  # Give it a moment
        booking = self.check_booking_status(payment['payment_id'])
        if not booking:
            print("❌ Test failed - no booking created")
            return False
        
        # Step 7: List all bookings
        print("\n7️⃣  Listing all bookings...")
        all_bookings = self.get_all_bookings()
        
        print("\n🎉 COMPLETE FLOW TEST SUCCESSFUL!")
        print("=" * 60)
        print("✅ Cart created → Payment processed → Payment success → Booking created")
        print(f"📋 Final booking: {booking['book_id']}")
        print(f"💳 Payment amount: ₹{payment.get('amount', 'N/A')}")
        
        return True

def main():
    """Main test function"""
    print("OKPUJA Payment-First Booking Flow Tester")
    print("=" * 50)
    
    # Initialize tester
    tester = OKPujaAPITester()
    
    # Run complete test
    success = tester.run_complete_test()
    
    if success:
        print("\n🎯 TEST RESULT: SUCCESS! Your payment-first flow is working perfectly!")
    else:
        print("\n❌ TEST RESULT: FAILED. Check the errors above.")
    
    print("\n📝 Notes:")
    print("- This test uses the simulate endpoint for development")
    print("- In production, PhonePe webhooks will handle payment confirmation")
    print("- Make sure your Django server is running on http://127.0.0.1:8000")

if __name__ == "__main__":
    main()
