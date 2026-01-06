from rest_framework import permissions

class IsAdminOrPrincipal(permissions.BasePermission):
    """
    Custom permission to only allow admin or principal users.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Allow admin/principal/head of school
        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class IsTeacherOrAbove(permissions.BasePermission):
    """
    Custom permission to only allow teachers and above.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        allowed_roles = [
            'head', 'principal', 'vice_principal',
            'teacher', 'form_teacher', 'subject_teacher'
        ]
        return request.user.role in allowed_roles


class IsStudent(permissions.BasePermission):
    """
    Custom permission to only allow students.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'student'


class IsParent(permissions.BasePermission):
    """
    Custom permission to only allow parents.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'parent'


class CanChangePassword(permissions.BasePermission):
    """
    Permission to check if user can change password.
    Only admin/principal can change passwords.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.can_change_password()