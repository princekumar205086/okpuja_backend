from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from twilio.rest import Client
import logging

from booking.models import Booking
from misc.models import ContactUs

logger = logging.getLogger(__name__)

@shared_task
def send_booking_confirmation(booking_id):
    booking = Booking.objects.get(id=booking_id)
    
    # Email notification only
    subject = f"Booking Confirmation - {booking.book_id}"
    message = render_to_string('emails/booking_confirmation.html', {
        'booking': booking
    })
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.user.email],
        html_message=message
    )

@shared_task
def send_booking_notification(booking_id):
    booking = Booking.objects.get(id=booking_id)
    
    status_map = {
        'CONFIRMED': ('Booking Confirmed', 'booking_confirmed.html'),
        'CANCELLED': ('Booking Cancelled', 'booking_cancelled.html'),
        'COMPLETED': ('Booking Completed', 'booking_completed.html'),
        'REJECTED': ('Booking Rejected', 'booking_rejected.html'),
        'FAILED': ('Booking Failed', 'booking_failed.html')
    }
    
    if booking.status in status_map:
        subject, template = status_map[booking.status]
        subject = f"{subject} - {booking.book_id}"
        # Email notification only
        message = render_to_string(f'emails/{template}', {
            'booking': booking
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            html_message=message
        )

@shared_task
def send_payment_notification(payment_id):
    from payment.models import Payment
    payment = Payment.objects.get(id=payment_id)
    
    # Email Notification only
    send_payment_email_notification.delay(
        payment.booking.user.email,
        f"Payment {payment.get_status_display()}",
        f"Your payment of ₹{payment.amount} for booking {payment.booking.book_id} is {payment.get_status_display()}."
    )

@shared_task
def send_payment_sms_notification(phone_number, message):
    # SMS notification disabled for now
    pass

@shared_task
def send_payment_email_notification(email, subject, message):
    try:
        html_message = render_to_string('emails/payment_notification.html', {
            'subject': subject,
            'message': message
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message
        )
    except Exception as e:
        logger.error(f"Email notification failed: {str(e)}")

@shared_task
def send_payment_initiated_notification(payment_id):
    # TODO: Implement notification logic for payment initiation
    pass

@shared_task
def send_payment_status_notification(payment_id):
    # TODO: Implement notification logic for payment status change
    pass

@shared_task
def send_refund_initiated_notification(refund_id):
    # TODO: Implement notification logic for refund initiation
    pass

@shared_task
def send_contact_confirmation_email(contact_id):
    try:
        contact = ContactUs.objects.get(pk=contact_id)
        subject = "Thank you for contacting us"
        context = {'contact': contact}
        
        text_content = render_to_string('emails/contact_confirmation.txt', context)
        html_content = render_to_string('emails/contact_confirmation.html', context)
        
        send_mail(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [contact.email],
            html_message=html_content
        )
    except ContactUs.DoesNotExist:
        pass

@shared_task
def send_contact_notification_email(contact_id):
    try:
        contact = ContactUs.objects.get(pk=contact_id)
        subject = f"New Contact Message: {contact.subject}"
        context = {'contact': contact}
        
        text_content = render_to_string('emails/contact_notification.txt', context)
        html_content = render_to_string('emails/contact_notification.html', context)
        
        send_mail(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [settings.CONTACT_NOTIFICATION_EMAIL],
            html_message=html_content
        )
    except ContactUs.DoesNotExist:
        pass