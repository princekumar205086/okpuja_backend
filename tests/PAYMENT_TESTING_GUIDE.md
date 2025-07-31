## Manual Payment Testing Guide

### Test Environment Setup
- **API Base URL**: `http://localhost:8000`
- **Test User Email**: `asliprinceraj@gmail.com`
- **Test User Password**: `testpass123`

### Step-by-Step Testing Process

#### Step 1: User Authentication
```bash
# Login to get access token
curl -X POST http://localhost:8000/api/accounts/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"asliprinceraj@gmail.com","password":"testpass123"}'
```

Expected Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {...}
}
```

#### Step 2: Get Available Puja Services
```bash
# Replace TOKEN with the access token from step 1
curl -X GET http://localhost:8000/api/puja/services/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json"
```

#### Step 3: Create Cart
```bash
# Replace TOKEN, SERVICE_ID, and PACKAGE_ID with actual values
curl -X POST http://localhost:8000/api/cart/carts/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "PUJA",
    "puja_service": SERVICE_ID,
    "package": PACKAGE_ID,
    "selected_date": "2025-08-02",
    "selected_time": "10:00"
  }'
```

Expected Response:
```json
{
  "id": 123,
  "total_price": "100.00",
  "status": "ACTIVE",
  ...
}
```

#### Step 4: Process Payment
```bash
# Replace TOKEN and CART_ID with actual values
curl -X POST http://localhost:8000/api/payments/payments/process-cart/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": CART_ID,
    "method": "PHONEPE"
  }'
```

Expected Response (Success):
```json
{
  "success": true,
  "payment_id": 456,
  "transaction_id": "TXN123ABC",
  "merchant_transaction_id": "TX20250726123456ABC",
  "amount": "100.00",
  "currency": "INR",
  "payment_url": "https://api-preprod.phonepe.com/...",
  "status": "PENDING"
}
```

Expected Response (Debug Mode with Connectivity Issues):
```json
{
  "error": "Payment processing failed",
  "error_category": "CONNECTION_REFUSED",
  "user_message": "Unable to connect to payment gateway...",
  "debug_options": {
    "simulate_payment_url": "/api/payments/payments/456/simulate-success/",
    "debug_connectivity_url": "/api/payments/payments/debug-connectivity/"
  }
}
```

#### Step 5: Test Debug Connectivity (if needed)
```bash
curl -X GET http://localhost:8000/api/payments/payments/debug-connectivity/ \
  -H "Authorization: Bearer TOKEN"
```

#### Step 6: Simulate Payment Success (Development Only)
```bash
# If PhonePe connectivity fails, simulate payment success
curl -X POST http://localhost:8000/api/payments/payments/PAYMENT_ID/simulate-success/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json"
```

### PowerShell Testing Commands

```powershell
# Step 1: Login
$loginBody = '{"email":"asliprinceraj@gmail.com","password":"testpass123"}'
$loginResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/accounts/auth/login/' -Method POST -Body $loginBody -ContentType 'application/json'
$token = $loginResponse.access

# Step 2: Get Services
$headers = @{'Authorization'="Bearer $token"; 'Content-Type'='application/json'}
$services = Invoke-RestMethod -Uri 'http://localhost:8000/api/puja/services/' -Headers $headers

# Step 3: Create Cart (replace with actual IDs)
$cartBody = '{"service_type":"PUJA","puja_service":1,"package":1,"selected_date":"2025-08-02","selected_time":"10:00"}'
$cart = Invoke-RestMethod -Uri 'http://localhost:8000/api/cart/carts/' -Method POST -Body $cartBody -Headers $headers

# Step 4: Process Payment
$paymentBody = "{`"cart_id`":$($cart.id),`"method`":`"PHONEPE`"}"
$payment = Invoke-RestMethod -Uri 'http://localhost:8000/api/payments/payments/process-cart/' -Method POST -Body $paymentBody -Headers $headers
```

### Troubleshooting

#### Common Issues:
1. **User doesn't exist**: Create user through Django admin or shell
2. **No puja services**: Create test services and packages
3. **PhonePe connectivity issues**: Use simulation endpoints in debug mode
4. **Cart validation errors**: Ensure selected date is in future

#### Debug Endpoints:
- **Connectivity Test**: `GET /api/payments/payments/debug-connectivity/`
- **Payment Simulation**: `POST /api/payments/payments/{payment_id}/simulate-success/`
- **Booking Status Check**: `GET /api/payments/payments/{payment_id}/check-booking/`

#### Expected Test Flow:
1. ✅ User authentication successful
2. ✅ Puja services retrieved
3. ✅ Cart created with total price
4. ⚠️ PhonePe connectivity test (might fail in local development)
5. 🎯 Payment simulation used for testing
6. ✅ Booking created from successful payment

### Production vs Development
- **Development**: Uses simulation endpoints when PhonePe is unreachable
- **Production**: Uses actual PhonePe V2 Standard Checkout API
- **UAT Testing**: Uses PhonePe sandbox environment with test credentials

### PhonePe V2 Configuration
Current `.env` settings are configured for PhonePe V2 UAT testing:
- Client ID: `TAJFOOTWEARUAT_2503031838273556894438`
- Environment: `UAT` (sandbox)
- API URLs: `https://api-preprod.phonepe.com/apis/pg-sandbox`
