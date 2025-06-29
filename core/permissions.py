from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.conf import settings
from accounts.models import User

class IsActiveUser(BasePermission):
    """Base permission allowing only active users"""
    message = "Your account is not active or requires verification"
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and
            request.user.account_status == User.AccountStatus.ACTIVE
        )

# Role-Based Permissions
class IsAdminUser(IsActiveUser):
    """Admin-only access"""
    message = "Administrator privileges required"
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == User.Role.ADMIN

class IsEmployeeUser(IsActiveUser):
    """Employee-only access (includes priests)"""
    message = "Employee account required"
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == User.Role.EMPLOYEE

class IsPublicUser(IsActiveUser):
    """Public user-only access"""
    message = "Public user account required"
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == User.Role.USER

# Combined Role Permissions
class IsStaffUser(IsActiveUser):
    """Employee or Admin access"""
    message = "Staff privileges required"
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in [
            User.Role.EMPLOYEE, 
            User.Role.ADMIN
        ]

class IsEmployeeOrPublicUser(IsActiveUser):
    """Employee or Public user access"""
    message = "Employee or public user account required"
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in [
            User.Role.EMPLOYEE,
            User.Role.USER
        ]

# Object-Level Permissions
class IsOwnerOrReadOnly(IsActiveUser):
    """Read access for all, write only for owners"""
    message = "You must be the owner to perform this action"
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
            
        owner = getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        return owner == request.user

class IsOwner(IsActiveUser):
    """Strict ownership requirement"""
    message = "You must be the owner to access this"
    
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        return owner == request.user

class IsOwnerOrStaff(IsActiveUser):
    """Owner or staff can modify"""
    message = "You must be the owner or staff to perform this action"
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
            
        owner = getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        return owner == request.user or request.user.role in [User.Role.EMPLOYEE, User.Role.ADMIN]

# Special Case Permissions
class IsAdminOrEmployeeReadOnly(BasePermission):
    """Admin has full access, employees have read-only"""
    message = "Administrator access required for modifications"
    
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == User.Role.ADMIN:
                return True
            if request.user.role == User.Role.EMPLOYEE and request.method in SAFE_METHODS:
                return True
        return False

# Utility Permissions
class ReadOnly(BasePermission):
    """Global read-only permission"""
    message = "Read-only access allowed"
    
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

class HasVerifiedEmail(IsActiveUser):
    """Requires verified email"""
    message = "Email verification required"
    
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.email_verified

class ActionBasedPermissionMixin:
    """
    Dynamically switches permissions based on action
    Example:
    permission_classes_by_action = {
        'list': [IsAuthenticated],
        'create': [IsAdminUser],
        'retrieve': [IsOwnerOrReadOnly],
        'update': [IsOwnerOrStaff],
        'destroy': [IsAdminUser]
    }
    """
    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except (KeyError, AttributeError):
            return [permission() for permission in self.permission_classes]