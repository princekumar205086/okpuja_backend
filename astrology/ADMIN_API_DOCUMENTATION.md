# Astrology Admin API Documentation

## Enterprise-Level Admin Endpoints

This document provides comprehensive documentation for all admin endpoints in the Astrology system, designed for enterprise-level management with full notification support.

## Base URL
```
https://your-domain.com/api/astrology/admin/
```

## Authentication
All admin endpoints require admin-level authentication. Include the authorization header:
```
Authorization: Bearer <your-admin-token>
```

## Endpoints Overview

### 1. Dashboard & Analytics

#### GET `/dashboard/`
Comprehensive dashboard with analytics and overview data.

**Parameters:**
- `days` (optional): Number of days for analytics (default: 30)

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_bookings": 150,
      "confirmed_bookings": 120,
      "completed_bookings": 80,
      "cancelled_bookings": 10,
      "pending_sessions": 15,
      "total_revenue": "299800.00",
      "average_booking_value": "1999.00",
      "bookings_this_period": 45,
      "active_services": 6
    },
    "recent_bookings": [...],
    "pending_sessions": [...],
    "upcoming_sessions": [...],
    "service_performance": [...]
  }
}
```

**Notifications Triggered:**
- None (Read-only operation)

---

### 2. Booking Management

#### GET `/bookings/`
Advanced booking management with filtering and search.

**Parameters:**
- `status`: Filter by booking status
- `service`: Filter by service ID
- `date_from`: Start date filter (YYYY-MM-DD)
- `date_to`: End date filter (YYYY-MM-DD)
- `is_session_scheduled`: Filter by session status (true/false)
- `search`: Search in booking ID, email, phone, birth place
- `ordering`: Sort by created_at, preferred_date, preferred_time

**Response:**
```json
{
  "count": 150,
  "next": "http://...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "astro_book_id": "ASTRO_BOOK_123",
      "payment_id": "PAY_456",
      "user": {...},
      "service": {...},
      "customer_name": "John Doe",
      "session_status": "Scheduled & Link Sent",
      "payment_status": "Paid",
      "days_until_session": 3,
      "preferred_date": "2025-08-10",
      "preferred_time": "10:00:00",
      "status": "CONFIRMED",
      ...
    }
  ]
}
```

#### GET `/bookings/{astro_book_id}/`
Get detailed booking information for a specific booking.

#### PATCH `/bookings/{astro_book_id}/`
Update booking details with automatic notifications.

**Request Body:**
```json
{
  "status": "COMPLETED",
  "google_meet_link": "https://meet.google.com/abc-def-ghi",
  "session_notes": "Customer was very satisfied with the consultation",
  "preferred_date": "2025-08-10",
  "preferred_time": "10:00:00"
}
```

**Notifications Triggered:**
- Status change notification (if status changed)
- Google Meet link notification (if link added/updated)
- Reschedule notification (if date/time changed)

---

### 3. Bulk Operations

#### POST `/bookings/bulk-actions/`
Perform bulk operations on multiple bookings.

**Request Body:**
```json
{
  "booking_ids": [1, 2, 3, 4],
  "action": "schedule_sessions",
  "params": {
    "google_meet_link": "https://meet.google.com/bulk-session",
    "session_notes": "Bulk scheduled session"
  }
}
```

**Available Actions:**
- `update_status`: Update booking status
- `schedule_sessions`: Add Google Meet links
- `send_reminders`: Send session reminders
- `mark_completed`: Mark sessions as completed
- `send_follow_up`: Send follow-up messages

**Response:**
```json
{
  "success": true,
  "message": "Bulk action 'schedule_sessions' completed",
  "processed": 4,
  "failed": 0,
  "details": [
    {
      "booking_id": "ASTRO_BOOK_123",
      "status": "success",
      "message": "Action 'schedule_sessions' completed successfully"
    }
  ]
}
```

**Notifications Triggered:**
- Individual notifications for each booking based on the action

---

### 4. Service Management

#### GET `/services/`
List all astrology services with performance metrics.

**Parameters:**
- `service_type`: Filter by service type
- `is_active`: Filter by active status
- `search`: Search in title and description
- `ordering`: Sort by various fields

#### POST `/services/`
Create new astrology service.

**Request Body:**
```json
{
  "title": "Advanced Gemstone Consultation",
  "service_type": "GEMSTONE",
  "description": "Detailed analysis and recommendation of gemstones",
  "price": "2999.00",
  "duration_minutes": 60,
  "is_active": true,
  "image": "<image-file>"
}
```

**Notifications Triggered:**
- Admin notification for new service creation

---

### 5. Reports & Analytics

#### GET `/reports/`
Generate comprehensive reports.

**Parameters:**
- `report_type`: summary, revenue, bookings, services
- `start_date`: Report start date (YYYY-MM-DD)
- `end_date`: Report end date (YYYY-MM-DD)

**Response Structure:**
```json
{
  "success": true,
  "report_type": "summary",
  "date_range": {
    "start_date": "2025-07-01",
    "end_date": "2025-08-01"
  },
  "data": {
    "revenue": {...},
    "bookings": {...},
    "services": {...}
  }
}
```

**Report Types:**

##### Revenue Report
```json
{
  "total_revenue": 299800.00,
  "total_bookings": 150,
  "average_booking_value": 1999.00,
  "service_breakdown": {
    "Horoscope Analysis": {
      "count": 50,
      "revenue": 99750.00
    }
  }
}
```

##### Booking Report
```json
{
  "total_bookings": 150,
  "status_breakdown": {
    "CONFIRMED": {
      "count": 100,
      "display_name": "Confirmed"
    },
    "COMPLETED": {
      "count": 40,
      "display_name": "Completed"
    }
  },
  "sessions_scheduled": 120,
  "pending_sessions": 30
}
```

---

### 6. Manual Notifications

#### POST `/notifications/send/`
Send manual notifications to customers.

**Request Body:**
```json
{
  "booking_id": "ASTRO_BOOK_123",
  "message_type": "custom",
  "custom_message": "We wanted to check how your consultation went. Please feel free to reach out if you have any questions.",
  "include_booking_details": true
}
```

**Message Types:**
- `reminder`: Session reminder
- `update`: Booking update
- `custom`: Custom message
- `follow_up`: Follow-up message

**Notifications Triggered:**
- Custom email notification to customer

---

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "success": false,
  "error": "Error message",
  "errors": {
    "field_name": ["Field-specific error message"]
  }
}
```

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `500`: Internal Server Error

---

## Notification System

### Email Templates
The system includes professional HTML email templates for all notifications:

1. **Booking Status Update** (`booking_status_update.html`)
2. **Session Rescheduled** (`booking_rescheduled.html`)
3. **Session Reminder** (`session_reminder.html`)
4. **Session Completed** (`session_completed.html`)
5. **Manual Notification** (`manual_notification.html`)

### Notification Triggers

| Action | Notification Sent | Recipients |
|--------|------------------|------------|
| Status Change | Status update email | Customer |
| Add Google Meet Link | Session link email | Customer |
| Reschedule Session | Reschedule notification | Customer |
| Bulk Session Scheduling | Session link email | All affected customers |
| Manual Notification | Custom message email | Customer |
| Session Completion | Completion & feedback email | Customer |

### Notification Features

- **Professional HTML Templates**: Responsive design with modern styling
- **Comprehensive Information**: All relevant booking details included
- **Action Buttons**: Direct links to Google Meet, feedback forms, etc.
- **Error Handling**: Graceful fallback if notifications fail
- **Logging**: All notifications are logged for audit trails

---

## Permissions & Security

### Admin Permissions Required
- `IsAdminUser`: Full admin access for all endpoints
- All endpoints require authenticated admin users
- Role-based access control integrated

### Rate Limiting
- Bulk operations: Limited to 100 bookings per request
- Notification sending: Rate limited to prevent spam

### Data Validation
- Comprehensive input validation on all endpoints
- Date/time validation for scheduling
- Email format validation
- URL validation for Google Meet links

---

## Usage Examples

### Complete Booking Management Flow

1. **View Dashboard**
```bash
GET /api/astrology/admin/dashboard/
```

2. **Filter Pending Sessions**
```bash
GET /api/astrology/admin/bookings/?is_session_scheduled=false&status=CONFIRMED
```

3. **Schedule Multiple Sessions**
```bash
POST /api/astrology/admin/bookings/bulk-actions/
{
  "booking_ids": [1, 2, 3],
  "action": "schedule_sessions",
  "params": {
    "google_meet_link": "https://meet.google.com/abc-def-ghi"
  }
}
```

4. **Send Reminders**
```bash
POST /api/astrology/admin/bookings/bulk-actions/
{
  "booking_ids": [1, 2, 3],
  "action": "send_reminders"
}
```

5. **Mark Completed**
```bash
PATCH /api/astrology/admin/bookings/ASTRO_BOOK_123/
{
  "status": "COMPLETED",
  "session_notes": "Excellent consultation session"
}
```

### Reporting Flow

1. **Generate Revenue Report**
```bash
GET /api/astrology/admin/reports/?report_type=revenue&start_date=2025-07-01&end_date=2025-08-01
```

2. **Get Service Performance**
```bash
GET /api/astrology/admin/reports/?report_type=services&days=30
```

---

## Integration Notes

### Frontend Integration
- All endpoints return JSON responses suitable for modern frontend frameworks
- Consistent data structures across all endpoints
- Real-time updates supported through WebSocket connections (if implemented)

### Third-party Integrations
- Google Meet API integration for session links
- Email service integration (SMTP/SendGrid/SES)
- Payment gateway integration for refund processing

### Monitoring & Analytics
- Built-in logging for all admin actions
- Performance metrics tracking
- Error monitoring and alerting capabilities

---

This comprehensive admin system provides enterprise-level functionality with robust notification management, ensuring professional communication with customers at every step of their astrology journey.
