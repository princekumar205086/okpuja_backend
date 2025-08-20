# Employee Endpoints API Documentation

## Overview
This document provides comprehensive documentation for all employee-related endpoints in the OKPUJA API system.

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Employee Roles
- **USER**: Regular customer
- **EMPLOYEE**: Priest/Service provider who can be assigned to bookings
- **ADMIN**: Administrator with full access

## Endpoints

## Error Responses

Common error response format:
```json
{
  "error": "Error message description",
  "detail": "Detailed error information"
}
```

### HTTP Status Codes
- **200**: Success
- **201**: Created successfully
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **500**: Internal Server Error

## Employee Registration Process

1. Employee obtains registration code from admin
2. Employee uses registration endpoint with code
3. Admin can view and manage employees
4. Admin assigns bookings to employees
5. Employees view and manage assigned bookings

## Booking Assignment Workflow

1. Admin views unassigned bookings
2. Admin gets list of available employees
3. Admin assigns booking to specific employee
4. Employee receives notification (if configured)
5. Employee manages assigned booking through their booking list

## Employee Permissions

**Employees can**:
- View their own bookings
- View bookings assigned to them
- Update status of assigned bookings
- Access their profile and settings

**Employees cannot**:
- View other employees' bookings
- Access admin-only endpoints
- Assign/reassign bookings
- Access full user management

## Testing Notes

To test these endpoints:

1. **Start the Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Register as employee** (requires valid registration code)
3. **Login to get JWT token**
4. **Use token in Authorization header for protected endpoints**

## Configuration Required

In `settings.py`, set:
```python
EMPLOYEE_REGISTRATION_CODE = "your_secret_code_here"
```

This code is required for employee registration.
