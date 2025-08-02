# PhonePe V2 Integration Setup Guide

## 1. Webhook Configuration

Based on your PhonePe dashboard screenshots, you need to set up a webhook URL in the PhonePe business portal.

### Webhook URL to Add in PhonePe Dashboard:
```
https://yourdomain.com/api/payments/webhook/phonepe/
```

For local testing, you can use ngrok:
```
https://your-ngrok-url.ngrok.io/api/payments/webhook/phonepe/
```

### Current Webhook Endpoint:
Your Django app already has the webhook endpoint at:
- URL: `/api/payments/webhook/phonepe/`
- View: Handles POST requests from PhonePe
- Authentication: X-VERIFY header validation

## 2. PhonePe V2 Credentials Update

Add these to your `.env` file:

```env
# PhonePe V2 Credentials (replace with your actual credentials)
PHONEPE_CLIENT_ID=your_client_id_here
PHONEPE_CLIENT_SECRET=your_client_secret_here
PHONEPE_CLIENT_VERSION=1
PHONEPE_MERCHANT_ID=your_merchant_id_here

# Environment (uat for testing, production for live)
PHONEPE_ENV=uat

# Webhook URLs
PHONEPE_WEBHOOK_URL=https://yourdomain.com/api/payments/webhook/phonepe/
```

## 3. Test Credentials from PhonePe Email:
```
clientId: TAJFOOTWEARUAT_2503031838273556894438
clientVersion: 1
clientSecret: NTY5NjExODAtZTlkNy00ZWM3LThlZWEtYWQ0NGJkMGMzMjkz
grantType: client_credentials
```

## 4. PhonePe Dashboard Setup Steps:

1. **Go to Webhooks Tab** in your PhonePe dashboard
2. **Create New Webhook** with these details:
   - **Webhook URL**: `https://yourdomain.com/api/payments/webhook/phonepe/`
   - **Username**: `your_webhook_username` (optional)
   - **Password**: `your_webhook_password` (optional)
   - **Description**: `OkPuja Payment Webhook`
   - **Active Events**: Select all payment events

3. **Test the webhook** using PhonePe's test feature

## 5. Current Integration Status:

✅ **PhonePe V2 Client**: Already implemented
✅ **Webhook Handler**: Already implemented
✅ **Booking Auto-Creation**: Working
✅ **Email Notifications**: Configured
✅ **Cart Management**: Working

## 6. Required Actions:

1. **Update Environment Variables** with your V2 credentials
2. **Add Webhook URL** in PhonePe dashboard
3. **Test with real PhonePe payments**
4. **Optionally**: Set up ngrok for local testing

## 7. Local Testing with ngrok:

```bash
# Install ngrok
npm install -g ngrok

# Expose your local server
ngrok http 8000

# Use the ngrok URL in PhonePe webhook setup
```

The system is already V2-ready and should work once you:
1. Update the credentials in your `.env` file
2. Add the webhook URL in PhonePe dashboard
