# PhonePe V2 Next.js 15 Quick Start Guide (Axios + Zustand)

## 🚀 Quick Implementation Steps

### 1. Install Dependencies

```bash
npm install axios zustand
npm install lucide-react
# If using shadcn/ui components
npx shadcn-ui@latest add button card
```

### 2. Create Axios Configuration

**File:** `lib/axios.js`

```javascript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error.response?.data || error)
);

export { apiClient };
```

### 3. Create Payment Store

**File:** `store/paymentStore.js`

```javascript
import { create } from 'zustand';
import { apiClient } from '@/lib/axios';

export const usePaymentStore = create((set) => ({
  loading: false,
  error: null,
  currentPayment: null,

  initiatePayment: async (cartId) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post('/payment/payments/', {
        cart_id: cartId,
        payment_method: 'PHONEPE'
      });
      
      if (response.success && response.payment_url) {
        set({ currentPayment: response, loading: false });
        window.location.href = response.payment_url;
      }
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  checkPaymentStatus: async (paymentId) => {
    try {
      const response = await apiClient.get(`/payment/payments/${paymentId}/status/`);
      set({ currentPayment: response });
      return response;
    } catch (error) {
      set({ error: error.message });
      throw error;
    }
  },
}));
```

### 4. Create Cart Store

**File:** `store/cartStore.js`

```javascript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],
      total: 0,

      addToCart: (item) => {
        const currentItems = get().items;
        const existingIndex = currentItems.findIndex(i => i.id === item.id);
        
        let newItems;
        if (existingIndex >= 0) {
          newItems = currentItems.map((i, index) =>
            index === existingIndex ? { ...i, quantity: i.quantity + 1 } : i
          );
        } else {
          newItems = [...currentItems, { ...item, quantity: 1 }];
        }

        const newTotal = newItems.reduce((sum, i) => sum + (i.price * i.quantity), 0);
        set({ items: newItems, total: newTotal });
      },

      removeFromCart: (itemId) => {
        const newItems = get().items.filter(i => i.id !== itemId);
        const newTotal = newItems.reduce((sum, i) => sum + (i.price * i.quantity), 0);
        set({ items: newItems, total: newTotal });
      },

      clearCart: () => set({ items: [], total: 0 }),
    }),
    { name: 'cart-storage' }
  )
);
```

### 5. Payment Button Component

**File:** `components/PaymentButton.jsx`

```jsx
'use client';
import { usePaymentStore } from '@/store/paymentStore';

export default function PaymentButton({ cartId, amount, onSuccess, onError }) {
  const { loading, error, initiatePayment } = usePaymentStore();

  const handlePayment = async () => {
    try {
      await initiatePayment(cartId);
      onSuccess?.();
    } catch (error) {
      onError?.(error.message);
    }
  };

  return (
    <div>
      <button 
        onClick={handlePayment}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Processing...' : `Pay ₹${amount}`}
      </button>
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </div>
  );
}
```

### 6. Success Page

**File:** `app/payment/success/page.jsx`

```jsx
'use client';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { usePaymentStore } from '@/store/paymentStore';
import { useCartStore } from '@/store/cartStore';

export default function PaymentSuccess() {
  const searchParams = useSearchParams();
  const { checkPaymentStatus, currentPayment } = usePaymentStore();
  const { clearCart } = useCartStore();
  const [status, setStatus] = useState('verifying');
  
  useEffect(() => {
    const verifyPayment = async () => {
      const paymentId = searchParams.get('payment_id');
      if (paymentId) {
        try {
          const result = await checkPaymentStatus(paymentId);
          if (result.status === 'COMPLETED') {
            clearCart(); // Clear cart on success
            setStatus('success');
          } else {
            setStatus('failed');
          }
        } catch (error) {
          setStatus('error');
        }
      }
    };
    verifyPayment();
  }, [searchParams, checkPaymentStatus, clearCart]);

  if (status === 'verifying') {
    return <div className="text-center py-20">Verifying payment...</div>;
  }

  return (
    <div className="text-center py-20">
      {status === 'success' ? (
        <div>
          <h1 className="text-3xl font-bold text-green-600 mb-4">Payment Successful!</h1>
          <p>Your booking has been confirmed.</p>
          {currentPayment && (
            <p className="text-sm text-gray-600 mt-2">
              Transaction ID: {currentPayment.merchant_transaction_id}
            </p>
          )}
        </div>
      ) : (
        <div>
          <h1 className="text-3xl font-bold text-red-600 mb-4">Payment Failed</h1>
          <p>Please try again.</p>
        </div>
      )}
    </div>
  );
}
```

### 7. Failure Page

**File:** `app/payment/failure/page.jsx`

```jsx
'use client';
export default function PaymentFailure() {
  return (
    <div className="text-center py-20">
      <h1 className="text-3xl font-bold text-red-600 mb-4">Payment Failed</h1>
      <p className="mb-6">Your cart items are still saved. Please try again.</p>
      <button 
        onClick={() => window.location.href = '/checkout'}
        className="bg-blue-600 text-white px-6 py-2 rounded-lg"
      >
        Retry Payment
      </button>
    </div>
  );
}
```

---

## 🔄 Integration in Your Existing Flow

### Step 1: Update Your Cart Component

```jsx
// In your cart/checkout component
import { useCartStore } from '@/store/cartStore';
import { usePaymentStore } from '@/store/paymentStore';

export default function Cart() {
  const { items, total, clearCart } = useCartStore();
  const { loading, error, initiatePayment } = usePaymentStore();

  const handlePayment = async () => {
    try {
      await initiatePayment('cart-id-from-backend');
    } catch (err) {
      alert(`Payment failed: ${err.message}`);
    }
  };

  return (
    <div>
      {/* Your existing cart items */}
      <div className="mt-6">
        <button 
          onClick={handlePayment}
          disabled={loading || !items.length}
          className="w-full bg-blue-600 text-white py-3 rounded-lg"
        >
          {loading ? 'Processing...' : `Pay ₹${total}`}
        </button>
        {error && <p className="text-red-500 mt-2">{error}</p>}
      </div>
    </div>
  );
}
```

### Step 2: Add to Cart Example

```jsx
// In your product component
import { useCartStore } from '@/store/cartStore';

export default function Product({ product }) {
  const { addToCart } = useCartStore();
  
  const handleAddToCart = () => {
    addToCart({
      id: product.id,
      name: product.name,
      price: product.price,
    });
  };

  return (
    <div>
      <h3>{product.name}</h3>
      <p>₹{product.price}</p>
      <button onClick={handleAddToCart}>Add to Cart</button>
    </div>
  );
}
```

### Step 2: Update Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_PAYMENT_SUCCESS_URL=http://localhost:3000/payment/success
NEXT_PUBLIC_PAYMENT_FAILURE_URL=http://localhost:3000/payment/failure
```

### Step 3: Update Your Django Settings

```python
# settings.py - Add these URLs
PHONEPE_SUCCESS_REDIRECT_URL = "http://localhost:3000/payment/success"
PHONEPE_FAILURE_REDIRECT_URL = "http://localhost:3000/payment/failure"
PHONEPE_WEBHOOK_URL = "http://localhost:8000/api/payment/webhook/phonepe/v2/"

# CORS settings for frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

---

## 🎯 Your Exact Flow Implementation with Zustand

```javascript
// Complete flow handler with Zustand
class OkPujaPaymentFlow {
  async processPayment() {
    // 1. Items already in Zustand cart store (persistent)
    const { items, total } = useCartStore.getState();
    
    // 2. Create payment via Zustand payment store
    const { initiatePayment } = usePaymentStore.getState();
    await initiatePayment('cart-id');
    
    // 3. User redirected to PhonePe automatically
    // 4. PhonePe redirects back to success/failure page
    // 5. Success page verifies payment and clears cart via Zustand
    // 6. Backend auto-creates booking if payment successful
    // 7. Cart cleared on success, retained on failure (via Zustand persistence)
  }
}
```

### Zustand Store Benefits:

✅ **Persistent State** - Cart survives page refreshes  
✅ **Global Access** - Access cart/payment from any component  
✅ **Type Safety** - Better TypeScript support  
✅ **Performance** - No unnecessary re-renders  
✅ **DevTools** - Built-in debugging support

---

## 📱 Testing Your Integration

### Test Payment Flow:

1. **Add items to cart**
2. **Go to checkout** 
3. **Click Pay button** → Should redirect to PhonePe
4. **Complete test payment** on PhonePe
5. **Return to your app** → Should show success/failure
6. **Check database** → Booking should be created on success

### Test URLs (Sandbox):
- PhonePe will redirect to your success/failure URLs
- Use test card: `4111 1111 1111 1111`
- CVV: `123`, Any future date

---

## 🚨 Common Issues & Solutions

### Issue 1: CORS Errors
```python
# Add to Django settings.py
CORS_ALLOW_ALL_ORIGINS = True  # Only for development
```

### Issue 2: Payment URL Not Working
```javascript
// Check if URL is properly formed
console.log('Payment URL:', result.payment_url);
// Should start with https://phoenixuat.phonepe.com
```

### Issue 3: Callback Not Working
```javascript
// Ensure your callback URLs are accessible
// Test: curl http://localhost:3000/payment/success
```

---

## 🎉 Final Integration Checklist

- [ ] ✅ Payment service created
- [ ] ✅ Payment button component added
- [ ] ✅ Success/failure pages created
- [ ] ✅ Environment variables configured
- [ ] ✅ Django CORS settings updated
- [ ] ✅ Test payment flow end-to-end
- [ ] ✅ Verify booking creation on success
- [ ] ✅ Verify cart retention on failure

**Your payment gateway is now ready! 🚀**

The flow will work exactly as you specified:
`Add to Cart → Checkout → Payment → Success (Booking + Clear Cart) / Failure (Retain Cart)`
