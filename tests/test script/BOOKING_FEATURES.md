# Enhanced Booking API Documentation

## 🎯 New Features Overview

The booking system has been enhanced with the following capabilities:

### 1. **Booking Assignment**
- Admin can assign bookings to employees/priests
- Automatic email notifications to both user and assigned employee
- Track who is responsible for each booking

### 2. **Booking Rescheduling** 
- Admin can reschedule any booking
- Employees can reschedule their assigned bookings
- Users can reschedule their own bookings
- Email notifications for all reschedules

### 3. **Enhanced Email Notifications**
- Invoice email with complete booking details
- Reschedule notifications with old vs new schedule
- Assignment notifications with priest details

---

## 📡 API Endpoints

### User Booking Endpoints

#### Reschedule Own Booking
```http
POST /api/bookings/{booking_id}/reschedule/
Authorization: Bearer {user_token}
Content-Type: application/json

{
  "selected_date": "2024-01-15",
  "selected_time": "10:00:00",
  "reason": "Family emergency"
}
```

**Response:**
```json
{
  "message": "Booking rescheduled successfully",
  "booking": {
    "id": 1,
    "book_id": "BK-ABC123",
    "selected_date": "2024-01-15",
    "selected_time": "10:00:00",
    "status": "CONFIRMED",
    "assigned_to": {...}
  }
}
```

---

### Admin Booking Endpoints

#### Assign Booking to Employee
```http
POST /api/admin/bookings/{booking_id}/assign/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "assigned_to_id": 5,
  "notes": "Preferred priest for this type of puja"
}
```

**Response:**
```json
{
  "message": "Booking assigned to Priest Kumar",
  "booking": {
    "id": 1,
    "book_id": "BK-ABC123",
    "assigned_to": {
      "id": 5,
      "first_name": "Priest",
      "last_name": "Kumar",
      "email": "priest@okpuja.com"
    },
    "status": "CONFIRMED"
  }
}
```

#### Admin Reschedule Booking
```http
POST /api/admin/bookings/{booking_id}/reschedule/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "selected_date": "2024-01-20",
  "selected_time": "15:30:00",
  "reason": "Priest availability change"
}
```

#### Get Available Employees
```http
GET /api/admin/bookings/employees/
Authorization: Bearer {admin_token}
```

**Response:**
```json
[
  {
    "id": 5,
    "first_name": "Priest",
    "last_name": "Kumar",
    "email": "priest@okpuja.com"
  },
  {
    "id": 7,
    "first_name": "Pandit",
    "last_name": "Sharma",
    "email": "pandit@okpuja.com"
  }
]
```

#### Admin Dashboard Stats
```http
GET /api/admin/bookings/dashboard_stats/
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "total_bookings": 150,
  "pending_bookings": 12,
  "confirmed_bookings": 85,
  "completed_bookings": 45,
  "todays_bookings": 8,
  "this_week_bookings": 32,
  "unassigned_bookings": 15,
  "status_breakdown": [
    {"status": "PENDING", "count": 12},
    {"status": "CONFIRMED", "count": 85},
    {"status": "COMPLETED", "count": 45}
  ]
}
```

---

## 🔐 Permissions

| Action | User | Employee | Admin |
|--------|------|----------|-------|
| View own bookings | ✅ | ✅ | ✅ |
| View assigned bookings | ❌ | ✅ | ✅ |
| Reschedule own booking | ✅ | ✅ | ✅ |
| Reschedule assigned booking | ❌ | ✅ | ✅ |
| Reschedule any booking | ❌ | ❌ | ✅ |
| Assign bookings | ❌ | ❌ | ✅ |
| View dashboard stats | ❌ | ❌ | ✅ |

---

## 📧 Email Notifications

### 1. Booking Confirmation with Invoice
**Triggered:** When payment is successful and booking is created
**Recipients:** User + Admin notification
**Template:** `booking_invoice.html`

### 2. Booking Rescheduled
**Triggered:** When booking date/time is changed
**Recipients:** User
**Template:** `booking_rescheduled.html`

### 3. Booking Assignment - User Notification  
**Triggered:** When booking is assigned to employee
**Recipients:** User
**Template:** `booking_assigned_user.html`

### 4. Booking Assignment - Employee Notification
**Triggered:** When booking is assigned to employee
**Recipients:** Assigned Employee
**Template:** `booking_assigned_priest.html`

---

## 🗄️ Database Changes

### New Model Fields

```python
class Booking(models.Model):
    # ... existing fields ...
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings',
        help_text="Employee/Priest assigned to handle this booking"
    )
```

### New Helper Methods

```python
# Check if booking can be rescheduled
booking.can_be_rescheduled()  # Returns bool

# Check if booking can be assigned
booking.can_be_assigned()  # Returns bool

# Reschedule booking
booking.reschedule(new_date, new_time, rescheduled_by)

# Assign booking to employee
booking.assign_to(employee, assigned_by)
```

---

## 🧪 Testing

Run the test script:
```bash
python test_booking_features.py
```

## 🚀 Deployment Steps

1. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

2. **Configure email settings** in production `.env`:
   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=your-smtp-host
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email
   EMAIL_HOST_PASSWORD=your-password
   DEFAULT_FROM_EMAIL=noreply@okpuja.com
   ADMIN_EMAIL=admin@okpuja.com
   ```

3. **Test API endpoints** using Postman or your frontend

4. **Verify email delivery** in test environment

---

## 💡 Usage Examples

### Frontend Integration

```javascript
// Reschedule booking
const rescheduleBooking = async (bookingId, newDate, newTime) => {
  const response = await fetch(`/api/bookings/${bookingId}/reschedule/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      selected_date: newDate,
      selected_time: newTime,
      reason: 'User requested change'
    })
  });
  return response.json();
};

// Admin assign booking
const assignBooking = async (bookingId, employeeId) => {
  const response = await fetch(`/api/admin/bookings/${bookingId}/assign/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      assigned_to_id: employeeId,
      notes: 'Assigned based on availability'
    })
  });
  return response.json();
};
```

---

## 🎉 Benefits

1. **Better Organization:** Clear assignment of responsibilities
2. **Improved Communication:** Automatic email notifications keep everyone informed
3. **Flexibility:** Easy rescheduling for better customer service
4. **Admin Control:** Complete oversight and management capabilities
5. **Employee Empowerment:** Employees can manage their assigned bookings
6. **Customer Satisfaction:** Transparent communication and easy rescheduling
