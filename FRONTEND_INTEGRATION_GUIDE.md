# COMPLETE BOOKING FLOW - FRONTEND API SEQUENCE
# ============================================

## AUTHENTICATION & SETUP
```
Base URL: http://127.0.0.1:8000/api
Authorization: Bearer {access_token}
Content-Type: application/json
```

## 1. USER LOGIN ✅
```
POST /auth/login/
{
  "email": "asliprinceraj@gmail.com",
  "password": "testpass123"
}
→ Store access token from response
```

## 2. ADD TO CART ✅
```
POST /cart/carts/
{
  "service_type": "PUJA",
  "puja_service": 8,
  "package_id": 2,
  "selected_date": "2025-09-12",
  "selected_time": "16:30"
}
→ Store cart_id from response
```

## 3. CREATE PAYMENT ✅
```
POST /payments/cart/
{
  "cart_id": "{cart_id_from_step_2}"
}
→ Redirect user to phonepe_payment_url from response
```

## 4. AFTER PHONEPE REDIRECT (User completes payment) ✅
```
PhonePe redirects to: 
http://localhost:3000/confirmbooking?cart_id={cart_id}&order_id={order_id}&redirect_source=phonepe

Frontend should:
1. Extract cart_id from URL
2. Call: GET /booking/bookings/by-cart/{cart_id}/
3. If booking found → Show success
4. If not found → Call payment status check
```

## 5. VERIFY BOOKING CREATION ✅
```
GET /booking/bookings/by-cart/{cart_id}/
→ If 200: Booking created successfully
→ If 404: Check payment status below
```

## 6. CHECK PAYMENT STATUS (If needed) ✅
```
GET /payments/cart/status/{cart_id}/
→ Check payment_status field:
  - "SUCCESS" → Booking will be auto-created (wait/refresh)
  - "INITIATED" → Payment still processing
  - "FAILED" → Show payment failed
```

## 7. GET LATEST BOOKING (For dashboard) ✅
```
GET /booking/bookings/latest/
→ Shows user's most recent booking
```

## 8. CART CLEANUP ✅
```
POST /cart/carts/clear_converted/
→ This happens AUTOMATICALLY after booking creation
→ Frontend doesn't need to call this manually
```

---

# FRONTEND IMPLEMENTATION COMMANDS

## Step-by-Step Commands for Testing:

### 1. Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "asliprinceraj@gmail.com", "password": "testpass123"}'
```

### 2. Add to Cart  
```bash
curl -X POST http://127.0.0.1:8000/api/cart/carts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "PUJA",
    "puja_service": 8,
    "package_id": 2,
    "selected_date": "2025-09-12",
    "selected_time": "16:30"
  }'
```

### 3. Create Payment
```bash
curl -X POST http://127.0.0.1:8000/api/payments/cart/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cart_id": "YOUR_CART_ID"}'
```

### 4. Check Booking
```bash
curl -X GET http://127.0.0.1:8000/api/booking/bookings/by-cart/YOUR_CART_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Check Payment Status
```bash
curl -X GET http://127.0.0.1:8000/api/payments/cart/status/YOUR_CART_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Get Latest Booking
```bash
curl -X GET http://127.0.0.1:8000/api/booking/bookings/latest/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

# JAVASCRIPT/REACT IMPLEMENTATION EXAMPLE

```javascript
const API_BASE = 'http://127.0.0.1:8000/api';

// 1. Login
const login = async (email, password) => {
  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  return data;
};

// 2. Add to Cart
const addToCart = async (serviceData) => {
  const response = await fetch(`${API_BASE}/cart/carts/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(serviceData)
  });
  return await response.json();
};

// 3. Create Payment
const createPayment = async (cartId) => {
  const response = await fetch(`${API_BASE}/payments/cart/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ cart_id: cartId })
  });
  const data = await response.json();
  // Redirect to PhonePe
  window.location.href = data.data.payment_order.phonepe_payment_url;
};

// 4. Check Booking (After PhonePe redirect)
const checkBooking = async (cartId) => {
  const response = await fetch(`${API_BASE}/booking/bookings/by-cart/${cartId}/`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  if (response.ok) {
    return await response.json(); // Booking found
  } else {
    return null; // Check payment status
  }
};

// 5. Check Payment Status
const checkPaymentStatus = async (cartId) => {
  const response = await fetch(`${API_BASE}/payments/cart/status/${cartId}/`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return await response.json();
};
```

---

# FLOW DIAGRAM

```
User Login
    ↓
Add to Cart → Get cart_id
    ↓
Create Payment → Get phonepe_payment_url
    ↓
Redirect to PhonePe → User completes payment
    ↓
PhonePe Redirect → Extract cart_id from URL
    ↓
Check Booking by cart_id
    ↓
If Found: Show Success
If Not Found: Check Payment Status
    ↓
If SUCCESS: Wait for auto-booking creation
If FAILED: Show error
If INITIATED: Show processing
```

---

# IMPORTANT NOTES

✅ **Working Endpoints**: All endpoints are tested and working
✅ **Auto-Booking**: Bookings are automatically created when payments complete
✅ **Email Notifications**: Sent automatically to user and admin
✅ **Cart Cleanup**: Happens automatically after booking creation
✅ **Error Handling**: Proper status codes and error messages

⚠️ **Testing Note**: In sandbox/testing, you may need to simulate successful payment completion as PhonePe webhooks might not fire in test environment.

🎯 **Production Ready**: System is ready for production deployment with proper PhonePe webhook configuration.
