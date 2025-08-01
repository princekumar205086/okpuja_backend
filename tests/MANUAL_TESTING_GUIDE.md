# Manual Testing Guide for Cart → Payment → Booking Flow

## Prerequisites

1. **Test User Setup**
   - Admin user: `prince@gmail.com` (superuser)
   - Test user: `asliprinceraj@gmail.com` with password `testpass123`

## Step 1: Verify Database Setup

Run these commands one by one in PowerShell (wait for each to complete):

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Check Django setup
python check_users.py

# Check models and data
python check_models.py

# Check cart functionality
python test_cart_simple.py
```

## Step 2: Create Migrations (if needed)

```powershell
# Create migrations for payments app
python manage.py makemigrations payments

# Run all migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

## Step 3: Start Django Server

```powershell
# Start development server
python manage.py runserver 0.0.0.0:8000
```

Keep this terminal open and open a new terminal for testing.

## Step 4: Test API Endpoints

### 4.1 Get Authentication Token

**Request:**
```bash
POST http://localhost:8000/api/accounts/login/
Content-Type: application/json

{
  "email": "asliprinceraj@gmail.com",
  "password": "testpass123"
}
```

**Expected Response:**
```json
{
  "access": "your-jwt-token-here",
  "refresh": "refresh-token-here"
}
```

### 4.2 Create Cart

**Request:**
```bash
POST http://localhost:8000/api/cart/carts/
Authorization: Bearer your-jwt-token-here
Content-Type: application/json

{
  "service_type": "PUJA",
  "puja_service": 1,
  "package": 1,
  "selected_date": "2025-08-15",
  "selected_time": "10:00 AM"
}
```

**Expected Response:**
```json
{
  "id": 1,
  "cart_id": "CART_USER_001",
  "user": 1,
  "total_price": 999.00,
  "status": "ACTIVE"
}
```

### 4.3 Create Payment from Cart

**Request:**
```bash
POST http://localhost:8000/api/payments/cart/
Authorization: Bearer your-jwt-token-here
Content-Type: application/json

{
  "cart_id": "CART_USER_001",
  "redirect_url": "http://localhost:3000/confirmbooking"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Payment order created for cart",
  "data": {
    "payment_order": {
      "id": "uuid-here",
      "merchant_order_id": "CART_CART_USER_001_ABC123",
      "amount": 99900,
      "amount_in_rupees": 999.00,
      "cart_id": "CART_USER_001",
      "status": "INITIATED",
      "phonepe_payment_url": "https://api-preprod.phonepe.com/..."
    }
  }
}
```

### 4.4 Check Payment Status

**Request:**
```bash
GET http://localhost:8000/api/payments/cart/status/CART_USER_001/
Authorization: Bearer your-jwt-token-here
```

**Expected Response (before payment):**
```json
{
  "success": true,
  "data": {
    "cart_id": "CART_USER_001",
    "payment_status": "INITIATED",
    "booking_created": false,
    "booking_id": null
  }
}
```

### 4.5 Simulate Payment Success (for testing)

To test without actually paying through PhonePe, you can simulate a webhook:

**Request:**
```bash
POST http://localhost:8000/api/payments/webhook/phonepe/
Content-Type: application/json

{
  "merchantOrderId": "CART_CART_USER_001_ABC123",
  "eventType": "PAYMENT_SUCCESS",
  "transactionId": "TXN_TEST_123",
  "amount": 99900,
  "status": "SUCCESS"
}
```

### 4.6 Check Final Status

**Request:**
```bash
GET http://localhost:8000/api/payments/cart/status/CART_USER_001/
Authorization: Bearer your-jwt-token-here
```

**Expected Response (after payment):**
```json
{
  "success": true,
  "data": {
    "cart_id": "CART_USER_001",
    "payment_status": "SUCCESS",
    "booking_created": true,
    "booking_id": "BK-12345678",
    "cart_status": "CONVERTED"
  }
}
```

## Step 5: Test Redirect Flow

1. **Get Payment URL** from step 4.3
2. **Visit the URL** in browser (will redirect to PhonePe)
3. **After payment**, you'll be redirected to:
   ```
   http://localhost:3000/confirmbooking?redirect_source=phonepe
   ```

## Step 6: Verify Complete Flow

Run the integration test:

```powershell
# Run complete flow test
python test_complete_flow.py
```

## Expected Test Results

If everything is working correctly, you should see:

```
🧪 Complete Integration Testing

🚀 Testing Complete Cart -> Payment -> Booking Flow

✅ All models imported successfully
✅ Using test user: asliprinceraj@gmail.com
✅ Using puja service: [Service Name]
✅ Using package: [Package Type] - ₹[Price]
✅ Cart created successfully: TEST-CART-[USER-ID]-001
✅ Payment order created: CART_TEST-CART-[USER-ID]-001_[ID]
✅ Webhook processed successfully
✅ Payment status: SUCCESS
✅ Booking created successfully: BK-[BOOKING-ID]

🔗 Testing Cart Payment API Flow

✅ Using cart: [CART-ID]
✅ Cart Payment API endpoints are properly defined

==================================================
🎉 ALL TESTS PASSED!
```

## Troubleshooting

### Common Issues

1. **User Not Found**
   - Create user: `python manage.py shell`
   - Then: `User.objects.create_user('asliprinceraj@gmail.com', 'testpass123')`

2. **No Puja Services/Packages**
   - Access admin: http://localhost:8000/admin/
   - Login with: `prince@gmail.com`
   - Create puja services and packages

3. **Migration Issues**
   - Run: `python manage.py makemigrations`
   - Then: `python manage.py migrate`

4. **Import Errors**
   - Check if all apps are in `INSTALLED_APPS`
   - Verify virtual environment is activated

5. **PhonePe Integration Issues**
   - Check `.env` file configuration
   - Verify PhonePe credentials are correct
   - Ensure redirect URLs are properly set

## Frontend Integration

Once backend testing is complete, update your Next.js frontend:

### 1. Update Cart Payment Function

```javascript
// Instead of old payment endpoint
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

### 2. Update Confirm Booking Page

```javascript
// Poll payment status
const checkPaymentStatus = async (cartId) => {
  const response = await api.get(`/api/payments/cart/status/${cartId}/`);
  return response.data;
};
```

## Success Criteria

- ✅ Cart creation works without import errors
- ✅ Payment order creation from cart works
- ✅ PhonePe redirect URLs are correct
- ✅ Webhook processing works
- ✅ Booking auto-creation on payment success
- ✅ Status checking APIs work
- ✅ Complete flow test passes

Once all these steps pass, your cart → payment → booking flow is fully functional!
