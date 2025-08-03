# PhonePe V2 Webhook Configuration Guide

## 🔧 Webhook Form Configuration

Fill the PhonePe webhook form with these exact values:

### ✅ Webhook URL
```
Production: https://backend.okpuja.com/api/payments/webhook/phonepe/
Testing: https://abc123.ngrok.io/api/payments/webhook/phonepe/
```

### 🔐 Authentication Details

**Username:**
```
okpuja_webhook_user
```

**Password:**
```
okpuja_secure_webhook_2025
```

### 📝 Description
```
OKPUJA Booking Auto-Creation Webhook for Payment Success Notifications
```

### 🎯 Active Events
Select these events from the dropdown:
- ✅ **PAYMENT_SUCCESS** (Primary - triggers booking creation)
- ✅ **PAYMENT_FAILED** (Error handling)
- ✅ **PAYMENT_PENDING** (Status updates)

## 🔍 How It Works

1. **User makes payment** → PhonePe processes payment
2. **Payment success** → PhonePe sends webhook to your endpoint
3. **Webhook authentication** → Basic Auth validation with username/password
4. **Auto-booking creation** → System creates booking from cart
5. **Email notifications** → Confirmation emails sent to user and admin
6. **Cart cleanup** → Cart status updated to CONVERTED
7. **User redirect** → Smart redirect with cart_id parameter

## 🛡️ Security Features

- **Basic Authentication:** Username/password protection
- **Request validation:** Payload verification
- **Error handling:** Comprehensive logging and fallback
- **Rate limiting:** Built-in protection against spam

## 🧪 Testing the Webhook

After configuration, test with this curl command:

```bash
curl -X POST https://backend.okpuja.com/api/payments/webhook/phonepe/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic b2twdWphX3dlYmhvb2tfdXNlcjpva3B1amFfc2VjdXJlX3dlYmhvb2tfMjAyNQ==" \
  -d '{
    "merchantId": "M22KEWU5BO1I2",
    "transactionId": "TEST_TXN_123",
    "amount": 10000,
    "status": "SUCCESS",
    "paymentInstrument": {
      "type": "UPI"
    },
    "merchantOrderId": "CART_test-cart-id_123456"
  }'
```

## ⚙️ Environment Variables

Add these to your `.env` file:

```env
# Webhook Authentication
PHONEPE_WEBHOOK_USERNAME=okpuja_webhook_user
PHONEPE_WEBHOOK_PASSWORD=okpuja_secure_webhook_2025

# Production Webhook URL
PHONEPE_WEBHOOK_URL=https://backend.okpuja.com/api/payments/webhook/phonepe/
```

## 📋 Verification Checklist

- [ ] Webhook URL configured in PhonePe dashboard
- [ ] Username and password match your settings
- [ ] Active events selected (PAYMENT_SUCCESS minimum)
- [ ] SSL certificate valid on your domain
- [ ] Endpoint returns 200 OK for test requests
- [ ] Booking auto-creation working
- [ ] Email notifications sending
- [ ] Cart cleanup functioning
- [ ] Redirect URLs using cart_id

## 🚨 Important Notes

1. **Production URL:** Replace ngrok URL with your actual domain
2. **SSL Required:** PhonePe requires HTTPS endpoints
3. **Response Time:** Webhook should respond within 10 seconds
4. **Retry Logic:** PhonePe will retry failed webhooks up to 3 times
5. **Merchant ID:** Ensure webhook uses your actual merchant ID: `M22KEWU5BO1I2`

## 🔄 Workflow Summary

```
Payment Flow:
Cart Creation → Payment Order → PhonePe Payment → Webhook Notification → 
Booking Creation → Email Notifications → Smart Redirect (cart_id)
```

## 📞 Support

If webhook setup fails:
1. Check PhonePe dashboard logs
2. Verify SSL certificate
3. Test endpoint manually
4. Check authentication credentials
5. Review server logs for errors
