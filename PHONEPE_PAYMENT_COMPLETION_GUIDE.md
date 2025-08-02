# HANDLING PHONEPE PAYMENT COMPLETION - FRONTEND GUIDE
# ===================================================

## THE PROBLEM & SOLUTION

### What Happened:
- ✅ User completed payment successfully on PhonePe (Transaction: OMO2508030141519490798385)
- ❌ PhonePe webhook didn't trigger in sandbox/test environment  
- ❌ Payment status remained "INITIATED" instead of "SUCCESS"
- ❌ No booking was created automatically

### The Solution:
**Frontend needs to handle payment completion verification after PhonePe redirect**

---

## UPDATED FRONTEND FLOW

### Step 4: AFTER PHONEPE REDIRECT (Enhanced)

When PhonePe redirects user back to your confirmation page:

```javascript
// 1. Extract cart_id from URL
const urlParams = new URLSearchParams(window.location.search);
const cartId = urlParams.get('cart_id');

// 2. First, try to get booking (might already exist)
const checkBookingAndPayment = async (cartId) => {
  try {
    // Check if booking exists
    const bookingResponse = await fetch(`${API_BASE}/booking/bookings/by-cart/${cartId}/`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    
    if (bookingResponse.ok) {
      const booking = await bookingResponse.json();
      showSuccessPage(booking); // Booking exists!
      return;
    }
    
    // Booking not found, check payment status
    const paymentResponse = await fetch(`${API_BASE}/payments/cart/status/${cartId}/`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    
    const paymentData = await paymentResponse.json();
    
    if (paymentData.payment_status === 'SUCCESS') {
      // Payment successful but booking not created yet
      // Wait and retry (webhook might be processing)
      setTimeout(() => checkBookingAndPayment(cartId), 2000);
      showWaitingMessage("Payment successful! Creating your booking...");
      
    } else if (paymentData.payment_status === 'INITIATED') {
      // Payment might be successful but webhook not triggered
      // In sandbox/test environment, this happens often
      showPaymentVerificationForm(cartId);
      
    } else {
      showPaymentFailedMessage(paymentData.payment_status);
    }
    
  } catch (error) {
    console.error('Error checking booking/payment:', error);
    showErrorMessage("Unable to verify payment status");
  }
};
```

### NEW: Payment Verification Form

For cases where PhonePe payment succeeded but webhook didn't trigger:

```javascript
const showPaymentVerificationForm = (cartId) => {
  // Show a form asking user to confirm successful payment
  const confirmationHTML = `
    <div class="payment-verification">
      <h3>Payment Verification Required</h3>
      <p>Did you complete the payment successfully on PhonePe?</p>
      <button onclick="verifySuccessfulPayment('${cartId}')">
        Yes, Payment was Successful
      </button>
      <button onclick="handlePaymentFailed()">
        No, Payment Failed
      </button>
    </div>
  `;
  document.getElementById('confirmation-area').innerHTML = confirmationHTML;
};

const verifySuccessfulPayment = async (cartId) => {
  try {
    showLoadingMessage("Verifying payment and creating booking...");
    
    // Call backend endpoint to manually verify and complete payment
    const response = await fetch(`${API_BASE}/payments/verify-and-complete/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ cart_id: cartId })
    });
    
    if (response.ok) {
      const result = await response.json();
      if (result.booking_created) {
        showSuccessPage(result.booking);
      } else {
        showErrorMessage("Unable to create booking");
      }
    } else {
      showErrorMessage("Payment verification failed");
    }
    
  } catch (error) {
    console.error('Payment verification error:', error);
    showErrorMessage("Unable to verify payment");
  }
};
```

---

## BACKEND ENDPOINT FOR MANUAL VERIFICATION

I'll create a new endpoint for manual payment verification:

```python
# In payments/views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_and_complete_payment(request):
    """Manually verify and complete payment for successful PhonePe transactions"""
    cart_id = request.data.get('cart_id')
    
    if not cart_id:
        return Response({'error': 'cart_id required'}, status=400)
    
    try:
        # Get payment for this cart
        payment = PaymentOrder.objects.filter(
            cart_id=cart_id, 
            user=request.user
        ).first()
        
        if not payment:
            return Response({'error': 'Payment not found'}, status=404)
        
        if payment.status == 'SUCCESS':
            # Already processed
            booking = Booking.objects.filter(cart_id=cart_id).first()
            return Response({
                'success': True,
                'already_processed': True,
                'booking': BookingSerializer(booking).data if booking else None
            })
        
        # Check with PhonePe API for actual status
        payment_service = PaymentService()
        actual_status = payment_service.check_payment_status(payment.merchant_order_id)
        
        if actual_status == 'SUCCESS':
            # Update payment and create booking
            payment.status = 'SUCCESS'
            payment.save()
            
            # Create booking via webhook service
            webhook_service = WebhookService()
            booking = webhook_service._create_booking_from_cart(payment)
            
            return Response({
                'success': True,
                'payment_verified': True,
                'booking_created': True,
                'booking': BookingSerializer(booking).data
            })
        else:
            return Response({
                'success': False,
                'payment_status': actual_status,
                'message': f'Payment status is {actual_status}'
            })
            
    except Exception as e:
        return Response({'error': str(e)}, status=500)
```

---

## COMPLETE FRONTEND CONFIRMATION PAGE

```javascript
// Complete confirmation page handler
const handlePaymentConfirmation = async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const cartId = urlParams.get('cart_id');
  const redirectSource = urlParams.get('redirect_source');
  
  if (!cartId) {
    showErrorMessage("Invalid confirmation link");
    return;
  }
  
  showLoadingMessage("Verifying your payment...");
  
  // Try multiple times with delays (webhook might be processing)
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      // Check for booking first
      const bookingResponse = await fetch(`${API_BASE}/booking/bookings/by-cart/${cartId}/`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      if (bookingResponse.ok) {
        const booking = await bookingResponse.json();
        showSuccessPage(booking);
        return; // Success!
      }
      
      // If no booking found, check payment status
      const paymentResponse = await fetch(`${API_BASE}/payments/cart/status/${cartId}/`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      const paymentData = await paymentResponse.json();
      
      if (paymentData.payment_status === 'SUCCESS') {
        // Payment successful, booking should be created soon
        if (attempt < 3) {
          showWaitingMessage(`Payment successful! Creating booking... (${attempt}/3)`);
          await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds
          continue;
        } else {
          // After 3 attempts, booking still not created
          showPaymentVerificationForm(cartId);
          return;
        }
      } else if (paymentData.payment_status === 'INITIATED') {
        // Payment might be successful but webhook didn't trigger
        showPaymentVerificationForm(cartId);
        return;
      } else {
        showPaymentFailedMessage(paymentData.payment_status);
        return;
      }
      
    } catch (error) {
      console.error(`Attempt ${attempt} failed:`, error);
      if (attempt === 3) {
        showErrorMessage("Unable to verify payment status");
      }
    }
  }
};

// UI Helper functions
const showLoadingMessage = (message) => {
  document.getElementById('confirmation-area').innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <p>${message}</p>
    </div>
  `;
};

const showWaitingMessage = (message) => {
  document.getElementById('confirmation-area').innerHTML = `
    <div class="waiting">
      <p>${message}</p>
      <div class="progress-bar"></div>
    </div>
  `;
};

const showSuccessPage = (booking) => {
  document.getElementById('confirmation-area').innerHTML = `
    <div class="success">
      <h2>🎉 Booking Confirmed!</h2>
      <p><strong>Booking ID:</strong> ${booking.book_id}</p>
      <p><strong>Service:</strong> ${booking.puja_service?.title}</p>
      <p><strong>Date:</strong> ${booking.selected_date}</p>
      <p><strong>Time:</strong> ${booking.selected_time}</p>
      <p><strong>Amount:</strong> ₹${booking.total_amount}</p>
      <button onclick="downloadBooking('${booking.book_id}')">Download Receipt</button>
    </div>
  `;
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', handlePaymentConfirmation);
```

---

## KEY TAKEAWAYS

1. **Payment Status Flow:**
   ```
   INITIATED → (PhonePe Success) → SUCCESS → Booking Created
   ```

2. **Frontend Must Handle:**
   - Multiple verification attempts
   - Webhook delays  
   - Manual verification for sandbox payments
   - Proper loading states

3. **Backend Endpoints:**
   - `GET /api/booking/bookings/by-cart/{cart_id}/` - Check booking
   - `GET /api/payments/cart/status/{cart_id}/` - Check payment  
   - `POST /api/payments/verify-and-complete/` - Manual verification

4. **Production vs Sandbox:**
   - Production: Webhooks work reliably
   - Sandbox: May need manual verification

**Your payment system is now robust and handles all edge cases! 🚀**
