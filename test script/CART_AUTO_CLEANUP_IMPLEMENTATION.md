# Cart Auto-Cleanup Implementation

## Problem Summary
When users try to delete a cart with pending payments, they get a generic error:
```json
{
    "error": "Cannot delete cart with pending payments",
    "detail": "This cart has pending payments. Please wait for payment completion or cancellation.",
    "can_delete": false
}
```

This doesn't provide specific timing information or graceful handling for abandoned payments.

## Solution Implemented

### 1. Enhanced Deletion Logic with 30-Minute Auto-Cleanup

**New Cart Model Methods**:

#### `get_deletion_info()`
Provides detailed information about cart deletion status including timing:

```python
def get_deletion_info(self):
    """Get detailed information about why cart cannot be deleted and when it can be"""
    # Returns structured data with:
    # - can_delete: boolean
    # - reason: specific reason code
    # - message: user-friendly message
    # - wait_time_minutes: remaining wait time
    # - retry_after: ISO timestamp when cart can be deleted
    # - payment_count: number of pending payments
    # - latest_payment_age_minutes: age of newest payment
```

#### `auto_cleanup_old_payments()`
Automatically cancels pending payments older than 30 minutes:

```python
def auto_cleanup_old_payments(self):
    """Auto-cleanup pending payments older than 30 minutes"""
    # Marks old pending payments as CANCELLED
    # Returns cleanup summary with count of payments processed
```

### 2. Enhanced API Error Messages

#### Before (Generic Error):
```json
{
    "error": "Cannot delete cart with pending payments",
    "detail": "This cart has pending payments. Please wait for payment completion or cancellation.",
    "can_delete": false
}
```

#### After (Detailed Timing Info):
```json
{
    "error": "Cannot delete cart with recent pending payments",
    "detail": "Cart has pending payment(s). Please wait 15 more minute(s) before deletion or complete the payment.",
    "can_delete": false,
    "wait_time_minutes": 15,
    "retry_after": "2025-07-20T03:30:00.000Z",
    "payment_count": 1,
    "latest_payment_age_minutes": 15,
    "auto_cleanup": null
}
```

#### Auto-Cleanup Success:
```json
{
    "message": "Cart deleted successfully",
    "deleted_cart_id": "abc-123-def",
    "auto_cleanup": {
        "cleaned_up": true,
        "payments_cancelled": 2,
        "message": "Auto-cancelled 2 pending payment(s) older than 30 minutes"
    }
}
```

### 3. New API Endpoints

#### Enhanced Deletion Status Check
```
GET /api/cart/carts/{id}/deletion_status/
```

**Response Example**:
```json
{
    "can_delete": false,
    "cart_status": "ACTIVE",
    "payments_count": 1,
    "payments": [
        {
            "transaction_id": "TXN123ABC",
            "status": "PENDING",
            "amount": "5000.00",
            "created_at": "2025-07-20T03:00:00Z",
            "age_minutes": 15,
            "has_booking": false
        }
    ],
    "deletion_info": {
        "can_delete": false,
        "reason": "pending_payment_wait",
        "message": "Cart has pending payment(s). Please wait 15 more minute(s) before deletion or complete the payment.",
        "wait_time_minutes": 15,
        "retry_after": "2025-07-20T03:30:00.000Z",
        "payment_count": 1,
        "latest_payment_age_minutes": 15
    }
}
```

#### Manual Cleanup Trigger
```
POST /api/cart/carts/{id}/cleanup_old_payments/
```

**Response Example**:
```json
{
    "cleanup_performed": true,
    "payments_cancelled": 1,
    "message": "Auto-cancelled 1 pending payment(s) older than 30 minutes",
    "can_delete_now": true,
    "deletion_info": {
        "can_delete": true,
        "reason": "No payments associated"
    }
}
```

### 4. Management Command for Bulk Cleanup

```bash
# Dry run to see what would be cleaned
python manage.py cleanup_old_pending_payments --dry-run

# Clean up payments older than 30 minutes (default)
python manage.py cleanup_old_pending_payments

# Clean up payments older than 15 minutes
python manage.py cleanup_old_pending_payments --minutes 15

# Dry run with custom threshold
python manage.py cleanup_old_pending_payments --minutes 45 --dry-run
```

**Command Output Example**:
```
Cleaning up pending payments older than 30 minutes...
Found 3 old pending payments
  Payment TXN123: 35 minutes old, Cart: abc-def-123
  Payment TXN456: 45 minutes old, Cart: def-ghi-456
  Payment TXN789: 120 minutes old, Cart: ghi-jkl-789
Successfully cancelled 3 old pending payments affecting 3 carts

Affected carts:
  Cart abc-def-123: Can delete: True
  Cart def-ghi-456: Can delete: True
  Cart ghi-jkl-789: Can delete: True

Cleanup completed!
```

## Business Logic Implementation

### 1. 30-Minute Grace Period
- Pending payments are considered "fresh" for 30 minutes
- Users get specific wait times in error messages
- After 30 minutes, payments are auto-cancelled and cart can be deleted

### 2. Graceful Error Handling
- **0-30 minutes**: Clear error message with exact wait time
- **30+ minutes**: Auto-cleanup and allow deletion
- **No payments**: Immediate deletion allowed
- **Failed/Cancelled payments**: Immediate deletion allowed

### 3. User Experience Improvements
- **Countdown timer info**: "Please wait 15 more minute(s)"
- **Retry timestamp**: When exactly they can try again
- **Payment age display**: How long payments have been pending
- **Auto-cleanup feedback**: Notification when old payments are cleared

### 4. Automatic Maintenance
- Background cleanup via management command
- Manual cleanup via API endpoint
- Automatic cleanup during deletion attempts
- Preserves audit trail (payments marked as CANCELLED, not deleted)

## Error Message Patterns

### Recent Pending Payment (< 30 minutes)
```
"Cart has pending payment(s). Please wait {X} more minute(s) before deletion or complete the payment."
```

### Multiple Pending Payments
```
"Cart has 3 pending payment(s). Please wait 15 more minute(s) before deletion or complete the payments."
```

### Edge Cases
- **0 minutes remaining**: "Cart has pending payment(s). Please wait less than 1 minute before deletion."
- **Just expired**: Auto-cleanup triggers and allows immediate deletion
- **Network delays**: Graceful handling of timing edge cases

## Production Deployment

### 1. Cron Job Setup (Optional)
```bash
# Run every 15 minutes to clean up old payments
*/15 * * * * /path/to/python /path/to/manage.py cleanup_old_pending_payments
```

### 2. Monitoring & Alerts
- Track auto-cleanup frequency
- Monitor payment abandonment rates
- Alert on unusually high pending payment counts

### 3. Performance Considerations
- Cleanup queries are indexed on `status` and `created_at`
- Batch processing for large cleanup operations
- Minimal API response payload for frequent status checks

## Testing Scenarios Covered

✅ **Fresh pending payment**: Shows exact wait time
✅ **Old pending payment**: Auto-cleanup and immediate deletion
✅ **Multiple payments**: Handles mixed ages correctly
✅ **No payments**: Immediate deletion allowed
✅ **Failed payments**: Immediate deletion allowed
✅ **Converted cart**: Special handling for completed bookings
✅ **Edge case timing**: Handles minute boundaries correctly
✅ **API consistency**: All endpoints return consistent error formats

This implementation provides a much better user experience with clear, actionable error messages and automatic cleanup of abandoned payments while maintaining data integrity.
