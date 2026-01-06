from rest_framework import permissions

class IsAdminOrPrincipal(permissions.BasePermission):
    """Allow only admin/principal/vice principal"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class IsAccountantOrSecretary(permissions.BasePermission):
    """Allow accountant/secretary for fee-related actions"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        allowed_roles = ['accountant', 'secretary', 'head', 'principal']
        return request.user.role in allowed_roles or request.user.is_staff


class CanEditStudent(permissions.BasePermission):
    """Check if user can edit student profile"""
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Student can view their own profile
        if request.user == obj.user and request.method in permissions.SAFE_METHODS:
            return True
        
        # Parent can view their child's profile
        from parents.models import Parent
        try:
            parent = request.user.parent_profile
            if obj.father == parent or obj.mother == parent:
                return request.method in permissions.SAFE_METHODS
        except:
            pass
        
        # Admin/Principal can do anything
        allowed_roles = ['head', 'principal', 'vice_principal', 'accountant', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff


class CanEditFee(permissions.BasePermission):
    """Only admin/accountant can edit fee information"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        allowed_roles = ['head', 'principal', 'vice_principal', 'accountant', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff