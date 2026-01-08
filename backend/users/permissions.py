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


class IsAccountant(permissions.BasePermission):
    """
    Permission for accountant-specific actions.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'accountant' or request.user.is_staff


class IsSecretary(permissions.BasePermission):
    """
    Permission for secretary-specific actions.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'secretary' or request.user.is_staff


class IsTeachingStaff(permissions.BasePermission):
    """
    Permission for all teaching staff.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        teaching_roles = ['teacher', 'form_teacher', 'subject_teacher']
        return request.user.role in teaching_roles


class IsSupportStaff(permissions.BasePermission):
    """
    Permission for support staff.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        support_roles = ['librarian', 'laboratory', 'security', 'cleaner']
        return request.user.role in support_roles


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Allow users to edit their own profile or admin to edit any.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Users can view/update their own profile
        if obj == request.user:
            return True

        # Admin/Principal can edit anyone
        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff