from django.conf import settings
from .models import SMSLog
from twilio.rest import Client

def send_sms(phone, message):
    if settings.SMS_BACKEND == 'accounts.sms.backends.twilio.TwilioBackend':
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
            return 'success'
        except Exception as e:
            return str(e)
    else:
        # Console backend for development
        print(f"SMS to {phone}: {message}")
        return 'sent'