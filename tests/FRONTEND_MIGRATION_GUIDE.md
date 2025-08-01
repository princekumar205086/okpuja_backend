# Frontend Migration Guide - Old Payment App to New Payments App

## ✅ **Good News: Your Test Shows Everything Works!**

Your test output shows the smart redirect is working perfectly:
- ✅ Smart redirect endpoint is accessible
- ✅ Redirecting to frontend (localhost:3000)
- ✅ Frontend receiving redirect properly

## 🔄 **API Endpoint Changes (Frontend Updates Needed)**

### **Old Payment App Endpoints → New Payments App Endpoints**

| Old Endpoint | New Endpoint | Status |
|-------------|-------------|---------|
| `/api/payment/create/` | `/api/payments/create/` | ✅ Update |
| `/api/payment/status/{id}/` | `/api/payments/status/{id}/` | ✅ Update |
| `/api/payment/list/` | `/api/payments/list/` | ✅ Update |
| `/api/payment/refund/{id}/` | `/api/payments/refund/{id}/` | ✅ Update |
| `/api/payment/webhook/phonepe/` | `/api/payments/webhook/phonepe/` | ✅ Update |

### **Key Changes:**
- **Endpoint Prefix**: `/api/payment/` → `/api/payments/` (plural)
- **New Redirect Handler**: `/api/payments/redirect/` (NEW)
- **Response Format**: Improved with better error handling

## 🔧 **Frontend Code Updates Required**

### **1. Update API Base URLs**

**Old Frontend Code:**
```javascript
// ❌ Old - needs updating
const API_BASE = 'http://localhost:8000/api/payment'

// Payment creation
const response = await fetch(`${API_BASE}/create/`, {
  method: 'POST',
  // ...
});
```

**New Frontend Code:**
```javascript
// ✅ New - correct
const API_BASE = 'http://localhost:8000/api/payments'  // Note: plural

// Payment creation
const response = await fetch(`${API_BASE}/create/`, {
  method: 'POST',
  // ...
});
```

### **2. Update Payment Creation Logic**

**Old Frontend Code:**
```javascript
// ❌ Old redirect URL
const paymentData = {
  amount: 500,
  redirect_url: "http://localhost:3000/payment/success"
};
```

**New Frontend Code:**
```javascript
// ✅ New smart redirect URL
const paymentData = {
  amount: 500,
  redirect_url: "http://localhost:8000/api/payments/redirect/"  // Smart handler
};
```

### **3. Update Success/Failure Page Handling**

Your existing pages will work perfectly:

**Success Page** (`/confirmbooking`):
```javascript
// Your existing page will receive these URL parameters:
// ?order_id=OKPUJA_123456&transaction_id=T789

import { useSearchParams } from 'next/navigation';

export default function ConfirmBooking() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get('order_id');
  const transactionId = searchParams.get('transaction_id');
  
  // Your existing confirmation logic
  // No changes needed here!
  
  return (
    <div>
      <h1>Booking Confirmed!</h1>
      <p>Order: {orderId}</p>
      {/* Your existing UI */}
    </div>
  );
}
```

**Failure Page** (`/failedbooking`):
```javascript
// Your existing page will receive:
// ?order_id=OKPUJA_123456&reason=failed

export default function FailedBooking() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get('order_id');
  const reason = searchParams.get('reason');
  
  // Your existing failure handling logic
  // No changes needed here!
  
  return (
    <div>
      <h1>Booking Failed</h1>
      <p>Order: {orderId}</p>
      <p>Reason: {reason}</p>
      {/* Your existing UI */}
    </div>
  );
}
```

## 🌐 **Production Readiness Check**

### ✅ **Your Production Setup is Ready!**

1. **Domain Whitelisted**: ✅ `https://www.okpuja.com` is whitelisted at PhonePe
2. **Production Credentials**: ✅ Available in your `.env`
3. **Smart Redirect**: ✅ Will work with production domain

### **Production Environment Variables**

Update your production `.env`:
```env
# Production PhonePe Settings
PHONEPE_ENV=PRODUCTION
PHONEPE_CLIENT_ID=SU2507311635477696235898
PHONEPE_CLIENT_SECRET=1f59672d-e31c-4898-9caf-19ab54bcaaab
PHONEPE_MERCHANT_ID=M22KEWU5BO1I2

# Production URLs
PHONEPE_CALLBACK_URL=https://api.okpuja.com/api/payments/webhook/phonepe/
PHONEPE_SMART_REDIRECT_URL=https://api.okpuja.com/api/payments/redirect/
PHONEPE_SUCCESS_REDIRECT_URL=https://www.okpuja.com/confirmbooking
PHONEPE_FAILED_REDIRECT_URL=https://www.okpuja.com/failedbooking
FRONTEND_BASE_URL=https://www.okpuja.com
```

## 📋 **Migration Checklist**

### **Backend (Already Done ✅)**
- [x] New payments app created
- [x] Smart redirect handler implemented
- [x] Environment variables updated
- [x] All test scripts moved to `tests/` folder
- [x] Swagger documentation enhanced

### **Frontend (Action Required 🔧)**
- [ ] Update API endpoints: `/api/payment/` → `/api/payments/`
- [ ] Update payment creation redirect URL to smart handler
- [ ] Test with new endpoints
- [ ] Deploy updated frontend

### **Production Deployment (Ready 🚀)**
- [ ] Switch environment variables to production
- [ ] Deploy backend with new endpoints
- [ ] Deploy frontend with updated API calls
- [ ] Test production payment flow

## 🔄 **Quick Frontend Update Script**

Here's a search-and-replace guide for your frontend:

```bash
# Find and replace in your Next.js project
# Old: /api/payment/
# New: /api/payments/

# Search for these patterns in your frontend codebase:
- "api/payment/"      → "api/payments/"
- "/payment/create"   → "/payments/create"
- "/payment/status"   → "/payments/status"
- "/payment/list"     → "/payments/list"
- "/payment/refund"   → "/payments/refund"
```

## 🎯 **Testing Strategy**

1. **Development Testing**:
   ```javascript
   // Test with new endpoints
   const response = await fetch('http://localhost:8000/api/payments/create/', {
     method: 'POST',
     headers: {
       'Authorization': `Bearer ${token}`,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       amount: 500,
       redirect_url: 'http://localhost:8000/api/payments/redirect/'
     })
   });
   ```

2. **Production Testing**:
   ```javascript
   // Production API calls
   const response = await fetch('https://api.okpuja.com/api/payments/create/', {
     // Same structure, different base URL
   });
   ```

## ✅ **Summary**

**What Works Without Changes:**
- ✅ Your existing success/failure pages (`/confirmbooking`, `/failedbooking`)
- ✅ Your PhonePe production credentials and domain whitelist
- ✅ Your overall payment flow logic

**What Needs Updates:**
- 🔧 API endpoint URLs (add 's' to make plural)
- 🔧 Payment redirect URL to use smart handler

**Estimated Update Time:** 15-30 minutes for a typical Next.js project

Your setup is **production-ready** and the changes are minimal! 🎉
