# Complete Cart -> Payment -> Booking Flow Documentation

## Overview

This document outlines the complete integration flow from cart creation to booking completion, using the new `payments` app with PhonePe V2 integration.

## Flow Architecture

```
Frontend (Next.js) → Cart Creation → Payment → PhonePe → Webhook → Booking Creation → Confirmation
```

## Step-by-Step Flow

### 1. Cart Creation (Frontend)

**Endpoint:** `POST /api/cart/carts/`

**Payload:**
```json
{
  "service_type": "PUJA",
  "puja_service": 1,
  "package": 1,
  "selected_date": "2025-08-15",
  "selected_time": "10:00 AM",
  "promo_code": null
}
```

**Response:**
```json
{
  "id": 1,
  "cart_id": "CART_USER1_001",
  "user": 1,
  "total_price": 999.00,
  "status": "ACTIVE",
  "created_at": "2025-08-01T10:00:00Z"
}
```

### 2. Payment Initiation (Frontend)

**Endpoint:** `POST /api/payments/cart/`

**Payload:**
```json
{
  "cart_id": "CART_USER1_001",
  "redirect_url": "http://localhost:3000/confirmbooking"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Payment order created for cart",
  "data": {
    "payment_order": {
      "id": "uuid-here",
      "merchant_order_id": "CART_CART_USER1_001_ABC123",
      "amount": 99900,
      "amount_in_rupees": 999.00,
      "cart_id": "CART_USER1_001",
      "status": "INITIATED",
      "phonepe_payment_url": "https://api-preprod.phonepe.com/...",
      "created_at": "2025-08-01T10:00:00Z"
    }
  }
}
```

### 3. PhonePe Payment (User)

1. Frontend redirects user to `phonepe_payment_url`
2. User completes payment on PhonePe
3. PhonePe redirects to our redirect handler: `/api/payments/redirect/simple/`
4. Redirect handler forwards to frontend: `http://localhost:3000/confirmbooking?redirect_source=phonepe`

### 4. Payment Status Check (Frontend)

**Endpoint:** `GET /api/payments/cart/status/CART_USER1_001/`

**Response:**
```json
{
  "success": true,
  "data": {
    "cart_id": "CART_USER1_001",
    "payment_status": "SUCCESS",
    "payment_amount": 999.00,
    "merchant_order_id": "CART_CART_USER1_001_ABC123",
    "booking_created": true,
    "booking_id": "BK-12345678",
    "cart_status": "CONVERTED",
    "payment_created_at": "2025-08-01T10:00:00Z",
    "payment_completed_at": "2025-08-01T10:05:00Z"
  }
}
```

### 5. Automatic Booking Creation (Backend)

When PhonePe webhook is received with payment success:

1. **Webhook Processing:** `/api/payments/webhook/phonepe/`
2. **Payment Status Update:** Mark payment as `SUCCESS`
3. **Auto-Booking Creation:** Create booking from cart
4. **Cart Status Update:** Mark cart as `CONVERTED`

## API Endpoints

### Cart Endpoints
- `POST /api/cart/carts/` - Create cart
- `GET /api/cart/carts/` - List user's carts
- `DELETE /api/cart/carts/{id}/` - Delete cart

### Payment Endpoints
- `POST /api/payments/cart/` - Create payment from cart
- `GET /api/payments/cart/status/{cart_id}/` - Get cart payment status
- `GET /api/payments/status/{merchant_order_id}/` - Get payment order status
- `POST /api/payments/webhook/phonepe/` - PhonePe webhook handler

### Redirect Endpoints
- `GET /api/payments/redirect/` - Smart redirect handler
- `GET /api/payments/redirect/simple/` - Simple redirect handler

### Booking Endpoints
- `GET /api/booking/bookings/` - List user's bookings
- `GET /api/booking/bookings/{id}/` - Get booking details

## Frontend Integration

### 1. Cart Management

```javascript
// Create cart
const createCart = async (cartData) => {
  const response = await api.post('/api/cart/carts/', cartData);
  return response.data;
};

// Get user's carts
const getCarts = async () => {
  const response = await api.get('/api/cart/carts/');
  return response.data;
};
```

### 2. Payment Processing

```javascript
// Initiate payment from cart
const initiatePayment = async (cartId) => {
  const response = await api.post('/api/payments/cart/', {
    cart_id: cartId,
    redirect_url: `${window.location.origin}/confirmbooking`
  });
  
  if (response.data.success) {
    // Redirect to PhonePe
    window.location.href = response.data.data.payment_order.phonepe_payment_url;
  }
};
```

### 3. Payment Status Polling

```javascript
// Check payment status (for confirmbooking page)
const checkPaymentStatus = async (cartId) => {
  const response = await api.get(`/api/payments/cart/status/${cartId}/`);
  return response.data;
};

// Poll payment status until completion
const pollPaymentStatus = async (cartId) => {
  const maxAttempts = 30; // 30 seconds
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    const status = await checkPaymentStatus(cartId);
    
    if (status.data.payment_status === 'SUCCESS' && status.data.booking_created) {
      return status.data; // Payment successful, booking created
    }
    
    if (status.data.payment_status === 'FAILED') {
      throw new Error('Payment failed');
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
    attempts++;
  }
  
  throw new Error('Payment status check timeout');
};
```

### 4. Confirm Booking Page

```javascript
// pages/confirmbooking.js
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function ConfirmBooking() {
  const router = useRouter();
  const [status, setStatus] = useState('checking');
  const [bookingData, setBookingData] = useState(null);
  
  useEffect(() => {
    const checkStatus = async () => {
      try {
        // Get cart ID from URL params or localStorage
        const cartId = getCartIdFromStorage(); // Your implementation
        
        if (!cartId) {
          setStatus('error');
          return;
        }
        
        const result = await pollPaymentStatus(cartId);
        
        setBookingData(result);
        setStatus('success');
        
        // Clear cart from storage
        clearCartFromStorage();
        
      } catch (error) {
        console.error('Payment verification failed:', error);
        setStatus('failed');
      }
    };
    
    checkStatus();
  }, []);
  
  if (status === 'checking') {
    return <div>Verifying payment...</div>;
  }
  
  if (status === 'success') {
    return (
      <div>
        <h1>Booking Confirmed!</h1>
        <p>Booking ID: {bookingData.booking_id}</p>
        <p>Amount Paid: ₹{bookingData.payment_amount}</p>
      </div>
    );
  }
  
  return <div>Payment verification failed</div>;
}
```

## Environment Configuration

### Backend (.env)
```bash
# PhonePe Configuration
PHONEPE_MERCHANT_ID=M22KEWU5BO1I2
PHONEPE_CLIENT_ID=TEST-M22KEWU5BO1I2_25070
PHONEPE_ENV=UAT
PHONEPE_SUCCESS_REDIRECT_URL=http://localhost:3000/confirmbooking/
PHONEPE_FAILED_REDIRECT_URL=http://localhost:3000/failedbooking/

# Frontend URL
FRONTEND_BASE_URL=http://localhost:3000
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Error Handling

### Common Scenarios

1. **Cart Not Found**
   - Status: 404
   - Message: "Cart not found"

2. **Cart Already Paid**
   - Status: 400
   - Message: "Cart has already been paid for"

3. **Payment Timeout**
   - Frontend should handle timeout after 30 seconds
   - Show appropriate error message

4. **PhonePe Payment Failed**
   - Payment status will be "FAILED"
   - No booking will be created

## Database Schema Changes

### PaymentOrder Model (Added)
```python
class PaymentOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    merchant_order_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart_id = models.CharField(max_length=100, null=True, blank=True)  # NEW
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    # ... other fields
```

### Migration Required
```bash
python manage.py makemigrations payments
python manage.py migrate
```

## Testing

### Manual Testing Steps

1. **Create Cart**
   ```bash
   curl -X POST http://localhost:8000/api/cart/carts/ \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"service_type": "PUJA", "puja_service": 1, "package": 1, "selected_date": "2025-08-15", "selected_time": "10:00 AM"}'
   ```

2. **Initiate Payment**
   ```bash
   curl -X POST http://localhost:8000/api/payments/cart/ \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"cart_id": "CART_ID_HERE"}'
   ```

3. **Check Status**
   ```bash
   curl -X GET http://localhost:8000/api/payments/cart/status/CART_ID_HERE/ \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

### Automated Testing
```bash
python test_complete_flow.py
```

## Production Considerations

1. **Environment Variables**
   - Update PhonePe URLs for production
   - Use production merchant credentials
   - Set correct redirect URLs

2. **Security**
   - Verify webhook signatures
   - Use HTTPS for all endpoints
   - Implement rate limiting

3. **Monitoring**
   - Log all payment transactions
   - Monitor webhook delivery
   - Set up alerts for failed payments

4. **Performance**
   - Implement caching for payment status
   - Use database indexing
   - Monitor response times

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all apps are in INSTALLED_APPS
   - Run migrations
   - Check model imports

2. **Webhook Not Received**
   - Verify callback URL configuration
   - Check PhonePe dashboard
   - Ensure webhook endpoint is accessible

3. **Booking Not Created**
   - Check webhook processing logs
   - Verify cart status
   - Check for exceptions in booking creation

4. **Payment Status Not Updated**
   - Verify PhonePe credentials
   - Check API response logs
   - Ensure proper error handling
