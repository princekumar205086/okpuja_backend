# Enhanced JWT Configuration for Auto-Logout Prevention
# Add this to your settings.py file to replace the existing SIMPLE_JWT configuration

from datetime import timedelta

# Enhanced JWT Configuration
SIMPLE_JWT = {
    # Token lifetimes
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 1 hour access token
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # 7 days refresh token
    
    # Token rotation and security
    'ROTATE_REFRESH_TOKENS': True,                   # Generate new refresh token on each refresh
    'BLACKLIST_AFTER_ROTATION': True,               # Blacklist old refresh tokens
    
    # Algorithm and signing
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': None,  # Uses SECRET_KEY by default
    'VERIFYING_KEY': None,
    
    # Token claims
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    # Token types
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    # JTI (JWT ID) for unique identification
    'JTI_CLAIM': 'jti',
    
    # Token validation
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Sliding tokens (alternative to access/refresh pattern)
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    
    # Token update on last activity
    'UPDATE_LAST_LOGIN': True,  # Update last_login field on token generation
}
