# Payment URL Configuration Fix

## Issue
The payment creation endpoint was failing with the error:
```
"Payment initiation failed: 'Settings' object has no attribute 'FRONTEND_URL'"
```

## Root Cause
The `PaymentService` in `payment/services.py` was trying to access `settings.FRONTEND_URL` and `settings.BACKEND_URL`, but these settings were not defined in the Django settings file.

## Solution
Added the missing URL settings to `okpuja_backend/settings.py`:

```python
# URL settings for PaymentService
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')
```

## Environment Variables (Optional)
You can set these in your `.env` file for different environments:

```env
# Development
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://127.0.0.1:8000

# Production
FRONTEND_URL=https://okpuja.com
BACKEND_URL=https://api.okpuja.com
```

## Usage in Payment Flow
These URLs are used for:
- `FRONTEND_URL`: User redirect after payment completion
- `BACKEND_URL`: PhonePe webhook callbacks

## Testing
The payment creation endpoint should now work correctly:

```bash
curl -X POST http://127.0.0.1:8000/api/payments/payments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"cart_id": CART_ID}'
```

## Status
✅ **FIXED** - Payment creation now works without URL configuration errors.
