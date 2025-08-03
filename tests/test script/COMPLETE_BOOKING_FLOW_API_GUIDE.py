"""
COMPLETE BOOKING FLOW - API ENDPOINTS SEQUENCE
==============================================

This document provides the exact sequence of API endpoints that the frontend 
should hit for a complete booking flow from cart creation to cleanup.

AUTHENTICATION REQUIRED: All endpoints require Bearer token in Authorization header
"""

# =============================================================================
# STEP 1: USER AUTHENTICATION
# =============================================================================
"""
1.1 USER LOGIN
--------------
POST /api/auth/login/
Content-Type: application/json

Body:
{
  "email": "user@example.com", 
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "id": 2,
  "email": "user@example.com",
  "role": "USER"
}

Store the 'access' token for subsequent requests.
"""

# =============================================================================
# STEP 2: CART MANAGEMENT 
# =============================================================================
"""
2.1 CREATE CART (Add service to cart)
-------------------------------------
POST /api/cart/carts/
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "service_type": "PUJA",
  "puja_service": 8,           // Puja service ID
  "package_id": 2,             // Package ID  
  "selected_date": "2025-09-12",
  "selected_time": "16:30"
}

Response:
{
  "id": 96,
  "cart_id": "d7a594ac-9333-4213-985f-67942a3b638b",
  "user": 2,
  "service_type": "PUJA",
  "puja_service": {...},
  "package": {...},
  "selected_date": "2025-09-12",
  "selected_time": "16:30",
  "status": "ACTIVE",
  "total_price": "5000.00"
}

IMPORTANT: Store the 'cart_id' for payment step.
"""

"""
2.2 GET ACTIVE CART (Optional - to verify cart)
-----------------------------------------------
GET /api/cart/carts/active/
Authorization: Bearer {access_token}

Response:
{
  "cart_id": "d7a594ac-9333-4213-985f-67942a3b638b",
  "status": "ACTIVE",
  "total_price": "5000.00",
  // ... cart details
}
"""

# =============================================================================
# STEP 3: PAYMENT PROCESSING
# =============================================================================
"""
3.1 CREATE PAYMENT ORDER
------------------------
POST /api/payments/cart/
Authorization: Bearer {access_token}
Content-Type: application/json

Body:
{
  "cart_id": "d7a594ac-9333-4213-985f-67942a3b638b"
}

Response:
{
  "success": true,
  "message": "Payment order created for cart",
  "data": {
    "payment_order": {
      "id": "d755ac99-094e-45b8-9017-80106bcfb957",
      "merchant_order_id": "CART_d7a594ac-9333-4213-985f-67942a3b638b_260E14E5",
      "amount": 500000,               // Amount in paisa (₹5000.00)
      "amount_in_rupees": 5000,
      "cart_id": "d7a594ac-9333-4213-985f-67942a3b638b",
      "status": "INITIATED",
      "phonepe_payment_url": "https://mercury-uat.phonepe.com/transact/uat_v2?token=...",
      "created_at": "2025-08-02T19:06:42.446457+00:00"
    }
  }
}

IMPORTANT: 
- Store 'merchant_order_id' for tracking
- Redirect user to 'phonepe_payment_url' for payment
"""

"""
3.2 REDIRECT USER TO PHONEPE
----------------------------
Frontend should redirect user to the 'phonepe_payment_url' from step 3.1
User completes payment on PhonePe platform.

After payment completion, PhonePe will redirect back to:
http://localhost:3000/confirmbooking?cart_id={cart_id}&order_id={order_id}&redirect_source=phonepe
"""

# =============================================================================
# STEP 4: PAYMENT VERIFICATION & BOOKING CREATION
# =============================================================================
"""
4.1 VERIFY BOOKING EXISTS (After PhonePe redirect)
--------------------------------------------------
GET /api/booking/bookings/by-cart/{cart_id}/
Authorization: Bearer {access_token}

Example:
GET /api/booking/bookings/by-cart/d7a594ac-9333-4213-985f-67942a3b638b/

Response (Success):
{
  "id": 45,
  "book_id": "BK-103AE4E3",
  "user": 2,
  "cart": {
    "cart_id": "d7a594ac-9333-4213-985f-67942a3b638b",
    "total_price": "5000.00"
  },
  "puja_service": {...},
  "package": {...},
  "selected_date": "2025-09-12",
  "selected_time": "16:30:00",
  "status": "CONFIRMED",
  "total_amount": "5000.00",
  "created_at": "2025-08-02T19:16:45.123456+00:00"
}

Response (Not Found):
{
  "detail": "Booking not found for this cart"
}

LOGIC: 
- If booking exists → Show success page
- If booking not found → Check payment status (next step)
"""

"""
4.2 CHECK PAYMENT STATUS (If booking not found)
-----------------------------------------------
GET /api/payments/cart/status/{cart_id}/
Authorization: Bearer {access_token}

Example:
GET /api/payments/cart/status/d7a594ac-9333-4213-985f-67942a3b638b/

Response:
{
  "success": true,
  "payment_status": "SUCCESS",     // or "INITIATED", "PENDING", "FAILED"
  "merchant_order_id": "CART_d7a594ac-9333-4213-985f-67942a3b638b_260E14E5",
  "amount": 500000,
  "cart_id": "d7a594ac-9333-4213-985f-67942a3b638b"
}

LOGIC:
- If payment_status = "SUCCESS" but no booking → System will auto-create via webhook
- If payment_status = "INITIATED" → Payment still processing
- If payment_status = "FAILED" → Show payment failed page
"""

# =============================================================================
# STEP 5: GET LATEST BOOKING (For dashboard/profile)
# =============================================================================
"""
5.1 GET USER'S LATEST BOOKING
-----------------------------
GET /api/booking/bookings/latest/
Authorization: Bearer {access_token}

Response:
{
  "id": 45,
  "book_id": "BK-103AE4E3",
  "status": "CONFIRMED",
  "total_amount": "5000.00",
  "created_at": "2025-08-02T19:16:45.123456+00:00",
  // ... full booking details
}
"""

"""
5.2 GET SPECIFIC BOOKING BY ID
------------------------------
GET /api/booking/bookings/by-id/{book_id}/
Authorization: Bearer {access_token}

Example:
GET /api/booking/bookings/by-id/BK-103AE4E3/

Response: Same as booking details above
"""

# =============================================================================
# STEP 6: CART CLEANUP (Automatic - No frontend action needed)
# =============================================================================
"""
6.1 AUTOMATIC CONVERTED CART CLEANUP
------------------------------------
POST /api/cart/carts/clear_converted/
Authorization: Bearer {access_token}

This is called AUTOMATICALLY by the system after booking creation.
Frontend doesn't need to call this manually.

The system automatically:
- Keeps the 3 most recent CONVERTED carts per user
- Deletes older converted carts to prevent database bloat
- Maintains referential integrity with bookings

Response:
{
  "success": true,
  "message": "Old converted carts cleaned successfully", 
  "carts_deleted": 2,
  "carts_kept": 3
}
"""

# =============================================================================
# COMPLETE FRONTEND FLOW SUMMARY
# =============================================================================
"""
FRONTEND IMPLEMENTATION CHECKLIST:
==================================

1. LOGIN FLOW:
   → POST /api/auth/login/
   → Store access token

2. ADD TO CART:
   → POST /api/cart/carts/
   → Store cart_id from response

3. INITIATE PAYMENT:
   → POST /api/payments/cart/ (with cart_id)
   → Redirect user to phonepe_payment_url

4. AFTER PHONEPE REDIRECT:
   → Parse cart_id from URL parameters
   → GET /api/booking/bookings/by-cart/{cart_id}/
   → If booking found: Show success page
   → If not found: GET /api/payments/cart/status/{cart_id}/
   → Based on payment status: Show appropriate message

5. DASHBOARD/PROFILE:
   → GET /api/booking/bookings/latest/
   → GET /api/booking/bookings/by-id/{book_id}/

6. CLEANUP:
   → Happens automatically, no frontend action needed

ERROR HANDLING:
- Always check response status codes
- Handle authentication errors (401) by redirecting to login
- Handle network errors gracefully
- Show appropriate loading states during API calls
"""

# =============================================================================
# WEBHOOK FLOW (Backend Only - For Understanding)
# =============================================================================
"""
WEBHOOK PROCESS (Automatic):
============================

1. User completes payment on PhonePe
2. PhonePe sends webhook to: POST /api/payments/webhook/phonepe/
3. System automatically:
   - Updates payment status to SUCCESS
   - Changes cart status to CONVERTED  
   - Creates booking with auto-generated book_id
   - Sends email notifications (user + admin)
   - Triggers cart cleanup

This all happens in the background. Frontend just needs to check for booking existence.
"""

print("API Endpoints Reference Document Created!")
print("Use this as your complete integration guide.")
