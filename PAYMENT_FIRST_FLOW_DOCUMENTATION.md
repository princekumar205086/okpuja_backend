# Payment-First Booking Flow API Documentation

## Overview
This document describes the new **Payment-First Booking Flow** implementation for the OkPuja backend. This approach ensures that bookings are only created after successful payment, preventing unpaid bookings in the system.

## Flow Summary
1. **Cart Creation**: User adds items to cart
2. **Payment Initiation**: Create payment linked to cart (NOT booking)
3. **Payment Gateway**: Process payment through PhonePe/other gateways
4. **Webhook Processing**: Receive payment status from gateway
5. **Booking Creation**: Create booking only after payment success
6. **Cart Conversion**: Mark cart as CONVERTED

## Key Changes Made

### 1. Payment Model Updates
- **Made `booking` field nullable**: `null=True, blank=True`
- **Added `cart` field**: Direct link to cart for payment-first flow
- **Added `user` field**: Direct user reference for easier queries
- **New method**: `create_booking_from_cart()` for post-payment booking creation

### 2. New API Endpoints

#### Process Cart Payment
**Endpoint**: `POST /api/payments/process-cart/`
**Purpose**: Main endpoint for payment-first flow

**Request Example**:
```json
{
    "cart_id": 123,
    "method": "PHONEPE"
}
```

**Response Example**:
```json
{
    "success": true,
    "payment_id": 456,
    "transaction_id": "TXN46B5EE6E7D",
    "merchant_transaction_id": "MT7a8b9c0d1e2f3",
    "amount": "999.00",
    "currency": "INR",
    "payment_url": "https://mercury-t2.phonepe.com/transact/...",
    "status": "PENDING",
    "cart_id": 123
}
```

#### Check Booking Status
**Endpoint**: `GET /api/payments/{payment_id}/check-booking/`
**Purpose**: Check if payment resulted in booking creation

**Response Examples**:

**Payment Successful + Booking Created**:
```json
{
    "success": true,
    "payment_status": "SUCCESS",
    "booking_created": true,
    "booking": {
        "id": 789,
        "book_id": "BK-449034CB",
        "user": {...},
        "selected_date": "2025-07-15",
        "selected_time": "10:30:00",
        "status": "CONFIRMED",
        "total_amount": "999.00"
    }
}
```

**Payment Successful + Booking Pending**:
```json
{
    "success": true,
    "payment_status": "SUCCESS",
    "booking_created": false,
    "message": "Payment successful but booking creation pending"
}
```

**Payment Failed**:
```json
{
    "success": false,
    "payment_status": "FAILED",
    "booking_created": false,
    "message": "Payment status: Failed"
}
```

### 3. Webhook Processing Enhancement
The webhook now automatically creates bookings when payments succeed:

```python
# In PaymentGateway.process_webhook()
if payment.status == PaymentStatus.SUCCESS and not payment.booking:
    try:
        booking = payment.create_booking_from_cart()
        logger.info(f"Booking {booking.book_id} created for payment {payment.transaction_id}")
    except Exception as e:
        logger.error(f"Failed to create booking: {str(e)}")
```

## Complete API Flow Example

### Step 1: Create Cart (Existing API)
```bash
POST /api/cart/carts/
Content-Type: application/json
Authorization: Bearer {token}

{
    "service_type": "PUJA",
    "puja_service": 1,
    "package_id": 2,
    "selected_date": "2025-07-20",
    "selected_time": "10:30"
}
```

**Response**:
```json
{
    "id": 123,
    "cart_id": "fb0bf338-b549-4ed5-8b91-dca76245cb27",
    "user": 1,
    "service_type": "PUJA",
    "puja_service": {...},
    "package": {...},
    "selected_date": "2025-07-20",
    "selected_time": "10:30",
    "status": "ACTIVE",
    "total_price": "999.00"
}
```

### Step 2: Process Payment (New API)
```bash
POST /api/payments/process-cart/
Content-Type: application/json
Authorization: Bearer {token}

{
    "cart_id": 123,
    "method": "PHONEPE"
}
```

**Response**:
```json
{
    "success": true,
    "payment_id": 456,
    "transaction_id": "TXN46B5EE6E7D",
    "merchant_transaction_id": "MT7a8b9c0d1e2f3",
    "amount": "999.00",
    "currency": "INR",
    "payment_url": "https://mercury-t2.phonepe.com/transact/pg-ui/...",
    "status": "PENDING",
    "cart_id": 123
}
```

### Step 3: Redirect User to Payment Gateway
Frontend redirects user to `payment_url` for payment completion.

### Step 4: Payment Gateway Webhook (Automatic)
Gateway sends webhook to `/api/payments/webhook/phonepe/` upon payment completion.

### Step 5: Check Booking Status (New API)
```bash
GET /api/payments/456/check-booking/
Authorization: Bearer {token}
```

**Response (after successful payment)**:
```json
{
    "success": true,
    "payment_status": "SUCCESS",
    "booking_created": true,
    "booking": {
        "id": 789,
        "book_id": "BK-449034CB",
        "user": {
            "id": 1,
            "email": "user@example.com"
        },
        "cart": {
            "cart_id": "fb0bf338-b549-4ed5-8b91-dca76245cb27",
            "total_price": "999.00"
        },
        "selected_date": "2025-07-20",
        "selected_time": "10:30:00",
        "status": "CONFIRMED",
        "total_amount": "999.00",
        "created_at": "2025-07-15T...",
        "address": {...}
    }
}
```

## Error Handling

### Validation Errors
```json
{
    "error": "Cart payment processing failed",
    "details": "Active cart not found"
}
```

### Amount Mismatch
```json
{
    "amount": ["Payment amount must be exactly 999.00"]
}
```

### Payment Gateway Errors
```json
{
    "error": "Payment processing failed",
    "details": "PhonePe payment failed: Invalid merchant ID"
}
```

## Benefits of Payment-First Approach

### ✅ **Data Integrity**
- No unpaid bookings in the system
- Clean separation of cart, payment, and booking states
- Atomic transactions ensure consistency

### ✅ **Better User Experience**
- Clear payment status tracking
- Automatic booking creation after payment
- Proper error handling for failed payments

### ✅ **Business Logic**
- Cart remains active until payment success
- Easy to retry failed payments
- Clear audit trail of payment → booking flow

### ✅ **Production Ready**
- Graceful error handling
- Webhook validation
- Proper logging and monitoring

## Testing
Run the comprehensive test suite:
```bash
python test_payment_first_flow.py
```

This tests:
- ✅ Cart creation
- ✅ Payment-first approach (payment created before booking)
- ✅ Payment gateway simulation
- ✅ Automatic booking creation after payment success
- ✅ Cart status update to CONVERTED
- ✅ Payment-booking linking
- ✅ Error handling for edge cases
- ✅ API endpoint availability

## Production Deployment Checklist

### Environment Configuration
- [ ] Update `.env` with production PhonePe credentials
- [ ] Set correct webhook URLs in PhonePe dashboard
- [ ] Configure email settings for notifications
- [ ] Set up proper logging and monitoring

### Database Migration
```bash
python manage.py migrate payment
```

### PhonePe Configuration
- [ ] Update webhook URLs to production domain
- [ ] Test webhook signature validation
- [ ] Set proper redirect URLs

### Monitoring
- [ ] Monitor payment webhook processing
- [ ] Track booking creation success rates
- [ ] Set up alerts for failed payment processing

## Security Considerations

### Webhook Security
- ✅ Webhook signature validation implemented
- ✅ Protected endpoints with proper authentication
- ✅ Input validation on all payment parameters

### Data Protection
- ✅ Payment data encrypted in transit
- ✅ No sensitive card data stored
- ✅ Proper user authorization checks

This implementation ensures robust, secure, and user-friendly payment processing while maintaining data integrity throughout the booking flow.


<!-- 

{
  "info": {
    "name": "OKPUJA Cart, Payments, Booking API",
    "description": "Test all endpoints for Cart, Payments, and Booking apps (payment-first flow)",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Cart",
      "item": [
        {
          "name": "Create Cart",
          "request": {
            "method": "POST",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/cart/carts/", "host": ["{{base_url}}"], "path": ["api", "cart", "carts"] },
            "body": {
              "mode": "raw",
              "raw": "{\n  \"service_type\": \"PUJA\",\n  \"puja_service\": 1,\n  \"package_id\": 1,\n  \"selected_date\": \"2025-07-20\",\n  \"selected_time\": \"10:00 AM\"\n}"
            }
          }
        },
        {
          "name": "Get Active Carts",
          "request": {
            "method": "GET",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/cart/carts/active/", "host": ["{{base_url}}"], "path": ["api", "cart", "carts", "active"] }
          }
        },
        {
          "name": "Apply Promo Code",
          "request": {
            "method": "POST",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/cart/carts/{{cart_id}}/apply_promo/", "host": ["{{base_url}}"], "path": ["api", "cart", "carts", "{{cart_id}}", "apply_promo"] },
            "body": {
              "mode": "raw",
              "raw": "{\n  \"promo_code\": \"DISCOUNT10\"\n}"
            }
          }
        }
      ]
    },
    {
      "name": "Payments",
      "item": [
        {
          "name": "Initiate Payment (Payment-First)",
          "request": {
            "method": "POST",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/payments/process-cart/", "host": ["{{base_url}}"], "path": ["api", "payments", "process-cart"] },
            "body": {
              "mode": "raw",
              "raw": "{\n  \"cart_id\": {{cart_id}},\n  \"amount\": 500.00\n}"
            }
          }
        },
        {
          "name": "Check Payment Status",
          "request": {
            "method": "GET",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/payments/payments/{{payment_id}}/", "host": ["{{base_url}}"], "path": ["api", "payments", "payments", "{{payment_id}}"] }
          }
        },
        {
          "name": "Check Booking After Payment",
          "request": {
            "method": "GET",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/payments/payments/{{payment_id}}/check-booking/", "host": ["{{base_url}}"], "path": ["api", "payments", "payments", "{{payment_id}}", "check-booking"] }
          }
        }
      ]
    },
    {
      "name": "Booking",
      "item": [
        {
          "name": "Get My Bookings",
          "request": {
            "method": "GET",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/booking/bookings/", "host": ["{{base_url}}"], "path": ["api", "booking", "bookings"] }
          }
        },
        {
          "name": "Get Booking Details",
          "request": {
            "method": "GET",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/booking/bookings/{{booking_id}}/", "host": ["{{base_url}}"], "path": ["api", "booking", "bookings", "{{booking_id}}"] }
          }
        },
        {
          "name": "Reschedule Booking",
          "request": {
            "method": "POST",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}", "type": "text" }
            ],
            "url": { "raw": "{{base_url}}/api/booking/bookings/{{booking_id}}/reschedule/", "host": ["{{base_url}}"], "path": ["api", "booking", "bookings", "{{booking_id}}", "reschedule"] },
            "body": {
              "mode": "raw",
              "raw": "{\n  \"selected_date\": \"2025-07-22\",\n  \"selected_time\": \"11:00 AM\",\n  \"reason\": \"Change of plans\"\n}"
            }
          }
        }
      ]
    }
  ],
  "variable": [
    { "key": "base_url", "value": "http://127.0.0.1:8000" },
    { "key": "token", "value": "" },
    { "key": "cart_id", "value": "" },
    { "key": "payment_id", "value": "" },
    { "key": "booking_id", "value": "" }
  ]
}


 -->