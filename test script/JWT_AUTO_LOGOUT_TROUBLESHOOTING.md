# JWT Auto-Logout Troubleshooting Guide

## Analysis Results

Your JWT refresh token functionality is **working correctly** on the backend. The issue is likely in the frontend implementation or configuration.

## Key Findings

✅ **Working Correctly:**
- Refresh tokens are being generated properly
- Token rotation is enabled and working
- Token blacklisting is functioning
- Access tokens expire in 1 hour
- Refresh tokens expire in 7 days

⚠️ **Potential Issues:**
- Token rotation with blacklisting requires careful frontend handling
- Multiple tabs can cause auto-logout if not handled properly
- Network interruptions during token refresh can cause issues

## Common Causes of Auto-Logout

### 1. Frontend Token Handling Issues
**Problem:** Frontend not properly handling token refresh
**Solution:** Implement axios interceptors with proper error handling

### 2. Multiple Tab Conflicts
**Problem:** Token rotation causes old refresh tokens to be blacklisted
**Solution:** Use broadcast channels or localStorage events to sync tokens across tabs

### 3. Network Connectivity Issues
**Problem:** Failed refresh requests due to network issues
**Solution:** Implement retry logic with exponential backoff

### 4. Token Storage Problems
**Problem:** Tokens being cleared unexpectedly from localStorage
**Solution:** Add error handling and fallback mechanisms

### 5. Clock Synchronization
**Problem:** Server and client clocks are out of sync
**Solution:** Add buffer time when checking token expiry

## Recommended Solutions

### 1. Implement Proper Frontend Token Management

```javascript
// Use the provided frontend_token_solution.js file
// Key features:
// - Automatic token refresh
// - Queue failed requests during refresh
// - Handle token rotation properly
// - Sync across multiple tabs
```

### 2. Add Debug Logging

```javascript
// Add to your frontend
const DEBUG_TOKENS = process.env.NODE_ENV === 'development';

if (DEBUG_TOKENS) {
    console.log('Token refresh attempt:', new Date());
    console.log('Access token expires:', tokenExpiry);
    console.log('Refresh token available:', !!refreshToken);
}
```

### 3. Backend Configuration Adjustments

If auto-logout continues, consider these backend changes:

```python
# Option 1: Disable token rotation (less secure but easier to handle)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,  # Disable rotation
    'BLACKLIST_AFTER_ROTATION': False,  # Disable blacklisting
}

# Option 2: Increase access token lifetime (less secure)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=4),  # Longer access token
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Option 3: Use sliding tokens (simpler pattern)
SIMPLE_JWT = {
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.SlidingToken',),
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=4),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}
```

### 4. Add Token Refresh Endpoint Monitoring

```python
# Add to your views.py for debugging
import logging

logger = logging.getLogger(__name__)

class TokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        logger.info(f"Token refresh attempt from {request.META.get('REMOTE_ADDR')}")
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info("Token refresh successful")
        else:
            logger.warning(f"Token refresh failed: {response.data}")
        return response
```

## Testing Your Implementation

### 1. Run the Diagnostic Script
```bash
python test_auto_logout_diagnosis.py
```

### 2. Monitor Network Tab
- Check for 401 responses
- Verify refresh token requests
- Look for failed API calls

### 3. Check Browser Console
- Look for JavaScript errors
- Check token storage operations
- Monitor token refresh attempts

### 4. Test Multiple Scenarios
- Page refresh
- Multiple tabs
- Network disconnection
- Long idle periods

## Production Checklist

- [ ] Implement proper token refresh logic
- [ ] Add error handling for failed refreshes
- [ ] Test with multiple browser tabs
- [ ] Verify token storage persistence
- [ ] Add user-friendly error messages
- [ ] Monitor token refresh success rates
- [ ] Set up proper logging and alerting

## Quick Fix for Immediate Relief

If you need an immediate solution, temporarily disable token rotation:

```python
# In settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,  # Temporary fix
    'BLACKLIST_AFTER_ROTATION': False,  # Temporary fix
}
```

This is less secure but will eliminate multi-tab auto-logout issues while you implement proper frontend handling.

## Need Further Help?

If auto-logout persists after implementing these solutions:

1. Check server logs for 401/403 errors
2. Monitor database for token blacklist entries
3. Verify frontend token refresh implementation
4. Test API endpoints with Postman
5. Check browser developer tools for storage issues

The backend JWT implementation is solid - the issue is almost certainly in the frontend token handling.
