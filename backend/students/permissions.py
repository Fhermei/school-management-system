from rest_framework import permissions
from django.db import models


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
        allowed_roles = ['accountant', 'secretary', 'head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class IsTeachingStaff(permissions.BasePermission):
    """Allow teaching staff"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        allowed_roles = ['teacher', 'form_teacher', 'subject_teacher',
                         'head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles


class CanEditStudent(permissions.BasePermission):
    """Check if user can edit student profile"""

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Student can view their own profile (read-only)
        if request.user == obj.user and request.method in permissions.SAFE_METHODS:
            return True

        # Parent can view their child's profile (read-only)
        from parents.models import Parent
        try:
            parent = request.user.parent_profile
            if obj.father == parent or obj.mother == parent:
                return request.method in permissions.SAFE_METHODS
        except:
            pass

        # Admin/Principal/Accountant/Secretary can do anything
        allowed_roles = ['head', 'principal', 'vice_principal', 'accountant', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff


class CanEditFee(permissions.BasePermission):
    """Only admin/accountant can edit fee information"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Check if this is a fee-related endpoint
        fee_related_actions = ['update_fee', 'add_payment', 'generate_receipt']
        if view.action in fee_related_actions:
            allowed_roles = ['head', 'principal', 'vice_principal', 'accountant']
            return request.user.role in allowed_roles or request.user.is_staff

        return True


class CanViewStudentRecords(permissions.BasePermission):
    """
    Permission to view student records.
    Teachers can view students in their classes.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admin/Principal can view all
        admin_roles = ['head', 'principal', 'vice_principal']
        if request.user.role in admin_roles or request.user.is_staff:
            return True

        # Teachers can view students in their classes
        if request.user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            return True

        # Accountant/Secretary can view for administrative purposes
        if request.user.role in ['accountant', 'secretary']:
            return True

        return False


class CanManageAttendance(permissions.BasePermission):
    """
    Permission to manage student attendance.
    Class teachers can manage attendance for their classes.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admin/Principal can manage all attendance
        admin_roles = ['head', 'principal', 'vice_principal']
        if request.user.role in admin_roles or request.user.is_staff:
            return True

        # Class teachers can manage attendance for their classes
        if request.user.role in ['teacher', 'form_teacher']:
            return True

        return False


class IsStudentOrParent(permissions.BasePermission):
    """
    Permission for students or parents to access their own information.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in ['student', 'parent']


class CanPromoteStudent(permissions.BasePermission):
    """
    Permission to promote students to next class.
    Only admin/principal can promote students.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class CanManageStudentEnrollment(permissions.BasePermission):
    """
    Permission to manage student enrollments.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal', 'secretary']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user.role in allowed_roles or request.user.is_staff

        # Teachers can view enrollments for their classes
        if request.method == 'GET':
            view_roles = ['head', 'principal', 'vice_principal',
                          'teacher', 'form_teacher', 'secretary']
            return request.user.role in view_roles

        return False