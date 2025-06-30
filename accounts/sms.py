from django.conf import settings
from .models import SMSLog
from twilio.rest import Client

def send_sms(phone, message):
    # Corrected the backend path to match the .env file
    if settings.SMS_BACKEND == 'accounts.sms.backends.twilio.SMSBackend':
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            response = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
            # Log the SID for debugging and confirmation
            print(f"Twilio message sent with SID: {response.sid}")
            return 'success'
        except Exception as e:
            print(f"Twilio Error: {e}")
            return str(e)
    else:
        # Console backend for development
        print(f"SMS to {phone}: {message}")
        return 'sent'