# Quick Setup Guide for Astrology Admin System

## 🚀 Quick Setup Steps

### 1. **Update Django Settings**

Add to your `settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-host.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-email-password'
DEFAULT_FROM_EMAIL = 'OkPuja <noreply@okpuja.com>'

# Admin Notification Emails
ASTROLOGY_ADMIN_EMAILS = ['admin@okpuja.com', 'support@okpuja.com']
ADMIN_NOTIFICATION_EMAILS = ['admin@okpuja.com']
SUPPORT_EMAIL = 'support@okpuja.com'
FEEDBACK_EMAIL = 'feedback@okpuja.com'

# Company Information
COMPANY_NAME = 'OkPuja'
WEBSITE_URL = 'https://okpuja.com'
ADMIN_PANEL_URL = 'https://admin.okpuja.com'

# Celery Configuration (if using background tasks)
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
```

### 2. **Update Main URLs**

In your main `urls.py`, the astrology URLs are already included:

```python
# urls.py already includes:
path('api/astrology/', include('astrology.urls')),
```

### 3. **Run Migrations**

```bash
python manage.py makemigrations astrology
python manage.py migrate
```

### 4. **Create Admin User**

```bash
python manage.py createsuperuser
```

### 5. **Test the Endpoints**

```bash
# Get admin dashboard
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://localhost:8000/api/astrology/admin/dashboard/

# List all bookings
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://localhost:8000/api/astrology/admin/bookings/
```

## 🔧 **Optional: Celery Setup (for Background Tasks)**

### Install Celery:
```bash
pip install celery redis
```

### Create `celery.py` in your project root:
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

app = Celery('okpuja_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### Start Celery Worker:
```bash
celery -A okpuja_backend worker -l info
```

### Start Celery Beat (for scheduled tasks):
```bash
celery -A okpuja_backend beat -l info
```

## 📧 **Testing Email Templates**

Your email templates are located in:
- `templates/emails/astrology/booking_status_update.html`
- `templates/emails/astrology/booking_rescheduled.html`
- `templates/emails/astrology/session_reminder.html`
- `templates/emails/astrology/session_completed.html`
- `templates/emails/astrology/manual_notification.html`

## 🎯 **Quick API Test**

### Get Dashboard Data:
```bash
GET /api/astrology/admin/dashboard/
```

### Schedule a Session:
```bash
PATCH /api/astrology/admin/bookings/ASTRO_BOOK_123/
{
  "google_meet_link": "https://meet.google.com/abc-def-ghi",
  "session_notes": "Customer consultation session"
}
```

### Send Custom Notification:
```bash
POST /api/astrology/admin/notifications/send/
{
  "booking_id": "ASTRO_BOOK_123",
  "message_type": "custom",
  "custom_message": "We hope your consultation went well!"
}
```

## ✅ **System Check**

After setup, verify:

1. ✅ Admin endpoints are accessible
2. ✅ Email configuration works
3. ✅ Notifications are being sent
4. ✅ Dashboard shows data
5. ✅ Bulk operations work
6. ✅ Templates render correctly

## 🎉 **You're Ready!**

Your enterprise-level astrology admin system is now ready with:
- 📊 Real-time dashboard
- 📋 Advanced booking management
- 🔄 Bulk operations
- 📧 Professional notifications
- 📈 Comprehensive reporting

## 🆘 **Need Help?**

Check the detailed documentation in:
- `ENTERPRISE_ADMIN_ENDPOINTS.md` - Complete endpoint reference
- `ADMIN_API_DOCUMENTATION.md` - Detailed API documentation
