from rest_framework import permissions


class IsParent(permissions.BasePermission):
    """
    Check if user is a parent
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'parent'


class CanEditParent(permissions.BasePermission):
    """
    Check if user can edit parent profile
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Parent can view/update own profile
        if request.user == obj.user:
            # For updates, check restricted fields
            if request.method in ['PUT', 'PATCH']:
                restricted_fields = ['parent_id', 'is_verified', 'user', 'parent_type']
                for field in restricted_fields:
                    if field in request.data:
                        return False
            return True
        
        # Admin/Principal can do anything
        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff