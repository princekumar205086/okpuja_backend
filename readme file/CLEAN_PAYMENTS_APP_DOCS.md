# Clean Payments App Documentation

## 🎯 Overview

This is a completely clean and optimized payments app for PhonePe integration, built with Django REST Framework. It follows clean architecture principles and is based on the official PhonePe Postman documentation.

## 🏗️ Architecture

### Apps Structure
```
payments/                    # New clean payments app
├── models.py               # Clean payment models
├── serializers.py          # DRF serializers
├── views.py               # Clean API views
├── services.py            # Business logic layer
├── phonepe_client.py      # PhonePe API client
├── urls.py                # URL patterns
└── admin.py               # Django admin

tests/                      # All test scripts organized here
├── test_clean_payments_app.py
└── ... (other test scripts)
```

### Clean Separation of Concerns
- **Models**: Database schema and basic model methods
- **Serializers**: API input/output validation
- **Views**: HTTP request/response handling
- **Services**: Business logic and PhonePe integration
- **Client**: Low-level PhonePe API communication

## 📊 Database Models

### PaymentOrder
```python
- id (UUID)
- merchant_order_id (unique)
- user (ForeignKey)
- amount (in paisa)
- status (PENDING, INITIATED, SUCCESS, FAILED, etc.)
- phonepe_payment_url
- phonepe_transaction_id
- redirect_url
- metadata (JSON)
- timestamps
```

### PaymentRefund
```python
- id (UUID)
- merchant_refund_id (unique)
- payment_order (ForeignKey)
- amount (in paisa)
- status (PENDING, PROCESSING, SUCCESS, FAILED)
- reason
- phonepe_response (JSON)
- timestamps
```

### PaymentWebhook
```python
- id (UUID)
- event_type
- merchant_order_id
- raw_data (JSON)
- processed (boolean)
- timestamps
```

## 🔌 API Endpoints

### Base URL: `/api/pay/`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/create/` | POST | Create payment order |
| `/list/` | GET | List user's payments |
| `/status/<order_id>/` | GET | Check payment status |
| `/refund/<order_id>/` | POST | Create refund |
| `/refund/status/<refund_id>/` | GET | Check refund status |
| `/webhook/phonepe/` | POST | PhonePe webhook handler |
| `/health/` | GET | Service health check |
| `/test/` | POST | Quick payment test |

## 🚀 Usage Examples

### 1. Create Payment Order

```bash
POST /api/pay/create/
Authorization: Bearer <token>
Content-Type: application/json

{
    "amount": 10000,
    "redirect_url": "https://okpuja.com/payment/success",
    "description": "Payment for puja booking",
    "metadata": {
        "booking_id": "123",
        "puja_type": "ganesh_puja"
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "Payment order created successfully",
    "data": {
        "payment_order": {
            "id": "uuid",
            "merchant_order_id": "OKPUJA_ABC123",
            "amount": 10000,
            "amount_in_rupees": 100.0,
            "status": "INITIATED",
            "phonepe_payment_url": "https://mercury-uat.phonepe.com/...",
            "created_at": "2025-07-31T10:30:00Z"
        },
        "payment_url": "https://mercury-uat.phonepe.com/...",
        "merchant_order_id": "OKPUJA_ABC123"
    }
}
```

### 2. Check Payment Status

```bash
GET /api/pay/status/OKPUJA_ABC123/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "merchant_order_id": "OKPUJA_ABC123",
        "status": "SUCCESS",
        "amount": 10000,
        "amount_in_rupees": 100.0,
        "payment_method": "UPI",
        "phonepe_transaction_id": "TXN123456",
        "completed_at": "2025-07-31T10:35:00Z"
    }
}
```

### 3. Create Refund

```bash
POST /api/pay/refund/OKPUJA_ABC123/
Authorization: Bearer <token>
Content-Type: application/json

{
    "amount": 5000,
    "reason": "Partial refund requested by customer"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Refund created successfully",
    "data": {
        "merchant_refund_id": "REFUND_XYZ789",
        "amount": 5000,
        "amount_in_rupees": 50.0,
        "status": "PROCESSING",
        "created_at": "2025-07-31T11:00:00Z"
    }
}
```

## 🔧 Frontend Integration

### Next.js + Axios Example

```javascript
// Create payment
const createPayment = async (paymentData) => {
    try {
        const response = await axios.post('/api/pay/create/', paymentData, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.data.success) {
            // Redirect to payment URL or open in iframe
            const paymentUrl = response.data.data.payment_url;
            window.location.href = paymentUrl;
        }
    } catch (error) {
        console.error('Payment creation failed:', error);
    }
};

// Check payment status
const checkPaymentStatus = async (merchantOrderId) => {
    try {
        const response = await axios.get(`/api/pay/status/${merchantOrderId}/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        return response.data;
    } catch (error) {
        console.error('Status check failed:', error);
    }
};
```

### PhonePe Iframe Integration

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://mercury.phonepe.com/web/bundle/checkout.js"></script>
</head>
<body>
    <button id="payButton">Pay Now</button>
    
    <script>
        document.getElementById('payButton').addEventListener('click', function() {
            // Get payment URL from your API
            const tokenUrl = 'PAYMENT_URL_FROM_API';
            
            function paymentCallback(response) {
                if (response === 'USER_CANCEL') {
                    alert('Payment cancelled');
                } else if (response === 'CONCLUDED') {
                    // Check payment status with your API
                    checkPaymentStatus(merchantOrderId);
                }
            }
            
            window.PhonePeCheckout.transact({
                tokenUrl: tokenUrl,
                callback: paymentCallback,
                type: 'IFRAME'
            });
        });
    </script>
</body>
</html>
```

## ⚙️ Configuration

### Django Settings

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'payments',  # New clean payments app
]

# PhonePe Configuration (already exists)
PHONEPE_ENV = 'UAT'  # or 'PRODUCTION'
PHONEPE_CLIENT_ID = 'your_client_id'
PHONEPE_CLIENT_SECRET = 'your_client_secret'
PHONEPE_MERCHANT_ID = 'your_merchant_id'

# Add to URLs
# In main urls.py
urlpatterns = [
    # ... other patterns
    path('api/pay/', include('payments.urls')),
]
```

## 🧪 Testing

### Run Tests

```bash
# Test the new payments app
python tests/test_clean_payments_app.py

# Run Django tests
python manage.py test payments
```

### API Testing with curl

```bash
# Health check
curl -X GET http://localhost:8000/api/pay/health/ \
  -H "Authorization: Bearer <token>"

# Create payment
curl -X POST http://localhost:8000/api/pay/create/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10000,
    "redirect_url": "https://okpuja.com/success",
    "description": "Test payment"
  }'
```

## 🔒 Security Features

- **JWT Authentication**: All endpoints require authentication
- **User Isolation**: Users can only access their own payments
- **Input Validation**: All inputs validated via DRF serializers
- **CSRF Protection**: Webhook endpoints properly configured
- **Error Handling**: Comprehensive error responses

## 📈 Benefits of Clean Architecture

1. **Maintainability**: Clear separation of concerns
2. **Testability**: Easy to unit test each component
3. **Scalability**: Easy to add new payment providers
4. **Readability**: Clean, well-documented code
5. **Reusability**: Service layer can be used in different contexts

## 🚀 Next Steps

1. **Add to INSTALLED_APPS** ✅ (Done)
2. **Run Migrations** ✅ (Done)
3. **Include URLs** ✅ (Done)
4. **Test APIs** with Postman/frontend
5. **Configure Webhooks** for production
6. **Add Monitoring** and logging
7. **Performance Optimization** if needed

## 🔧 Migration from Old Payment App

The new `payments` app runs alongside the old `payment` app:
- Old: `/api/payments/` (legacy)
- New: `/api/pay/` (clean)

You can gradually migrate endpoints and eventually remove the old app.

## 📞 Support

For any issues or questions:
1. Check the test scripts in `/tests/`
2. Review the service layer in `payments/services.py`
3. Examine the PhonePe client in `payments/phonepe_client.py`
4. Check Django admin for payment records

The new payments app is production-ready and follows Django best practices!
