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
    """Send booking confirmation email with invoice details"""
    try:
        booking = Booking.objects.select_related(
            'user', 'cart', 'address', 'assigned_to'
        ).get(id=booking_id)
        
        subject = f"🙏 Booking Confirmed & Invoice - {booking.book_id}"
        html_message = render_to_string('emails/booking_confirmation_professional.html', {
            'booking': booking,
            'MEDIA_URL': settings.MEDIA_URL
        })
        
        send_mail(
            subject,
            f"Your booking {booking.book_id} has been confirmed. Please find the invoice details in the email.",
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            html_message=html_message
        )
        
        # Also send notification to admin
        send_mail(
            f"New Booking Confirmed - {booking.book_id}",
            f"Booking {booking.book_id} for {booking.user.email} has been confirmed.",
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
        )
        
        logger.info(f"Booking confirmation email sent for {booking.book_id}")
        
    except Booking.DoesNotExist:
        logger.error(f"Booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {str(e)}")

@shared_task 
def send_booking_reschedule_notification(booking_id, old_date, old_time, rescheduled_by_id):
    """Send email notification when booking is rescheduled"""
    try:
        from accounts.models import User
        
        booking = Booking.objects.select_related(
            'user', 'cart', 'address', 'assigned_to'
        ).get(id=booking_id)
        
        rescheduled_by = User.objects.get(id=rescheduled_by_id)
        
        subject = f"📅 Booking Rescheduled - {booking.book_id}"
        html_message = render_to_string('emails/booking_rescheduled.html', {
            'booking': booking,
            'old_date': old_date,
            'old_time': old_time,
            'rescheduled_by': rescheduled_by
        })
        
        send_mail(
            subject,
            f"Your booking {booking.book_id} has been rescheduled to {booking.selected_date} at {booking.selected_time}.",
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            html_message=html_message
        )
        
        logger.info(f"Reschedule notification sent for {booking.book_id}")
        
    except (Booking.DoesNotExist, User.DoesNotExist):
        logger.error(f"Booking or user not found for reschedule notification")
    except Exception as e:
        logger.error(f"Failed to send reschedule notification: {str(e)}")

@shared_task
def send_booking_assignment_notification(booking_id, assigned_by_id, old_assigned_id=None):
    """Send email notifications when booking is assigned to employee"""
    try:
        from accounts.models import User
        
        booking = Booking.objects.select_related(
            'user', 'cart', 'address', 'assigned_to'
        ).get(id=booking_id)
        
        assigned_by = User.objects.get(id=assigned_by_id)
        
        # Send notification to user
        subject_user = f"👨‍🦱 Priest Assigned - {booking.book_id}"
        html_message_user = render_to_string('emails/booking_assigned_user.html', {
            'booking': booking,
            'assigned_by': assigned_by
        })
        
        send_mail(
            subject_user,
            f"A priest has been assigned to your booking {booking.book_id}.",
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            html_message=html_message_user
        )
        
        # Send notification to assigned priest
        if booking.assigned_to:
            subject_priest = f"📋 New Booking Assignment - {booking.book_id}"
            html_message_priest = render_to_string('emails/booking_assigned_priest.html', {
                'booking': booking,
                'assigned_by': assigned_by
            })
            
            send_mail(
                subject_priest,
                f"You have been assigned to booking {booking.book_id}.",
                settings.DEFAULT_FROM_EMAIL,
                [booking.assigned_to.email],
                html_message=html_message_priest
            )
        
        logger.info(f"Assignment notifications sent for {booking.book_id}")
        
    except (Booking.DoesNotExist, User.DoesNotExist):
        logger.error(f"Booking or user not found for assignment notification")
    except Exception as e:
        logger.error(f"Failed to send assignment notification: {str(e)}")

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