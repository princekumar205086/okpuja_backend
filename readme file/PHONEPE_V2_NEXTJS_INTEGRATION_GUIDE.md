# PhonePe V2 Payment Gateway Integration Guide for Next.js 15

## 📋 Overview

This guide provides complete integration steps for PhonePe V2 payment gateway with your Next.js 15 frontend and Django backend.

**Payment Flow:**
```
Add to Cart → Checkout → Payment → Success/Failure
                           ↓
                    Status = Success → Auto Booking → Cart Clear
                    Status ≠ Success → Cart Retain (Payment Pending)
```

## 🏗️ Architecture Overview

```
Next.js Frontend ↔ Django Backend ↔ PhonePe V2 API
      ↓                    ↓              ↓
   Payment UI         Payment Service   Gateway
      ↓                    ↓              ↓
   Callback           Webhook Handler   Status Updates
```

---

## 🔧 Backend Setup (Already Implemented)

### Django Endpoints Available:

1. **Payment Creation**: `POST /api/payment/payments/`
2. **Payment Status**: `GET /api/payment/payments/{id}/status/`
3. **Payment Webhook**: `POST /api/payment/webhook/phonepe/v2/`
4. **Refund**: `POST /api/payment/payments/{id}/refund/`

---

## 🌐 Frontend Integration (Next.js 15)

### 1. Install Dependencies

using pnpm in needed
```

### 2. Environment Configuration

Create `.env.local` in your Next.js project:

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000

# PhonePe Configuration
NEXT_PUBLIC_PHONEPE_ENVIRONMENT=sandbox
NEXT_PUBLIC_PAYMENT_SUCCESS_URL=http://localhost:3000/payment/success
NEXT_PUBLIC_PAYMENT_FAILURE_URL=http://localhost:3000/payment/failure
```

### 3. Axios Configuration
 
 all in globalApiconfig.ts



## 🔄 Payment Flow Implementation with Zustand

### Complete Flow Steps:

1. **Add to Cart** → Items stored in Zustand store (persisted in localStorage)
2. **Checkout Page** → Display cart from Zustand store
3. **Payment Initiation** → Zustand calls Django API to create payment record
4. **PhonePe Redirect** → User redirected to PhonePe payment page
5. **Payment Completion** → PhonePe redirects to success/failure page
6. **Status Verification** → Zustand store verifies payment with backend
7. **Booking Creation** → Backend automatically creates booking on success
8. **Cart Management** → Zustand clears cart on success, retains on failure

### Status Handling with Zustand:

```typescrpit
// Payment status handling in success page
const PaymentSuccessLogic = () => {
  const { checkPaymentStatus, currentPayment } = usePaymentStore();
  const { clearCart } = useCartStore();

  const handlePaymentReturn = async (paymentId) => {
    const status = await checkPaymentStatus(paymentId);
    
    switch (status.status) {
      case 'COMPLETED':
        // Payment successful - clear cart
        clearCart();
        // Booking automatically created by backend
        break;
        
      case 'FAILED':
        // Payment failed - cart retained in store
        // User can retry payment
        break;
        
      case 'PENDING':
        // Payment pending - keep monitoring
        break;
        
      default:
        // Unknown status
        console.error('Unknown payment status:', status.status);
    }
  };
};
```


## 🔐 Security Considerations

1. **Never store sensitive data** in localStorage
2. **Validate all payment responses** on the backend
3. **Use HTTPS** in production
4. **Implement CSRF protection** for API calls
5. **Add rate limiting** for payment attempts

---

## 🧪 Testing

### Test Payment Flow:

// Test with PhonePe test credentials
const testPayment = {
  cart_id: 'test-cart-123',
  amount: 100.00,
  payment_method: 'PHONEPE'
};

// Use sandbox environment for testing
NEXT_PUBLIC_PHONEPE_ENVIRONMENT=sandbox
```

---

## 📱 Mobile Responsiveness

All components are built with Tailwind CSS and are mobile-responsive. The payment flow works seamlessly on mobile devices with PhonePe app integration.

---

## 🚀 Production Checklist

- [ ] Update environment variables for production
- [ ] Configure production PhonePe credentials
- [ ] Set up proper CORS settings
- [ ] Add error tracking (Sentry, etc.)
- [ ] Configure webhook URLs
- [ ] Test payment flow end-to-end
- [ ] Set up monitoring and alerts

---

## 📞 Support

For issues with this integration:
1. Check browser console for errors
2. Verify API endpoints are accessible
3. Confirm PhonePe credentials are correct
4. Test webhook connectivity

This integration provides a complete, production-ready payment system with your specified flow: **Cart → Checkout → Payment → Booking (success) / Cart Retain (failure)**.
