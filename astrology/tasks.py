"""
Celery tasks for Astrology notification system
Enterprise-level background task processing with comprehensive notification management
"""
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import AstrologyBooking, AstrologyService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_astrology_booking_confirmation(self, booking_id):
    """Send booking confirmation email for astrology services"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        subject = f"🔮 Astrology Booking Confirmed - {booking.astro_book_id}"
        
        # Render HTML email template
        html_message = render_to_string('emails/astrology/booking_confirmation.html', {
            'booking': booking,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com'),
            'website_url': getattr(settings, 'WEBSITE_URL', 'https://okpuja.com')
        })
        
        # Plain text version
        plain_message = f"""
Dear {booking.contact_email},

Your astrology booking has been confirmed!

Booking Details:
- Booking ID: {booking.astro_book_id}
- Service: {booking.service.title}
- Date & Time: {booking.preferred_date} at {booking.preferred_time}
- Duration: {booking.service.duration_minutes} minutes
- Language: {booking.language}

Our astrologer will contact you soon to schedule the session. You will receive a Google Meet link before your session.

Thank you for choosing OkPuja for your spiritual guidance.

Best regards,
OkPuja Team
        """
        
        # Create email message
        email = EmailMessage(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.contact_email],
            reply_to=[getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com')]
        )
        email.content_subtype = "html"
        email.body = html_message
        
        # Send email
        email.send(fail_silently=False)
        
        # Send admin notification
        send_astrology_admin_notification.delay(booking_id, 'new_booking')
        
        logger.info(f"Astrology booking confirmation sent for {booking.astro_book_id}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send astrology booking confirmation: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_astrology_session_link(self, booking_id):
    """Send Google Meet session link to customer"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        if not booking.google_meet_link:
            logger.warning(f"No Google Meet link found for booking {booking.astro_book_id}")
            return
        
        subject = f"🎥 Your Session Link is Ready - {booking.astro_book_id}"
        
        html_message = render_to_string('emails/astrology/session_link.html', {
            'booking': booking,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com')
        })
        
        plain_message = f"""
Dear {booking.contact_email},

Your Google Meet session link is ready!

Session Details:
- Booking ID: {booking.astro_book_id}
- Service: {booking.service.title}
- Date & Time: {booking.preferred_date} at {booking.preferred_time}
- Duration: {booking.service.duration_minutes} minutes

Google Meet Link: {booking.google_meet_link}

Please join the session 5 minutes early to ensure everything is working properly.

Best regards,
OkPuja Team
        """
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Update booking status
        booking.is_session_scheduled = True
        booking.save(update_fields=['is_session_scheduled'])
        
        # Send admin notification
        send_astrology_admin_notification.delay(booking_id, 'session_scheduled')
        
        logger.info(f"Session link sent for booking {booking.astro_book_id}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send session link: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_astrology_session_reminder(self, booking_id, reminder_type='24h'):
    """Send session reminder notifications"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        reminder_subjects = {
            '24h': f"⏰ Reminder: Your Astrology Session Tomorrow - {booking.astro_book_id}",
            '2h': f"🔔 Your Astrology Session in 2 Hours - {booking.astro_book_id}",
            '30m': f"🚨 Your Astrology Session in 30 Minutes - {booking.astro_book_id}"
        }
        
        subject = reminder_subjects.get(reminder_type, f"Session Reminder - {booking.astro_book_id}")
        
        html_message = render_to_string('emails/astrology/session_reminder.html', {
            'booking': booking,
            'reminder_type': reminder_type,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com')
        })
        
        send_mail(
            subject,
            f"Reminder: Your astrology session with {booking.service.title} is scheduled for {booking.preferred_date} at {booking.preferred_time}",
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Session reminder ({reminder_type}) sent for booking {booking.astro_book_id}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send session reminder: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_astrology_booking_reschedule(self, booking_id, old_date, old_time, admin_user_id=None):
    """Send reschedule notification to customer"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        subject = f"📅 Session Rescheduled - {booking.astro_book_id}"
        
        context = {
            'booking': booking,
            'old_date': old_date,
            'old_time': old_time,
            'admin_user_id': admin_user_id,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com')
        }
        
        html_message = render_to_string('emails/astrology/booking_rescheduled.html', context)
        
        plain_message = f"""
Dear {booking.contact_email},

Your astrology session has been rescheduled.

Previous Time: {old_date} at {old_time}
New Time: {booking.preferred_date} at {booking.preferred_time}

Service: {booking.service.title}
Duration: {booking.service.duration_minutes} minutes

If you have any concerns about this change, please contact us immediately.

Best regards,
OkPuja Team
        """
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Reschedule notification sent for booking {booking.astro_book_id}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send reschedule notification: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_astrology_booking_status_update(self, booking_id, old_status, new_status):
    """Send status update notification to customer"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        subject = f"📄 Booking Status Updated - {booking.astro_book_id}"
        
        html_message = render_to_string('emails/astrology/booking_status_update.html', {
            'booking': booking,
            'old_status': old_status,
            'new_status': new_status,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com')
        })
        
        send_mail(
            subject,
            f"Your booking {booking.astro_book_id} status has been updated from {old_status} to {new_status}",
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Status update notification sent for booking {booking.astro_book_id}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send status update notification: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_astrology_session_completed(self, booking_id):
    """Send session completion notification with feedback request"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        subject = f"🎉 Session Completed - Thank You! - {booking.astro_book_id}"
        
        html_message = render_to_string('emails/astrology/session_completed.html', {
            'booking': booking,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com'),
            'feedback_email': getattr(settings, 'FEEDBACK_EMAIL', 'feedback@okpuja.com'),
            'website_url': getattr(settings, 'WEBSITE_URL', 'https://okpuja.com')
        })
        
        send_mail(
            subject,
            f"Thank you for your astrology consultation! We hope you found it insightful. Please share your feedback with us.",
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Schedule follow-up email after 3 days
        send_astrology_follow_up.apply_async(
            args=[booking_id],
            countdown=3 * 24 * 60 * 60  # 3 days
        )
        
        logger.info(f"Completion notification sent for booking {booking.astro_book_id}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send completion notification: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def send_astrology_follow_up(self, booking_id):
    """Send follow-up email after session completion"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        if booking.status != 'COMPLETED':
            logger.info(f"Skipping follow-up for booking {booking.astro_book_id} - status is {booking.status}")
            return
        
        subject = f"🔮 How was your astrology experience? - {booking.astro_book_id}"
        
        html_message = render_to_string('emails/astrology/follow_up.html', {
            'booking': booking,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com'),
            'website_url': getattr(settings, 'WEBSITE_URL', 'https://okpuja.com')
        })
        
        send_mail(
            subject,
            f"We hope your astrology consultation was insightful! We'd love to hear about your experience.",
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Follow-up email sent for booking {booking.astro_book_id}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send follow-up email: {str(e)}")
        raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_astrology_admin_notification(self, booking_id, notification_type):
    """Send notifications to admin team"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', ['admin@okpuja.com'])
        
        subjects = {
            'new_booking': f"🆕 New Astrology Booking - {booking.astro_book_id}",
            'session_scheduled': f"📅 Session Scheduled - {booking.astro_book_id}",
            'booking_cancelled': f"❌ Booking Cancelled - {booking.astro_book_id}",
            'session_completed': f"✅ Session Completed - {booking.astro_book_id}",
        }
        
        subject = subjects.get(notification_type, f"Astrology Notification - {booking.astro_book_id}")
        
        html_message = render_to_string('emails/astrology/admin_notification.html', {
            'booking': booking,
            'notification_type': notification_type,
            'admin_panel_url': getattr(settings, 'ADMIN_PANEL_URL', 'https://admin.okpuja.com')
        })
        
        for admin_email in admin_emails:
            send_mail(
                subject,
                f"Astrology booking notification: {notification_type} for {booking.astro_book_id}",
                settings.DEFAULT_FROM_EMAIL,
                [admin_email],
                html_message=html_message,
                fail_silently=True  # Don't fail customer operations if admin emails fail
            )
        
        logger.info(f"Admin notification sent for booking {booking.astro_book_id} - {notification_type}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send admin notification: {str(e)}")
        # Don't retry admin notifications to avoid blocking customer notifications


@shared_task
def send_daily_astrology_reminders():
    """Daily task to send session reminders"""
    try:
        # Get bookings for tomorrow (24h reminder)
        tomorrow = timezone.now().date() + timedelta(days=1)
        tomorrow_bookings = AstrologyBooking.objects.filter(
            preferred_date=tomorrow,
            status='CONFIRMED'
        ).select_related('service')
        
        for booking in tomorrow_bookings:
            send_astrology_session_reminder.delay(booking.id, '24h')
        
        # Get bookings for today in 2 hours (2h reminder)
        now = timezone.now()
        two_hours_later = now + timedelta(hours=2)
        
        today_bookings = AstrologyBooking.objects.filter(
            preferred_date=now.date(),
            status='CONFIRMED'
        ).select_related('service')
        
        for booking in today_bookings:
            booking_datetime = timezone.make_aware(
                datetime.combine(booking.preferred_date, booking.preferred_time)
            )
            
            # Send 2h reminder if session is within 2-3 hours
            if two_hours_later <= booking_datetime <= two_hours_later + timedelta(hours=1):
                send_astrology_session_reminder.delay(booking.id, '2h')
            
            # Send 30m reminder if session is within 30-45 minutes
            thirty_minutes_later = now + timedelta(minutes=30)
            if thirty_minutes_later <= booking_datetime <= thirty_minutes_later + timedelta(minutes=15):
                send_astrology_session_reminder.delay(booking.id, '30m')
        
        logger.info(f"Daily reminders processed: {tomorrow_bookings.count()} tomorrow reminders, {today_bookings.count()} today reminders")
        
    except Exception as e:
        logger.error(f"Failed to process daily reminders: {str(e)}")


@shared_task
def cleanup_astrology_notifications():
    """Weekly cleanup task for notification logs"""
    try:
        # This could include cleanup of old notification logs, metrics, etc.
        # Implementation depends on your logging strategy
        logger.info("Astrology notification cleanup completed")
        
    except Exception as e:
        logger.error(f"Failed to cleanup notifications: {str(e)}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_custom_astrology_notification(self, booking_id, message_type, custom_message, include_details=True):
    """Send custom notification to customer"""
    try:
        booking = AstrologyBooking.objects.select_related('service', 'user').get(id=booking_id)
        
        subject_map = {
            'reminder': f"Session Reminder - {booking.astro_book_id}",
            'update': f"Booking Update - {booking.astro_book_id}",
            'custom': f"Message from OkPuja - {booking.astro_book_id}",
            'follow_up': f"Follow-up - {booking.astro_book_id}"
        }
        
        subject = subject_map.get(message_type, f"Notification - {booking.astro_book_id}")
        
        html_message = render_to_string('emails/astrology/manual_notification.html', {
            'booking': booking,
            'message_type': message_type,
            'custom_message': custom_message,
            'include_details': include_details,
            'company_name': getattr(settings, 'COMPANY_NAME', 'OkPuja'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@okpuja.com')
        })
        
        send_mail(
            subject,
            custom_message or f"You have a notification regarding your booking {booking.astro_book_id}",
            settings.DEFAULT_FROM_EMAIL,
            [booking.contact_email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Custom notification sent for booking {booking.astro_book_id} - {message_type}")
        
    except AstrologyBooking.DoesNotExist:
        logger.error(f"Astrology booking with ID {booking_id} not found")
    except Exception as e:
        logger.error(f"Failed to send custom notification: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
