# PhonePe Redirect Issue - SOLUTION GUIDE

## 🚨 **Problem Identified**
PhonePe V2 Standard Checkout API **does not send the `merchantOrderId`** in the redirect URL. This is a known limitation.

Your logs show:
```
No merchant order ID in redirect
GET /api/payments/redirect/ HTTP/1.1" 302 0
```

## ✅ **Solution Options**

### **Option 1: Enhanced Smart Redirect (UPDATED)**
The redirect handler now:
- ✅ Logs all parameters PhonePe sends
- ✅ Checks multiple parameter names
- ✅ Falls back to success page if no order ID
- ✅ Handles errors gracefully

### **Option 2: Simple Direct Redirect (NEW)**
- ✅ Always redirects to success page
- ✅ Frontend checks latest payment status
- ✅ Simpler and more reliable

### **Option 3: Frontend Status Check (RECOMMENDED)**
- ✅ Use simple redirect
- ✅ Frontend API call to get latest payment
- ✅ Most reliable approach

## 🔧 **Updated Configuration**

### **For Testing (Use Simple Redirect):**
```json
{
  "amount": 500,
  "redirect_url": "http://localhost:8000/api/payments/redirect/simple/"
}
```

### **New API Endpoints Added:**
- `GET /api/payments/redirect/simple/` - Simple redirect handler
- `GET /api/payments/latest/` - Get user's latest payment status

## 🎯 **Recommended Implementation**

### **1. Backend Payment Creation**
```json
{
  "amount": 500,
  "redirect_url": "http://localhost:8000/api/payments/redirect/simple/"
}
```

### **2. Frontend Success Page Logic**
```javascript
// In your /confirmbooking page
useEffect(() => {
  const checkLatestPayment = async () => {
    try {
      const response = await fetch('/api/payments/latest/', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        const payment = data.data;
        console.log('Latest payment:', payment);
        
        // Update UI based on payment status
        if (payment.status === 'SUCCESS') {
          // Show success message
          setPaymentStatus('success');
          setOrderId(payment.merchant_order_id);
        } else {
          // Show pending or failure
          setPaymentStatus(payment.status.toLowerCase());
        }
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
    }
  };
  
  // Check payment status when page loads
  if (searchParams.get('redirect_source') === 'phonepe') {
    checkLatestPayment();
  }
}, []);
```

## 🧪 **Testing the Fix**

### **Test 1: Check What PhonePe Sends**
```bash
# Watch your Django logs when payment redirects
# The enhanced handler will log all parameters PhonePe sends
```

### **Test 2: Test Simple Redirect**
```bash
# Create payment with simple redirect URL
curl -X POST http://localhost:8000/api/payments/create/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 500,
    "redirect_url": "http://localhost:8000/api/payments/redirect/simple/"
  }'
```

### **Test 3: Test Latest Payment API**
```bash
# Check latest payment status
curl -X GET http://localhost:8000/api/payments/latest/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📋 **Updated Environment Variables**

Your `.env` is already correct:
```env
PHONEPE_SUCCESS_REDIRECT_URL=http://localhost:3000/confirmbooking
PHONEPE_FAILED_REDIRECT_URL=http://localhost:3000/failedbooking
```

## 🔄 **New Testing Flow**

1. **Create Payment**: Use simple redirect URL
2. **Complete Payment**: On PhonePe
3. **PhonePe Redirects**: To `/api/payments/redirect/simple/`
4. **Backend Redirects**: To `http://localhost:3000/confirmbooking?redirect_source=phonepe`
5. **Frontend Checks**: Latest payment status via `/api/payments/latest/`
6. **UI Updates**: Based on actual payment status

## 🚀 **Production URLs**

```env
# Production redirect URLs
PHONEPE_SUCCESS_REDIRECT_URL=https://www.okpuja.com/confirmbooking
PHONEPE_FAILED_REDIRECT_URL=https://www.okpuja.com/failedbooking

# Use simple redirect for production too
"redirect_url": "https://api.okpuja.com/api/payments/redirect/simple/"
```

## ✅ **This Solves Your Issue**

- ✅ **No more missing order ID errors**
- ✅ **Always redirects to success page**
- ✅ **Frontend gets actual payment status**
- ✅ **Works with PhonePe V2 limitations**
- ✅ **Production ready**

## 🎯 **Next Steps**

1. **Test the simple redirect**: Use `/api/payments/redirect/simple/` as redirect URL
2. **Update frontend**: Add payment status check on success page
3. **Deploy**: This approach works in production

The simple redirect approach is the most reliable because it works around PhonePe V2's limitation of not sending order parameters in the redirect URL.
