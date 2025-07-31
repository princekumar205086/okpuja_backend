# PhonePe Payment Gateway Integration Guide

## Overview
This guide covers the updated PhonePe payment gateway integration using the latest PhonePe SDK v2.1.4 for your Django backend.

## Configuration

### Environment Variables
Add these variables to your `.env` file:

```bash
# PhonePe Payment Gateway Configuration (Latest SDK)
# UAT/Test Environment
PHONEPE_ENV=UAT
PHONEPE_CLIENT_ID=TEST-M22KEWU5BO1I2_25070
PHONEPE_CLIENT_SECRET=MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh
PHONEPE_CLIENT_VERSION=1

# Production Environment (uncomment for production)
# PHONEPE_ENV=PRODUCTION
# PHONEPE_CLIENT_ID=your_production_client_id
# PHONEPE_CLIENT_SECRET=73e5f6e1-1da3-403e-8168-da15fdffbd7d
# PHONEPE_CLIENT_VERSION=1

# URLs for redirect and callback (Development)
PHONEPE_REDIRECT_URL=http://localhost:8000/api/payments/webhook/phonepe/
PHONEPE_CALLBACK_URL=http://localhost:8000/api/payments/webhook/phonepe/
PHONEPE_FAILED_REDIRECT_URL=http://localhost:3000/failedbooking
PHONEPE_SUCCESS_REDIRECT_URL=http://localhost:3000/confirmbooking/

# Frontend Base URL (Development)
FRONTEND_BASE_URL=http://localhost:3000

# Production URLs (uncomment for production deployment)
# PHONEPE_REDIRECT_URL=https://api.okpuja.com/api/payments/webhook/phonepe/
# PHONEPE_CALLBACK_URL=https://api.okpuja.com/api/payments/webhook/phonepe/
# PHONEPE_FAILED_REDIRECT_URL=https://www.okpuja.com/failedbooking
# PHONEPE_SUCCESS_REDIRECT_URL=https://www.okpuja.com/confirmbooking/
# FRONTEND_BASE_URL=https://www.okpuja.com

# Callback Authentication (configure these in PhonePe dashboard)
PHONEPE_CALLBACK_USERNAME=your_callback_username
PHONEPE_CALLBACK_PASSWORD=your_callback_password
```

### Installation

1. Install the PhonePe SDK:
```bash
pip install --index-url https://phonepe.mycloudrepo.io/public/repositories/phonepe-pg-sdk-python --extra-index-url https://pypi.org/simple phonepe_sdk
```

2. Run migrations:
```bash
python manage.py migrate
```

## API Endpoints

### 1. Create Payment
**POST** `/api/payments/payments/`

Request body:
```json
{
    "booking": 1,
    "amount": "100.00",
    "method": "PHONEPE",
    "redirect_url": "http://localhost:3000/confirmbooking/"
}
```

Response:
```json
{
    "success": true,
    "payment_id": 1,
    "merchant_transaction_id": "MT1234567890",
    "transaction_id": "TXN1234567890",
    "amount": "100.00",
    "currency": "INR",
    "payment_url": "https://checkout.phonepe.com/...",
    "status": "PENDING"
}
```

### 2. Check Payment Status
**GET** `/api/payments/payments/{id}/status/`

Response:
```json
{
    "success": true,
    "code": "STATUS_CHECKED",
    "message": "Payment status checked successfully",
    "transaction_id": "TXN1234567890",
    "merchant_transaction_id": "MT1234567890",
    "amount": "100.00",
    "currency": "INR",
    "status": "SUCCESS",
    "payment_method": "PHONEPE"
}
```

### 3. Webhook Endpoint
**POST** `/api/payments/webhook/phonepe/`

This endpoint receives callbacks from PhonePe when payment status changes.

## Payment Flow

1. **Frontend initiates payment**:
   - User selects items and proceeds to checkout
   - Frontend calls the create payment API
   - Backend creates payment record and returns PhonePe checkout URL

2. **User completes payment**:
   - User is redirected to PhonePe checkout page
   - User completes payment using preferred method
   - PhonePe processes the payment

3. **Payment completion**:
   - PhonePe sends webhook notification to your backend
   - Backend updates payment status
   - User is redirected to success/failure page

## PhonePe Dashboard Configuration

### UAT (Testing) Environment
1. Login to PhonePe Business Dashboard (UAT)
2. Go to Developer Settings > API Keys
3. Use the test credentials:
   - Client ID: `TEST-M22KEWU5BO1I2_25070`
   - Client Secret: `MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh`

### Production Environment
1. Login to PhonePe Business Dashboard (Production)
2. Go to Developer Settings > API Keys
3. Use your production credentials:
   - API Key: `73e5f6e1-1da3-403e-8168-da15fdffbd7d`

### Webhook Configuration
In your PhonePe dashboard, configure:

**For Development:**
- Webhook URL: `http://localhost:8000/api/payments/webhook/phonepe/`

**For Production:**
- Webhook URL: `https://api.okpuja.com/api/payments/webhook/phonepe/`

Set authentication username and password and update environment variables with these credentials.

## Production Deployment

### Environment Variables for Production
When deploying to production with domain `okpuja.com`, update your `.env` file:

```bash
# Switch to production environment
PHONEPE_ENV=PRODUCTION
PHONEPE_CLIENT_ID=your_production_client_id
PHONEPE_CLIENT_SECRET=73e5f6e1-1da3-403e-8168-da15fdffbd7d
PHONEPE_CLIENT_VERSION=1

# Production URLs
PHONEPE_REDIRECT_URL=https://api.okpuja.com/api/payments/webhook/phonepe/
PHONEPE_CALLBACK_URL=https://api.okpuja.com/api/payments/webhook/phonepe/
PHONEPE_FAILED_REDIRECT_URL=https://www.okpuja.com/failedbooking
PHONEPE_SUCCESS_REDIRECT_URL=https://www.okpuja.com/confirmbooking/
FRONTEND_BASE_URL=https://www.okpuja.com

# Other production settings
DEBUG=False
ALLOWED_HOSTS=okpuja.com,backend.okpuja.com,okpuja.com
```

### SSL Certificate Requirements
- **HTTPS Required**: PhonePe requires HTTPS for production webhooks
- Ensure your domain `okpuja.com` and `backend.okpuja.com` have valid SSL certificates
- Test webhook connectivity from PhonePe dashboard after deployment

### DNS Configuration
Make sure your DNS points to your server:
- `okpuja.com` → Your frontend application
- `backend.okpuja.com` → Your Django backend API

### PhonePe Dashboard Production Setup
1. Login to PhonePe Business Dashboard (Production)
2. Update webhook URL to: `https://api.okpuja.com/api/payments/webhook/phonepe/`
3. Configure callback authentication credentials
4. Test the connection from dashboard

## Testing

### Run Integration Test
```bash
python test_phonepe_integration.py
```

### Test Server
```bash
python manage.py runserver
```

### Sample Payment Test
1. Create a user account and booking
2. Use the payment API to create a payment
3. Open the returned `payment_url` in browser
4. Complete the test payment flow

## Error Handling

The integration includes comprehensive error handling:
- Network timeouts
- Invalid responses
- Authentication failures
- Invalid webhooks

## Security Considerations

1. **Webhook Validation**: All webhooks are validated using PhonePe's signature verification
2. **Environment Separation**: Separate credentials for UAT and production
3. **Secure Storage**: Sensitive data stored in environment variables
4. **HTTPS Required**: Production must use HTTPS for all endpoints

## Migration from Old Integration

If you're migrating from the old hash-based integration:

1. **Database**: No changes required to existing payment records
2. **API**: Endpoints remain the same, only backend logic updated
3. **Frontend**: No changes required, same API responses
4. **Configuration**: Update environment variables as shown above

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure PhonePe SDK is installed correctly
2. **Authentication Error**: Verify client credentials in environment
3. **Webhook Failures**: Check callback URL configuration in PhonePe dashboard
4. **Network Issues**: Verify firewall and network connectivity

### Debug Mode
Set `DEBUG=True` in settings for detailed error logs.

### Logs
Check Django logs for detailed error information:
```bash
tail -f /path/to/your/logfile
```

## Support

For PhonePe-specific issues:
- Documentation: https://developer.phonepe.com/
- Support: Contact PhonePe integration team

For implementation issues:
- Check Django logs
- Verify environment configuration
- Test with the provided test script
