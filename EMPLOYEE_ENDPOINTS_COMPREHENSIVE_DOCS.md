# Employee Endpoints API Documentation

## Overview
This document provides comprehensive documentation for all employee-related endpoints in the OKPUJA API system. The system supports three main user roles: USER (customers), EMPLOYEE (priests/service providers), and ADMIN (administrators).

## Base URL
```
http://localhost:8000/api
```

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Getting JWT Token
1. Register/Login to get access and refresh tokens
2. Use access token for API calls
3. Refresh token when access token expires

## User Roles

### EMPLOYEE (Priest/Service Provider)
- Can view their own bookings and assigned bookings
- Can update status of assigned bookings
- Can manage their profile
- Cannot access admin functions

### ADMIN (Administrator)
- Full access to all endpoints
- Can manage employees and assignments
- Can view all bookings and analytics
- Can assign/reassign bookings

### USER (Customer)
- Can book services
- Can view their own bookings
- Cannot access employee or admin functions

## Employee Registration Process

1. **Employee obtains registration code** from admin
2. **Employee registers** using `/api/auth/register/` with the code
3. **Employee logs in** to get JWT tokens
4. **Admin can manage** employee through admin endpoints

## Endpoints

## Employee Authentication & Profile Management

### POST /api/auth/register/

**Description**: Register a new employee/priest account

**Authentication**: Not Required
**Admin Only**: No

**Request Payload**:
```json
{
  "email": "employee@example.com",
  "phone": "9876543210",
  "password": "securepassword123",
  "password2": "securepassword123",
  "role": "EMPLOYEE",
  "employee_registration_code": "EMP_REG_CODE_2024"
}
```

**Response** (Status: 201):
```json
{
  "id": 3,
  "email": "employee@example.com",
  "username": "",
  "phone": "9876543210",
  "role": "EMPLOYEE",
  "account_status": "PENDING",
  "is_active": true,
  "date_joined": "2024-08-21T06:00:00Z"
}
```

**Notes**: Requires valid employee_registration_code from settings

---

### POST /api/auth/login/

**Description**: Employee login to get JWT tokens

**Authentication**: Not Required
**Admin Only**: No

**Request Payload**:
```json
{
  "email": "employee@example.com",
  "password": "securepassword123"
}
```

**Response** (Status: 200):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 3,
    "email": "employee@example.com",
    "role": "EMPLOYEE",
    "is_admin": false,
    "is_employee": true,
    "is_user": false
  }
}
```

---

### GET /api/auth/check-role/

**Description**: Check current user role and permissions

**Authentication**: Required
**Admin Only**: No

**Response** (Status: 200):
```json
{
  "user_id": 3,
  "email": "employee@example.com",
  "role": "EMPLOYEE",
  "is_admin": false,
  "is_employee": true,
  "is_user": false,
  "account_status": "ACTIVE"
}
```

---

### GET /api/auth/profile/

**Description**: Get employee profile information

**Authentication**: Required
**Admin Only**: No

**Response** (Status: 200):
```json
{
  "user": {
    "id": 3,
    "email": "employee@example.com",
    "username": "priest_ram",
    "phone": "9876543210",
    "role": "EMPLOYEE",
    "account_status": "ACTIVE",
    "is_active": true,
    "date_joined": "2024-08-21T06:00:00Z"
  },
  "profile": {
    "first_name": "Ram",
    "last_name": "Sharma",
    "dob": "1985-06-15",
    "profile_picture": "https://example.com/profile.jpg",
    "profile_thumbnail": "https://example.com/thumb.jpg"
  }
}
```

---

### PUT /api/auth/profile/

**Description**: Update employee profile information

**Authentication**: Required
**Admin Only**: No

**Request Payload**:
```json
{
  "first_name": "Ram",
  "last_name": "Sharma",
  "dob": "1985-06-15"
}
```

**Response** (Status: 200):
```json
{
  "first_name": "Ram",
  "last_name": "Sharma",
  "dob": "1985-06-15",
  "profile_picture": "https://example.com/profile.jpg",
  "profile_thumbnail": "https://example.com/thumb.jpg",
  "created_at": "2024-08-21T06:00:00Z",
  "updated_at": "2024-08-21T06:30:00Z"
}
```

---

### GET /api/auth/users/

**Description**: List all users (admin can filter by role to get employees)

**Authentication**: Required
**Admin Only**: Yes

**Query Parameters**:
- `role`: Filter by role (EMPLOYEE, ADMIN, USER)
- `search`: Search by email or username
- `is_active`: Filter by active status (true/false)
- `page`: Page number for pagination

**Response** (Status: 200):
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 3,
      "email": "employee@example.com",
      "username": "priest_ram",
      "phone": "9876543210",
      "role": "EMPLOYEE",
      "account_status": "ACTIVE",
      "is_active": true,
      "date_joined": "2024-08-21T06:00:00Z"
    }
  ]
}
```

---

### GET /api/auth/users/{id}/

**Description**: Get detailed information about a specific employee

**Authentication**: Required
**Admin Only**: Yes

**Response** (Status: 200):
```json
{
  "id": 3,
  "email": "employee@example.com",
  "username": "priest_ram",
  "phone": "9876543210",
  "role": "EMPLOYEE",
  "account_status": "ACTIVE",
  "is_active": true,
  "date_joined": "2024-08-21T06:00:00Z",
  "profile": {
    "first_name": "Ram",
    "last_name": "Sharma",
    "dob": "1985-06-15",
    "profile_picture": "https://example.com/profile.jpg"
  },
  "statistics": {
    "total_assignments": 25,
    "completed_assignments": 20,
    "active_assignments": 3,
    "completion_rate": 80.0
  }
}
```

---

### PUT /api/auth/users/{id}/

**Description**: Update employee account status and details

**Authentication**: Required
**Admin Only**: Yes

**Request Payload**:
```json
{
  "account_status": "ACTIVE",
  "is_active": true
}
```

**Response** (Status: 200):
```json
{
  "id": 3,
  "email": "employee@example.com",
  "username": "priest_ram",
  "phone": "9876543210",
  "role": "EMPLOYEE",
  "account_status": "ACTIVE",
  "is_active": true,
  "date_joined": "2024-08-21T06:00:00Z"
}
```

---

## Employee Booking Management

### GET /api/booking/bookings/

**Description**: Get employee's own bookings and assigned bookings

**Authentication**: Required
**Admin Only**: No

**Query Parameters**:
- `status`: Status filter (PENDING, CONFIRMED, COMPLETED, etc.)
- `ordering`: Sort by field (-created_at for newest first)
- `page`: Page number for pagination

**Response** (Status: 200):
```json
{
  "count": 15,
  "next": "http://localhost:8000/api/booking/bookings/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "book_id": "BOOK20240821001",
      "user": {
        "id": 2,
        "email": "customer@example.com",
        "username": "customer1"
      },
      "cart": {
        "id": 1,
        "total_amount": "2500.00"
      },
      "status": "CONFIRMED",
      "selected_date": "2024-08-25",
      "selected_time": "10:00",
      "assigned_to": {
        "id": 3,
        "email": "employee@example.com",
        "username": "priest_ram"
      },
      "created_at": "2024-08-21T06:00:00Z",
      "updated_at": "2024-08-21T06:30:00Z"
    }
  ]
}
```

---

### GET /api/booking/bookings/{id}/

**Description**: Get detailed information about a specific booking

**Authentication**: Required
**Admin Only**: No

**Response** (Status: 200):
```json
{
  "id": 1,
  "book_id": "BOOK20240821001",
  "user": {
    "id": 2,
    "email": "customer@example.com",
    "username": "customer1"
  },
  "cart": {
    "id": 1,
    "total_amount": "2500.00",
    "items": [
      {
        "id": 1,
        "service_name": "Ganesh Puja",
        "quantity": 1,
        "price": "2500.00"
      }
    ]
  },
  "status": "CONFIRMED",
  "selected_date": "2024-08-25",
  "selected_time": "10:00",
  "address": {
    "address_line1": "123 Main Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001"
  },
  "assigned_to": {
    "id": 3,
    "email": "employee@example.com",
    "username": "priest_ram"
  },
  "special_instructions": "Please bring all required materials",
  "attachments": [],
  "created_at": "2024-08-21T06:00:00Z",
  "updated_at": "2024-08-21T06:30:00Z"
}
```

---

### POST /api/booking/bookings/{id}/status/

**Description**: Update booking status (employee can update assigned bookings)

**Authentication**: Required
**Admin Only**: No

**Request Payload**:
```json
{
  "status": "IN_PROGRESS",
  "notes": "Puja ceremony has started"
}
```

**Response** (Status: 200):
```json
{
  "id": 1,
  "book_id": "BOOK20240821001",
  "status": "IN_PROGRESS",
  "status_updated_at": "2024-08-25T10:00:00Z",
  "status_updated_by": {
    "id": 3,
    "email": "employee@example.com"
  },
  "notes": "Puja ceremony has started"
}
```

**Notes**: Employee can only update status of bookings assigned to them

---

## Admin Employee Management

### GET /api/booking/admin/employees/

**Description**: Get list of all employees that can be assigned to bookings

**Authentication**: Required
**Admin Only**: Yes

**Response** (Status: 200):
```json
[
  {
    "id": 3,
    "email": "employee@example.com",
    "username": "priest_ram",
    "first_name": "Ram",
    "last_name": "Sharma"
  },
  {
    "id": 4,
    "email": "priest2@example.com",
    "username": "priest_shyam",
    "first_name": "Shyam",
    "last_name": "Pandey"
  }
]
```

---

### POST /api/booking/admin/bookings/{booking_id}/assign/

**Description**: Assign a booking to an employee/priest

**Authentication**: Required
**Admin Only**: Yes

**Request Payload**:
```json
{
  "assigned_to_id": 3,
  "notes": "Assigned to experienced priest for Ganesh Puja"
}
```

**Response** (Status: 200):
```json
{
  "success": true,
  "message": "Booking assigned to employee@example.com successfully",
  "booking": {
    "id": 1,
    "book_id": "BOOK20240821001",
    "assigned_to": {
      "id": 3,
      "email": "employee@example.com",
      "username": "priest_ram"
    },
    "assignment_notes": "Assigned to experienced priest for Ganesh Puja",
    "assigned_at": "2024-08-21T07:00:00Z",
    "assigned_by": {
      "id": 1,
      "email": "admin@example.com"
    }
  }
}
```

---

### GET /api/booking/admin/dashboard/

**Description**: Get admin dashboard with booking analytics including employee metrics

**Authentication**: Required
**Admin Only**: Yes

**Query Parameters**:
- `days`: Number of days for analytics (default: 30)

**Response** (Status: 200):
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_bookings": 1250,
      "confirmed_bookings": 980,
      "completed_bookings": 850,
      "cancelled_bookings": 75,
      "pending_bookings": 195,
      "total_revenue": "2750000.00",
      "average_booking_value": "2200.00",
      "active_employees": 25
    },
    "employee_metrics": {
      "total_employees": 25,
      "active_employees": 23,
      "average_completion_rate": 85.5,
      "top_performers": [
        {
          "id": 3,
          "name": "Ram Sharma",
          "completion_rate": 95.0,
          "total_assignments": 45
        }
      ]
    },
    "recent_bookings": [],
    "upcoming_bookings": []
  }
}
```

---

### GET /api/booking/admin/bookings/

**Description**: Get all bookings with advanced filtering and employee information

**Authentication**: Required
**Admin Only**: Yes

**Query Parameters**:
- `status`: Filter by booking status
- `assigned_to`: Filter by assigned employee ID
- `user`: Filter by customer user ID
- `search`: Search by book_id, user email, or employee email
- `ordering`: Sort by field (-created_at for newest first)
- `page`: Page number for pagination

**Response** (Status: 200):
```json
{
  "count": 1250,
  "next": "http://localhost:8000/api/booking/admin/bookings/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "book_id": "BOOK20240821001",
      "user": {
        "id": 2,
        "email": "customer@example.com",
        "username": "customer1"
      },
      "assigned_to": {
        "id": 3,
        "email": "employee@example.com",
        "username": "priest_ram",
        "full_name": "Ram Sharma"
      },
      "status": "CONFIRMED",
      "selected_date": "2024-08-25",
      "selected_time": "10:00",
      "total_amount": "2500.00",
      "created_at": "2024-08-21T06:00:00Z"
    }
  ]
}
```

---


## Error Responses

### Common Error Format
```json
{
  "error": "Error message description",
  "detail": "Detailed error information",
  "field_errors": {
    "field_name": ["Field specific error messages"]
  }
}
```

### HTTP Status Codes
- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data or validation errors
- **401 Unauthorized**: Authentication required or invalid token
- **403 Forbidden**: Insufficient permissions for the requested action
- **404 Not Found**: Requested resource not found
- **500 Internal Server Error**: Server-side error

## Employee Workflow Examples

### 1. Employee Registration and Login
```bash
# 1. Register as employee (requires registration code)
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "priest@example.com",
    "phone": "9876543210",
    "password": "securepass123",
    "password2": "securepass123",
    "role": "EMPLOYEE",
    "employee_registration_code": "EMP_REG_CODE_2024"
  }'

# 2. Login to get JWT tokens
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "priest@example.com",
    "password": "securepass123"
  }'
```

### 2. Employee Viewing Assigned Bookings
```bash
# Get all assigned bookings
curl -X GET http://localhost:8000/api/booking/bookings/ \
  -H "Authorization: Bearer <employee_jwt_token>"

# Get specific booking details
curl -X GET http://localhost:8000/api/booking/bookings/1/ \
  -H "Authorization: Bearer <employee_jwt_token>"
```

### 3. Employee Updating Booking Status
```bash
# Update booking status
curl -X POST http://localhost:8000/api/booking/bookings/1/status/ \
  -H "Authorization: Bearer <employee_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "IN_PROGRESS",
    "notes": "Puja ceremony has started"
  }'
```

### 4. Admin Managing Employees
```bash
# Get list of employees
curl -X GET http://localhost:8000/api/booking/admin/employees/ \
  -H "Authorization: Bearer <admin_jwt_token>"

# Assign booking to employee
curl -X POST http://localhost:8000/api/booking/admin/bookings/1/assign/ \
  -H "Authorization: Bearer <admin_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "assigned_to_id": 3,
    "notes": "Assigned to experienced priest"
  }'
```

## Configuration Requirements

### Django Settings
```python
# settings.py

# Employee registration code
EMPLOYEE_REGISTRATION_CODE = "your_secret_employee_code_here"

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# CORS settings (if frontend is on different domain)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000",
]
```

## Testing the API

### 1. Start the Django Server
```bash
python manage.py runserver
```

### 2. Test Employee Endpoints
```bash
# Test employee registration
python test_employee_endpoints.py

# Or use curl/postman with the examples above
```

### 3. Common Testing Scenarios

1. **Employee Registration Flow**
   - Register employee with valid code
   - Login to get tokens
   - Access employee endpoints

2. **Booking Assignment Flow**
   - Admin creates/views bookings
   - Admin assigns booking to employee
   - Employee views assigned booking
   - Employee updates booking status

3. **Permission Testing**
   - Employee tries to access admin endpoints (should fail)
   - Regular user tries to access employee endpoints (should fail)
   - Unauthenticated requests to protected endpoints (should fail)

## Security Considerations

1. **Employee Registration Code**: Keep the registration code secure and change it periodically
2. **JWT Token Security**: Implement proper token refresh and expiration handling
3. **Permission Checks**: All endpoints properly validate user roles and permissions
4. **Data Validation**: All input data is validated before processing
5. **Rate Limiting**: Consider implementing rate limiting for registration and login endpoints

## Troubleshooting

### Common Issues

1. **"Invalid employee registration code"**
   - Check that `EMPLOYEE_REGISTRATION_CODE` is set in settings
   - Ensure the code matches exactly

2. **"Invalid HTTP_HOST header"**
   - Add your domain to `ALLOWED_HOSTS` in settings
   - For development: `ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']`

3. **"Authentication credentials were not provided"**
   - Ensure JWT token is included in Authorization header
   - Check token format: `Bearer <token>`

4. **"User does not have permission"**
   - Verify user role matches endpoint requirements
   - Check if user account is active

### Support

For additional support or questions about the employee endpoints:
1. Check the Django logs for detailed error messages
2. Review the API documentation at `/api/docs/`
3. Test endpoints using the provided examples
4. Ensure all dependencies are installed and configured properly
