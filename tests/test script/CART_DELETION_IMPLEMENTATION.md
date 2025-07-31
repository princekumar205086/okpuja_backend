# Cart Deletion and Single-Cart System Implementation

## Problem Solved
- **ProtectedError**: Could not delete carts due to `on_delete=models.PROTECT` on Payment.cart field
- **Multi-cart confusion**: Users had multiple active carts simultaneously
- **Payment-first flow**: Need proper cart → payment → booking flow with cleanup

## Solution Overview

### 1. Payment Model Changes
```python
# Changed from PROTECT to SET_NULL with nullable field
cart = models.ForeignKey(
    'cart.Cart',
    on_delete=models.SET_NULL,  # Changed from PROTECT
    related_name="payments",
    null=True,                  # Added nullable
    blank=True,                 # Added blank
    help_text="Cart being purchased (can be cleared after successful booking)"
)
```

### 2. Single-Cart System Implementation
- **Automatic deactivation**: When user creates new cart, previous active carts become INACTIVE
- **One active cart rule**: Each user can have maximum 1 ACTIVE cart at any time
- **Cart status flow**: ACTIVE → CONVERTED → (deleted after successful booking)

### 3. Safe Cart Deletion Logic
```python
def can_be_deleted(self):
    """Check if cart can be safely deleted"""
    # Cart can be deleted if:
    # 1. No payments exist, OR
    # 2. All payments are FAILED/CANCELLED, OR  
    # 3. Cart is CONVERTED and has successful booking
```

### 4. Payment-First Flow
```
User Flow:
1. Add to Cart (ACTIVE status)
2. Checkout → Create Payment (cart still ACTIVE)
3. Payment Success → Create Booking + Mark cart as CONVERTED + Clear cart reference
4. Cart can now be safely deleted
```

## API Endpoints

### Enhanced Cart Endpoints
- `GET /api/cart/carts/{id}/deletion_status/` - Check if cart can be deleted
- `DELETE /api/cart/carts/{id}/` - Safe deletion with proper error handling
- `POST /api/cart/carts/clear_converted/` - Bulk clear converted carts
- `GET /api/cart/carts/active/` - Get user's single active cart

### Example API Responses

#### Deletion Status Check
```json
{
    "can_delete": false,
    "cart_status": "ACTIVE", 
    "payments_count": 1,
    "payments": [
        {
            "transaction_id": "TXN123",
            "status": "PENDING",
            "amount": "5000.00",
            "created_at": "2025-07-20T10:00:00Z",
            "has_booking": false
        }
    ],
    "reasons": [
        "1 pending payments prevent deletion"
    ]
}
```

#### Safe Deletion Success
```json
HTTP 204 No Content
```

#### Deletion Blocked
```json
{
    "error": "Cannot delete cart with pending payments",
    "detail": "This cart has pending payments. Please wait for payment completion or cancellation.",
    "can_delete": false
}
```

## Management Commands

### 1. Clean Converted Carts
```bash
# Dry run to see what would be cleaned
python manage.py clean_converted_carts --dry-run

# Actually clean up cart references
python manage.py clean_converted_carts

# Force cleanup (careful!)
python manage.py clean_converted_carts --force
```

### 2. Fix Single Cart Rule
```bash
# Enforce single active cart per user
python manage.py fix_single_cart

# Dry run first
python manage.py fix_single_cart --dry-run
```

## Database Changes
- Payment.cart field changed from PROTECT to SET_NULL
- Migration created and applied: `payment/migrations/0003_alter_payment_cart.py`

## Key Features

### 1. Graceful Error Handling
- No more ProtectedError crashes
- Clear error messages explaining why deletion failed
- Helpful suggestions for resolution

### 2. Automatic Cleanup
- Cart references cleared after successful booking
- Payment history preserved even after cart deletion
- Converted carts can be safely removed

### 3. Single-Cart UX
- Users focus on one service booking at a time
- No confusion with multiple carts
- Previous carts become inactive, not deleted

### 4. Admin Tools
- Management commands for data cleanup
- Detailed deletion status endpoint for debugging
- Bulk operations for converted cart cleanup

## Deployment Notes

1. **Run migrations**: `python manage.py migrate`
2. **Clean existing data**: 
   ```bash
   python manage.py clean_converted_carts
   python manage.py fix_single_cart
   ```
3. **Test deletion**: Use `/deletion_status/` endpoint to verify
4. **Monitor**: Check for any remaining ProtectedError issues

## Business Logic Benefits

### For Puja/Astrology Platform:
- **Simplified UX**: One booking at a time matches user behavior
- **Clear payment flow**: Cart → Payment → Booking → Cleanup
- **Data integrity**: Payment history preserved, references cleaned
- **Flexible deletion**: Users can clear carts when needed

### Prevention of Issues:
- ✅ No more ProtectedError crashes
- ✅ No multiple active carts confusion  
- ✅ Clean payment-booking relationship
- ✅ Proper cart lifecycle management
- ✅ Safe data cleanup without losing payment history

This implementation provides a robust, user-friendly cart system suitable for service booking platforms while maintaining data integrity and payment audit trails.
