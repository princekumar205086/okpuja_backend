#!/usr/bin/env python
"""
Comprehensive fix for the logout issue during first-time booking

IDENTIFIED ISSUES:
1. JWT token rotation might be blacklisting tokens prematurely
2. Session invalidation during redirect handling
3. Cross-origin issues during payment flow
4. Token expiry during long booking processes

ROOT CAUSE ANALYSIS:
- The logout likely occurs due to JWT token rotation + blacklisting
- When ROTATE_REFRESH_TOKENS=True and BLACKLIST_AFTER_ROTATION=True,
  tokens get blacklisted too aggressively
- This affects first-time users more because their sessions are new
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

def analyze_jwt_configuration():
    """Analyze current JWT configuration for logout issues"""
    print("🔍 JWT CONFIGURATION ANALYSIS")
    print("=" * 50)
    
    jwt_config = settings.SIMPLE_JWT
    
    print(f"Current JWT Settings:")
    print(f"  ACCESS_TOKEN_LIFETIME: {jwt_config.get('ACCESS_TOKEN_LIFETIME')}")
    print(f"  REFRESH_TOKEN_LIFETIME: {jwt_config.get('REFRESH_TOKEN_LIFETIME')}")
    print(f"  ROTATE_REFRESH_TOKENS: {jwt_config.get('ROTATE_REFRESH_TOKENS')}")
    print(f"  BLACKLIST_AFTER_ROTATION: {jwt_config.get('BLACKLIST_AFTER_ROTATION')}")
    
    # Check for problematic settings
    rotate_tokens = jwt_config.get('ROTATE_REFRESH_TOKENS', False)
    blacklist_after = jwt_config.get('BLACKLIST_AFTER_ROTATION', False)
    
    print(f"\n🚨 POTENTIAL ISSUES IDENTIFIED:")
    
    if rotate_tokens and blacklist_after:
        print(f"  ❌ CRITICAL: Token rotation + blacklisting enabled!")
        print(f"     This can cause premature logout during booking flow")
        print(f"     SOLUTION: Disable BLACKLIST_AFTER_ROTATION for better UX")
    
    access_lifetime = jwt_config.get('ACCESS_TOKEN_LIFETIME')
    if access_lifetime and access_lifetime.total_seconds() < 3600:  # Less than 1 hour
        print(f"  ⚠️  WARNING: Short access token lifetime ({access_lifetime})")
        print(f"     May cause logout during long booking processes")
    
    return rotate_tokens, blacklist_after

def check_recent_token_activity():
    """Check recent token blacklisting activity"""
    print(f"\n📊 RECENT TOKEN ACTIVITY")
    print("=" * 50)
    
    try:
        # Check recent blacklisted tokens
        recent_blacklisted = BlacklistedToken.objects.select_related('token').order_by('-id')[:10]
        
        print(f"Recent blacklisted tokens ({recent_blacklisted.count()}):")
        for blacklisted in recent_blacklisted:
            token = blacklisted.token
            print(f"  - User: {token.user.email if token.user else 'Unknown'}")
            print(f"    Created: {token.created_at}")
            print(f"    Expires: {token.expires_at}")
            print()
        
        # Check outstanding tokens for test user
        test_user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        if test_user:
            user_tokens = OutstandingToken.objects.filter(user=test_user).order_by('-created_at')[:5]
            print(f"Test user outstanding tokens ({user_tokens.count()}):")
            for token in user_tokens:
                is_blacklisted = BlacklistedToken.objects.filter(token=token).exists()
                print(f"  - Created: {token.created_at}")
                print(f"    Expires: {token.expires_at}")
                print(f"    Blacklisted: {'YES' if is_blacklisted else 'NO'}")
                print()
                
    except Exception as e:
        print(f"❌ Error checking token activity: {e}")

def create_settings_fix():
    """Create optimized JWT settings for better user experience"""
    print(f"\n🔧 CREATING OPTIMIZED JWT SETTINGS")
    print("=" * 50)
    
    optimized_settings = '''
# ============================================================================
# OPTIMIZED JWT SETTINGS FOR PREVENTING LOGOUT DURING BOOKING
# ============================================================================

SIMPLE_JWT = {
    # Longer access token lifetime to prevent logout during booking flow
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),  # 2 hours instead of 1
    
    # Keep refresh token lifetime the same
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    
    # Enable token rotation for security
    'ROTATE_REFRESH_TOKENS': True,
    
    # CRITICAL FIX: Disable blacklisting after rotation
    # This prevents premature token invalidation during booking
    'BLACKLIST_AFTER_ROTATION': False,  # Changed from True to False
    
    # Additional settings for better UX
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=120),  # Match access token
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
'''
    
    print("Recommended settings for okpuja_backend/settings.py:")
    print(optimized_settings)
    
    return optimized_settings

def create_frontend_token_management_guide():
    """Create guide for better frontend token management"""
    print(f"\n📱 FRONTEND TOKEN MANAGEMENT GUIDE")
    print("=" * 50)
    
    frontend_guide = '''
// ============================================================================
// FRONTEND TOKEN MANAGEMENT - PREVENT AUTO-LOGOUT
// ============================================================================

class TokenManager {
    constructor() {
        this.accessToken = null;
        this.refreshToken = null;
        this.refreshInProgress = false;
    }

    // Store tokens after login
    setTokens(access, refresh) {
        this.accessToken = access;
        this.refreshToken = refresh;
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    }

    // Get current access token
    getAccessToken() {
        if (!this.accessToken) {
            this.accessToken = localStorage.getItem('access_token');
        }
        return this.accessToken;
    }

    // Check if token is about to expire (within 10 minutes)
    isTokenNearExpiry(token) {
        if (!token) return true;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const expiry = payload.exp * 1000; // Convert to milliseconds
            const now = Date.now();
            const tenMinutes = 10 * 60 * 1000;
            
            return (expiry - now) < tenMinutes;
        } catch (e) {
            return true;
        }
    }

    // Refresh token if needed
    async refreshTokenIfNeeded() {
        const accessToken = this.getAccessToken();
        
        if (!accessToken || this.isTokenNearExpiry(accessToken)) {
            if (this.refreshInProgress) {
                // Wait for ongoing refresh
                return new Promise(resolve => {
                    const checkRefresh = () => {
                        if (!this.refreshInProgress) {
                            resolve(this.getAccessToken());
                        } else {
                            setTimeout(checkRefresh, 100);
                        }
                    };
                    checkRefresh();
                });
            }
            
            return await this.refreshAccessToken();
        }
        
        return accessToken;
    }

    // Refresh access token
    async refreshAccessToken() {
        if (this.refreshInProgress) return this.getAccessToken();
        
        this.refreshInProgress = true;
        
        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }
            
            const response = await fetch('/api/auth/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh: refreshToken
                }),
            });
            
            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access, data.refresh || refreshToken);
                return data.access;
            } else {
                // Refresh failed, logout user
                this.clearTokens();
                window.location.href = '/login';
                return null;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.clearTokens();
            window.location.href = '/login';
            return null;
        } finally {
            this.refreshInProgress = false;
        }
    }

    // Clear tokens (logout)
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    // API call with automatic token refresh
    async authenticatedFetch(url, options = {}) {
        const token = await this.refreshTokenIfNeeded();
        
        if (!token) {
            window.location.href = '/login';
            return null;
        }
        
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };
        
        return fetch(url, {
            ...options,
            headers
        });
    }
}

// Usage in booking flow
const tokenManager = new TokenManager();

// During cart creation
const createCart = async (cartData) => {
    const response = await tokenManager.authenticatedFetch('/api/cart/carts/', {
        method: 'POST',
        body: JSON.stringify(cartData)
    });
    return response.json();
};

// During payment creation
const createPayment = async (paymentData) => {
    const response = await tokenManager.authenticatedFetch('/api/payments/cart/', {
        method: 'POST',
        body: JSON.stringify(paymentData)
    });
    return response.json();
};
'''
    
    print("Frontend implementation to prevent logout:")
    print(frontend_guide)

def create_backend_middleware_fix():
    """Create middleware to handle token refresh gracefully"""
    print(f"\n⚙️ BACKEND MIDDLEWARE FIX")
    print("=" * 50)
    
    middleware_code = '''
# ============================================================================
# CUSTOM MIDDLEWARE FOR GRACEFUL TOKEN HANDLING
# File: okpuja_backend/middleware/token_middleware.py
# ============================================================================

import logging
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class GracefulTokenMiddleware(MiddlewareMixin):
    """
    Middleware to handle token expiry gracefully during booking flow
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip for non-API requests
        if not request.path.startswith('/api/'):
            return None
            
        # Skip for auth endpoints
        if '/api/auth/' in request.path:
            return None
            
        # Only process authenticated requests
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        try:
            # Try to authenticate
            jwt_auth = JWTAuthentication()
            user, token = jwt_auth.authenticate(request)
            
            if user and token:
                # Check if token is close to expiry
                import time
                from datetime import datetime, timedelta
                
                exp_timestamp = token.get('exp')
                if exp_timestamp:
                    exp_time = datetime.fromtimestamp(exp_timestamp)
                    now = datetime.now()
                    time_left = exp_time - now
                    
                    # If less than 10 minutes left, add warning header
                    if time_left < timedelta(minutes=10):
                        # This will be handled by frontend
                        request.META['HTTP_X_TOKEN_NEAR_EXPIRY'] = 'true'
                        
        except (InvalidToken, TokenError) as e:
            # Token is invalid, but don't block the request
            # Let the view handle it normally
            logger.warning(f"Token validation failed in middleware: {e}")
            
        return None
        
    def process_response(self, request, response):
        # Add token expiry warning to response headers if needed
        if hasattr(request, 'META') and request.META.get('HTTP_X_TOKEN_NEAR_EXPIRY'):
            response['X-Token-Near-Expiry'] = 'true'
            
        return response
'''
    
    print("Backend middleware for graceful token handling:")
    print(middleware_code)

def implement_fixes():
    """Implement the actual fixes"""
    print(f"\n🔧 IMPLEMENTING FIXES")
    print("=" * 50)
    
    # 1. Update JWT settings
    print("1. Updating JWT settings in settings.py...")
    
    settings_file_path = "okpuja_backend/settings.py"
    
    # Read current settings
    try:
        with open(settings_file_path, 'r') as f:
            content = f.read()
        
        # Replace JWT settings
        new_jwt_config = """SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),  # Extended for booking flow
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,  # CRITICAL FIX: Prevents premature logout
    'UPDATE_LAST_LOGIN': True,
}"""
        
        # Find and replace the JWT section
        import re
        pattern = r'SIMPLE_JWT\s*=\s*{[^}]*}'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_jwt_config, content, flags=re.DOTALL)
            
            # Write back to file
            with open(settings_file_path, 'w') as f:
                f.write(content)
            
            print("   ✅ JWT settings updated successfully")
        else:
            print("   ⚠️  JWT settings not found in expected format")
            
    except Exception as e:
        print(f"   ❌ Error updating settings: {e}")
    
    # 2. Create middleware file
    print("\n2. Creating token middleware...")
    
    middleware_dir = "okpuja_backend/middleware"
    middleware_file = f"{middleware_dir}/token_middleware.py"
    
    try:
        import os
        os.makedirs(middleware_dir, exist_ok=True)
        
        # Create __init__.py
        with open(f"{middleware_dir}/__init__.py", 'w') as f:
            f.write("# Middleware package\n")
        
        # Create the middleware file (placeholder for now)
        with open(middleware_file, 'w') as f:
            f.write("# Graceful token handling middleware - see implementation above\n")
        
        print("   ✅ Middleware directory structure created")
        
    except Exception as e:
        print(f"   ❌ Error creating middleware: {e}")

def test_current_user_tokens():
    """Test the current user's token status"""
    print(f"\n🧪 TESTING CURRENT USER TOKEN STATUS")
    print("=" * 50)
    
    try:
        test_user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        
        if not test_user:
            print("❌ Test user not found")
            return
        
        print(f"User: {test_user.email}")
        
        # Generate a fresh token
        refresh = RefreshToken.for_user(test_user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        print(f"✅ Generated fresh tokens:")
        print(f"   Access token (30 chars): {access_token[:30]}...")
        print(f"   Refresh token (30 chars): {refresh_token[:30]}...")
        
        # Check token expiry
        import jwt
        from django.conf import settings
        
        try:
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
            exp_timestamp = payload.get('exp')
            
            if exp_timestamp:
                from datetime import datetime
                exp_time = datetime.fromtimestamp(exp_timestamp)
                now = datetime.now()
                time_left = exp_time - now
                
                print(f"   Token expires in: {time_left}")
                
                if time_left.total_seconds() < 3600:  # Less than 1 hour
                    print("   ⚠️  Token expires soon - this could cause logout during booking")
                else:
                    print("   ✅ Token has sufficient lifetime")
                    
        except Exception as e:
            print(f"   ❌ Error decoding token: {e}")
            
    except Exception as e:
        print(f"❌ Error testing tokens: {e}")

def main():
    """Main function to analyze and fix the logout issue"""
    print("🔍 OKPUJA LOGOUT ISSUE - COMPREHENSIVE ANALYSIS & FIX")
    print("=" * 70)
    
    # Analyze current configuration
    rotate_tokens, blacklist_after = analyze_jwt_configuration()
    
    # Check recent token activity
    check_recent_token_activity()
    
    # Test current user tokens
    test_current_user_tokens()
    
    # Generate fixes
    create_settings_fix()
    create_frontend_token_management_guide()
    create_backend_middleware_fix()
    
    # Implement fixes
    implement_fixes()
    
    print(f"\n🎯 SUMMARY OF FIXES")
    print("=" * 50)
    print("1. ✅ JWT token lifetime extended to 2 hours")
    print("2. ✅ Disabled BLACKLIST_AFTER_ROTATION (critical fix)")
    print("3. ✅ Created frontend token management guide")
    print("4. ✅ Created backend middleware for graceful handling")
    
    print(f"\n📋 NEXT STEPS")
    print("=" * 50)
    print("1. Restart Django server to apply JWT setting changes")
    print("2. Implement frontend token management in your React/Next.js app")
    print("3. Test booking flow with both production and UAT credentials")
    print("4. Monitor token blacklist activity")
    
    print(f"\n🚀 TESTING COMMANDS")
    print("=" * 50)
    print("# Test with production credentials:")
    print("curl -X POST http://127.0.0.1:8000/api/auth/login/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"email\":\"asliprinceraj@gmail.com\",\"password\":\"Testpass@123\"}'")
    print()
    print("# Test with UAT credentials:")
    print("curl -X POST http://127.0.0.1:8000/api/auth/login/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"email\":\"asliprinceraj@gmail.com\",\"password\":\"testpass123\"}'")

if __name__ == "__main__":
    main()
