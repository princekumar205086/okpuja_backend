# Enterprise Admin Endpoints Summary for Astrology System

## 🎯 Complete Admin API Endpoints

### **Base URL:** `/api/astrology/admin/`

---

## 📊 **Dashboard & Analytics**

### 1. **GET** `/dashboard/` - *Admin Dashboard*
- **Purpose**: Comprehensive dashboard with real-time analytics
- **Features**: 
  - Total bookings, revenue, completion rates
  - Recent bookings list
  - Pending sessions requiring Google Meet links
  - Upcoming sessions (next 7 days)
  - Service performance metrics
- **Parameters**: `days` (optional, default: 30)
- **Notifications**: None (read-only)

---

## 📋 **Booking Management**

### 2. **GET** `/bookings/` - *Advanced Booking List*
- **Purpose**: Comprehensive booking management with advanced filtering
- **Features**:
  - Advanced search (booking ID, email, phone, birth place)
  - Multiple filters (status, service, date range, session status)
  - Sorting by various fields
  - Customer analytics (name, payment status, days until session)
- **Parameters**: 
  - `status`, `service`, `date_from`, `date_to`, `is_session_scheduled`
  - `search`, `ordering`
- **Notifications**: None

### 3. **GET/PATCH** `/bookings/{astro_book_id}/` - *Booking Detail Management*
- **Purpose**: View and update specific booking details
- **Features**:
  - Complete booking information
  - Update any field (status, schedule, Google Meet link, notes)
  - Automatic notification triggering
- **Notifications Triggered**:
  - ✉️ Status change notification (if status changed)
  - 🎥 Google Meet link notification (if link added/updated)  
  - 📅 Reschedule notification (if date/time changed)

---

## 🔄 **Bulk Operations**

### 4. **POST** `/bookings/bulk-actions/` - *Bulk Booking Actions*
- **Purpose**: Perform bulk operations on multiple bookings efficiently
- **Available Actions**:
  - `update_status` - Mass status updates
  - `schedule_sessions` - Add Google Meet links to multiple bookings
  - `send_reminders` - Send session reminders
  - `mark_completed` - Mark sessions as completed
  - `send_follow_up` - Send follow-up messages
- **Notifications Triggered**: Individual notifications for each affected booking

---

## 🛠️ **Service Management**

### 5. **GET/POST** `/services/` - *Service Management*
- **Purpose**: Manage astrology services with performance analytics
- **Features**:
  - List all services with booking counts and revenue
  - Create new services with image upload
  - Filter and search capabilities
- **Notifications**: Admin notification for new service creation

---

## 📈 **Reports & Analytics**

### 6. **GET** `/reports/` - *Comprehensive Reports*
- **Purpose**: Generate detailed business intelligence reports
- **Report Types**:
  - `summary` - Overall business summary
  - `revenue` - Detailed revenue analysis with service breakdown
  - `bookings` - Booking status analysis
  - `services` - Service performance metrics
- **Features**:
  - Date range filtering
  - Service-wise breakdowns
  - Trend analysis
  - Performance metrics

---

## 📧 **Manual Notifications**

### 7. **POST** `/notifications/send/` - *Custom Notifications*
- **Purpose**: Send personalized messages to customers
- **Message Types**:
  - `reminder` - Session reminders
  - `update` - Booking updates
  - `custom` - Custom messages
  - `follow_up` - Follow-up communications
- **Features**:
  - Custom message content
  - Option to include/exclude booking details
  - Professional email templates

---

## 🔔 **Comprehensive Notification System**

### **Automatic Notification Triggers:**

| **Trigger Event** | **Notification Type** | **Recipient** | **Template** |
|-------------------|----------------------|---------------|---------------|
| Booking Status Change | Status Update Email | Customer | `booking_status_update.html` |
| Google Meet Link Added | Session Link Email | Customer | `session_link.html` |
| Session Rescheduled | Reschedule Notification | Customer | `booking_rescheduled.html` |
| Bulk Session Scheduling | Session Link Email | All Customers | `session_link.html` |
| Session Reminder (24h/2h/30m) | Reminder Email | Customer | `session_reminder.html` |
| Session Completed | Completion & Feedback | Customer | `session_completed.html` |
| Manual Notification | Custom Message | Customer | `manual_notification.html` |
| New Booking | Admin Notification | Admin Team | `admin_notification.html` |

### **Advanced Notification Features:**
- ✅ **Professional HTML Templates** with responsive design
- ✅ **Multiple Reminder Types** (24h, 2h, 30min before session)
- ✅ **Comprehensive Email Content** with all booking details
- ✅ **Action Buttons** (Google Meet links, feedback forms)
- ✅ **Error Handling & Retry Logic** with Celery tasks
- ✅ **Admin Notifications** for all critical events
- ✅ **Logging & Audit Trails** for all notifications

---

## 🔐 **Security & Permissions**

### **Access Control:**
- **Required Permission**: `IsAdminUser` (Admin level access)
- **Authentication**: Bearer token required
- **Rate Limiting**: Bulk operations limited to 100 bookings
- **Data Validation**: Comprehensive input validation

### **Enterprise Security Features:**
- Role-based access control
- Audit logging for all admin actions
- Secure API endpoints with proper error handling
- Input sanitization and validation

---

## 📱 **API Response Format**

### **Success Response:**
```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation completed successfully"
}
```

### **Error Response:**
```json
{
  "success": false,
  "error": "General error message",
  "errors": {
    "field_name": ["Field-specific error"]
  }
}
```

---

## 🚀 **Enterprise Features**

### **Real-time Dashboard:**
- Live booking statistics
- Revenue analytics with trends
- Pending sessions monitoring
- Service performance tracking

### **Advanced Filtering:**
- Multi-field search capabilities
- Date range filters
- Status-based filtering
- Custom sorting options

### **Bulk Operations:**
- Efficient mass updates
- Batch notification sending
- Transaction-safe operations
- Detailed operation results

### **Professional Communication:**
- HTML email templates with modern design
- Personalized content for each customer
- Comprehensive booking information
- Action buttons for easy customer interaction

### **Business Intelligence:**
- Comprehensive reporting system
- Revenue analysis by service type
- Booking trend analysis
- Customer behavior insights

### **Notification Management:**
- Automated reminder system
- Multi-channel notifications (email + future SMS)
- Custom notification scheduling
- Failed notification retry logic

---

## 🛡️ **Error Handling**

### **Robust Error Management:**
- Graceful degradation if services are unavailable
- Detailed error logging for debugging
- User-friendly error messages
- Automatic retry for transient failures

### **Monitoring & Alerting:**
- Failed notification tracking
- Performance monitoring
- Error rate alerting
- Service health checks

---

## 📋 **Usage Examples**

### **Complete Booking Management Workflow:**

```bash
# 1. View dashboard
GET /api/astrology/admin/dashboard/

# 2. Filter pending sessions
GET /api/astrology/admin/bookings/?is_session_scheduled=false&status=CONFIRMED

# 3. Schedule multiple sessions
POST /api/astrology/admin/bookings/bulk-actions/
{
  "booking_ids": [1, 2, 3],
  "action": "schedule_sessions",
  "params": {
    "google_meet_link": "https://meet.google.com/abc-def-ghi"
  }
}

# 4. Send reminders
POST /api/astrology/admin/bookings/bulk-actions/
{
  "booking_ids": [1, 2, 3],
  "action": "send_reminders"
}

# 5. Update individual booking
PATCH /api/astrology/admin/bookings/ASTRO_BOOK_123/
{
  "status": "COMPLETED",
  "session_notes": "Excellent consultation"
}
```

---

## 🎯 **Enterprise Benefits**

### **For Administrators:**
- **Complete Control**: Manage all aspects of astrology bookings
- **Efficiency**: Bulk operations save time and reduce errors
- **Insights**: Comprehensive analytics for business decisions
- **Communication**: Professional customer communication

### **For Customers:**
- **Professional Experience**: Well-designed email communications
- **Timely Updates**: Automatic notifications at every step
- **Convenience**: Direct links to Google Meet sessions
- **Transparency**: Complete booking information in every email

### **For Business:**
- **Scalability**: Handle large volumes of bookings efficiently
- **Quality**: Consistent, professional customer experience
- **Analytics**: Data-driven insights for growth
- **Automation**: Reduced manual work, fewer errors

---

This enterprise-level admin system provides comprehensive management capabilities with professional notification handling, ensuring excellent customer experience and operational efficiency for your astrology services business.
