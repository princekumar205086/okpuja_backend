# PhonePe Smart Redirect System - Complete Guide

## 🎯 **Problem Solved: Success/Failure Redirect Handling**

PhonePe V2 API limitation: Only **ONE redirect URL** per payment.
**Solution**: Smart redirect handler that checks payment status and redirects accordingly.

## 🔧 **New Smart Redirect System**

### **How It Works:**
1. **Single Redirect**: PhonePe redirects to `/api/payments/redirect/`
2. **Status Check**: Handler checks actual payment status
3. **Smart Redirect**: Redirects to success/failure page based on status

### **Updated Environment Variables:**
```env
# PhonePe URLs (Smart redirect system)
PHONEPE_CALLBACK_URL=http://localhost:8000/api/payments/webhook/phonepe/        # Webhook (unchanged)
PHONEPE_SMART_REDIRECT_URL=http://localhost:8000/api/payments/redirect/         # Smart handler (NEW)
PHONEPE_SUCCESS_REDIRECT_URL=http://localhost:3000/confirmbooking              # Success page
PHONEPE_FAILED_REDIRECT_URL=http://localhost:3000/failedbooking                # Failure page
```

## ✅ **Correct API Usage Now**

### **For Payment Creation:**
```json
{
  "amount": 500,
  "redirect_url": "http://localhost:8000/api/payments/redirect/"
}
```

### **What Happens After Payment:**

```
1. Customer completes payment on PhonePe
2. PhonePe redirects to: http://localhost:8000/api/payments/redirect/?merchantOrderId=OKPUJA_XXX
3. Smart handler checks payment status
4. If SUCCESS → redirects to: http://localhost:3000/confirmbooking?order_id=OKPUJA_XXX
5. If FAILED → redirects to: http://localhost:3000/failedbooking?order_id=OKPUJA_XXX&reason=failed
6. If PENDING → redirects to: http://localhost:3000/payment/pending?order_id=OKPUJA_XXX
```

## 🎯 **Available Redirect Options**

### **Option 1: Use Smart Redirect (Recommended)**
```json
{
  "amount": 500,
  "redirect_url": "http://localhost:8000/api/payments/redirect/"
}
```
✅ **Pros**: Automatic success/failure handling
✅ **Uses your ENV variables**: `PHONEPE_SUCCESS_REDIRECT_URL` and `PHONEPE_FAILED_REDIRECT_URL`

### **Option 2: Use Direct Frontend Page**
```json
{
  "amount": 500,
  "redirect_url": "http://localhost:3000/payment/result"
}
```
✅ **Pros**: Direct to frontend
❌ **Cons**: Frontend must check payment status

### **Option 3: Use Environment Variable**
```python
# In your view/service, you can use:
redirect_url = settings.PHONEPE_SMART_REDIRECT_URL  # From ENV
```

## 🛠️ **Frontend Pages You Need**

### **Success Page**: `/confirmbooking`
```javascript
// pages/confirmbooking.js or app/confirmbooking/page.js
export default function ConfirmBooking() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get('order_id');
  const transactionId = searchParams.get('transaction_id');
  
  return (
    <div className="success-page">
      <h1>Booking Confirmed! 🎉</h1>
      <p>Order ID: {orderId}</p>
      <p>Transaction ID: {transactionId}</p>
      {/* Your success UI */}
    </div>
  );
}
```

### **Failure Page**: `/failedbooking`
```javascript
// pages/failedbooking.js or app/failedbooking/page.js
export default function FailedBooking() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get('order_id');
  const reason = searchParams.get('reason');
  
  return (
    <div className="failure-page">
      <h1>Booking Failed ❌</h1>
      <p>Order ID: {orderId}</p>
      <p>Reason: {reason}</p>
      {/* Your failure UI with retry option */}
    </div>
  );
}
```

### **Pending Page**: `/payment/pending` (Optional)
```javascript
export default function PaymentPending() {
  return (
    <div className="pending-page">
      <h1>Payment Processing... ⏳</h1>
      <p>Please wait while we confirm your payment.</p>
    </div>
  );
}
```

## 🔄 **Testing Examples**

### **Test with Smart Redirect:**
```bash
POST /api/payments/create/
{
  "amount": 500,
  "redirect_url": "http://localhost:8000/api/payments/redirect/"
}
```

### **Test with Direct Frontend:**
```bash
POST /api/payments/create/
{
  "amount": 500,
  "redirect_url": "http://localhost:3000/payment/result"
}
```

### **Test with Generic Payment Page:**
```bash
POST /api/payments/create/
{
  "amount": 500,
  "redirect_url": "http://localhost:3000/payment/success"
}
```

## 📋 **Environment Variables Explanation**

| Variable | Purpose | Example |
|----------|---------|---------|
| `PHONEPE_CALLBACK_URL` | Webhook for server notifications | `http://localhost:8000/api/payments/webhook/phonepe/` |
| `PHONEPE_SMART_REDIRECT_URL` | Smart redirect handler | `http://localhost:8000/api/payments/redirect/` |
| `PHONEPE_SUCCESS_REDIRECT_URL` | Success page in frontend | `http://localhost:3000/confirmbooking` |
| `PHONEPE_FAILED_REDIRECT_URL` | Failure page in frontend | `http://localhost:3000/failedbooking` |

## 🚀 **Recommended Usage**

**For Development:**
```json
{
  "amount": 500,
  "redirect_url": "http://localhost:8000/api/payments/redirect/"
}
```

**For Production:**
```json
{
  "amount": 500,
  "redirect_url": "https://api.okpuja.com/api/payments/redirect/"
}
```

This gives you **automatic success/failure handling** while respecting PhonePe's single redirect URL limitation! 🎯
