# 🚀 Frontend Integration Guide: Address-Required Checkout Flow

## 📋 **Complete Flow Overview:**
```
Cart Creation (No Address) → Address Selection → Payment Initiation → Booking Creation
```

---

## 🔧 **Backend Changes Summary:**

### ✅ **What Changed:**
1. **Cart Model**: Removed `selected_address` field - Cart no longer stores address
2. **Payment Model**: Added `address_id` field - Payment stores selected address  
3. **Payment API**: Now requires `address_id` parameter during payment initiation
4. **Booking Creation**: Uses `address_id` from payment, not from cart

### ✅ **What Stayed Same:**
- All existing cart functionality
- Payment processing flow
- Booking models and fields
- User authentication
- All other APIs

---

## 🎯 **Frontend Integration Steps:**

### **Step 1: Update Cart Page**
```javascript
// ❌ OLD: Cart could proceed to payment directly
<button onClick={() => initiatePayment(cartId)}>
  Proceed to Payment
</button>

// ✅ NEW: Cart must proceed to address selection
<button onClick={() => navigateToAddressSelection(cartId)}>
  Proceed to Checkout
</button>
```

### **Step 2: Create Address Selection Page**
```javascript
// NEW PAGE: AddressSelection.jsx
import React, { useState, useEffect } from 'react';

const AddressSelection = ({ cartId }) => {
  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch user addresses
  useEffect(() => {
    fetchUserAddresses();
  }, []);

  const fetchUserAddresses = async () => {
    try {
      const response = await fetch('/api/accounts/addresses/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setAddresses(data);
      
      // Auto-select default address
      const defaultAddr = data.find(addr => addr.is_default);
      if (defaultAddr) setSelectedAddressId(defaultAddr.id);
    } catch (error) {
      console.error('Failed to fetch addresses:', error);
    }
  };

  const handlePaymentInitiation = async () => {
    if (!selectedAddressId) {
      alert('Please select an address');
      return;
    }

    setLoading(true);
    try {
      // ✅ NEW: Payment initiation requires address_id
      const response = await fetch('/api/payments/cart/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          cart_id: cartId,
          address_id: selectedAddressId  // ⭐ REQUIRED!
        })
      });

      const data = await response.json();
      if (data.success) {
        // Redirect to PhonePe payment
        window.location.href = data.payment_url;
      } else {
        alert(`Payment initiation failed: ${data.error}`);
      }
    } catch (error) {
      console.error('Payment initiation failed:', error);
      alert('Payment initiation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="address-selection">
      <h2>Select Delivery Address</h2>
      
      {/* Address List */}
      <div className="address-list">
        {addresses.map(address => (
          <div 
            key={address.id} 
            className={`address-card ${selectedAddressId === address.id ? 'selected' : ''}`}
            onClick={() => setSelectedAddressId(address.id)}
          >
            <input 
              type="radio" 
              checked={selectedAddressId === address.id}
              onChange={() => setSelectedAddressId(address.id)}
            />
            <div className="address-details">
              <h4>{address.address_line1}</h4>
              <p>{address.city}, {address.state} - {address.pincode}</p>
              {address.is_default && <span className="default-badge">Default</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Add New Address Button */}
      <button 
        className="add-address-btn"
        onClick={() => {/* Open add address modal */}}
      >
        + Add New Address
      </button>

      {/* Payment Button */}
      <button 
        className="payment-btn"
        onClick={handlePaymentInitiation}
        disabled={!selectedAddressId || loading}
      >
        {loading ? 'Processing...' : 'Proceed to Payment'}
      </button>
    </div>
  );
};

export default AddressSelection;
```

### **Step 3: Update Payment API Calls**
```javascript
// ❌ OLD Payment API Call
const initiatePayment = async (cartId) => {
  const response = await fetch('/api/payments/cart/', {
    method: 'POST',
    body: JSON.stringify({ cart_id: cartId })
  });
};

// ✅ NEW Payment API Call (with address_id)
const initiatePayment = async (cartId, addressId) => {
  const response = await fetch('/api/payments/cart/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      cart_id: cartId,
      address_id: addressId  // ⭐ NOW REQUIRED
    })
  });
};
```

### **Step 4: Update Routing**
```javascript
// App.js or Router configuration
import AddressSelection from './components/AddressSelection';

// ✅ NEW Route
<Route 
  path="/checkout/:cartId" 
  element={<AddressSelection />} 
/>

// Update cart page navigation
const navigateToCheckout = (cartId) => {
  navigate(`/checkout/${cartId}`);
};
```

---

## 📱 **Complete Frontend Flow:**

### **1. Cart Page (`/cart`)**
```javascript
const CartPage = () => {
  const handleCheckout = () => {
    // ✅ Navigate to address selection instead of direct payment
    navigate(`/checkout/${cartId}`);
  };

  return (
    <div>
      {/* Cart items */}
      <button onClick={handleCheckout}>
        Proceed to Checkout
      </button>
    </div>
  );
};
```

### **2. Address Selection Page (`/checkout/:cartId`)**
```javascript
const CheckoutPage = () => {
  const { cartId } = useParams();
  
  return <AddressSelection cartId={cartId} />;
};
```

### **3. Payment Success Page (`/confirmbooking`)**
```javascript
// ✅ No changes needed - booking will have address from payment
const PaymentSuccess = () => {
  const [booking, setBooking] = useState(null);
  
  useEffect(() => {
    // Fetch booking details - will include address
    fetchBookingDetails();
  }, []);

  return (
    <div>
      <h2>Booking Confirmed!</h2>
      {booking && (
        <div>
          <p>Booking ID: {booking.book_id}</p>
          <p>Service will be delivered to:</p>
          <p>{booking.address.address_line1}, {booking.address.city}</p>
        </div>
      )}
    </div>
  );
};
```

---

## 🔗 **API Endpoints Reference:**

### **1. Get User Addresses**
```javascript
GET /api/accounts/addresses/
Headers: Authorization: Bearer <token>
Response: [
  {
    "id": 5,
    "address_line1": "123 Test Street", 
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "is_default": true
  }
]
```

### **2. Create Payment (Updated)**
```javascript
POST /api/payments/cart/
Headers: Content-Type: application/json
Body: {
  "cart_id": 123,
  "address_id": 5  // ⭐ NOW REQUIRED
}
Response: {
  "success": true,
  "payment_url": "https://phonepe.com/pay/...",
  "payment_order_id": "abc123"
}
```

### **3. Payment Status Check**
```javascript
GET /api/payments/status/<payment_id>/
Response: {
  "status": "SUCCESS",
  "booking_id": 89,
  "address_id": 5
}
```

---

## 🎨 **UI/UX Recommendations:**

### **Address Selection Page Design:**
```css
.address-selection {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.address-card {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  margin: 10px 0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.address-card.selected {
  border-color: #007bff;
  background-color: #f8f9ff;
}

.default-badge {
  background: #28a745;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.payment-btn {
  width: 100%;
  padding: 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  margin-top: 20px;
}

.payment-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
```

---

## ⚠️ **Important Notes:**

1. **Mandatory Address**: Payment will fail if `address_id` is not provided
2. **Address Validation**: Backend validates that address belongs to the user
3. **Booking Address**: All bookings will now have proper delivery addresses
4. **Error Handling**: Handle address selection validation on frontend
5. **User Experience**: Guide users through the new checkout flow

---

## 🚀 **Migration Strategy:**

### **For Existing Users:**
1. **Gradual Rollout**: Deploy backend changes first
2. **Frontend Update**: Update frontend to use new flow
3. **Testing**: Test with existing carts and addresses
4. **User Communication**: Inform users about the new checkout process

### **Testing Checklist:**
- ✅ Cart creation (verify no address field)
- ✅ Address selection page loads
- ✅ Payment initiation with address_id
- ✅ Booking creation includes address
- ✅ Payment success page shows address
- ✅ Error handling for missing address

---

**🎉 Your frontend is now ready for the new address-required checkout flow!**
