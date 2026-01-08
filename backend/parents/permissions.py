from rest_framework import permissions
from django.db import models


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
                restricted_fields = [
                    'parent_id', 'is_verified', 'user',
                    'parent_type', 'annual_income_range',
                    'bank_details', 'pta_position'
                ]
                for field in restricted_fields:
                    if field in request.data:
                        return False
            return True

        # Admin/Principal can do anything
        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class CanViewParentInfo(permissions.BasePermission):
    """
    Permission to view parent information.
    Teachers can view parents of students in their classes.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admin/Principal can view all
        admin_roles = ['head', 'principal', 'vice_principal']
        if request.user.role in admin_roles or request.user.is_staff:
            return True

        # Teachers can view parents of their students
        if request.user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            return True

        # Accountant/Secretary can view for administrative purposes
        if request.user.role in ['accountant', 'secretary']:
            return True

        return False


class CanAddParent(permissions.BasePermission):
    """
    Permission to add new parents.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal',
                         'teacher', 'form_teacher', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff


class CanViewChildrenInfo(permissions.BasePermission):
    """
    Permission to view children information.
    Parents can only view their own children.
    Staff can view children they are authorized to see.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Everyone who is authenticated can access this endpoint
        # Object-level permissions will handle detailed access control
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Parent can view their own children
        if request.user.role == 'parent':
            from students.models import Student
            try:
                parent = request.user.parent_profile
                return obj.father == parent or obj.mother == parent
            except:
                return False

        # Admin/Principal can view all
        admin_roles = ['head', 'principal', 'vice_principal']
        if request.user.role in admin_roles or request.user.is_staff:
            return True

        # Class teacher can view students in their class
        if request.user.role in ['teacher', 'form_teacher']:
            # Check if teacher is class teacher for this student
            from staff.models import TeacherProfile
            try:
                teacher_profile = request.user.staff_profile.teacher_profile
                return teacher_profile.is_class_teacher_of(obj)
            except:
                return False

        # Subject teacher can view students they teach
        if request.user.role == 'subject_teacher':
            # Check if teacher teaches this student
            # This would require checking the student's subjects and teachers
            pass

        return False


class CanManagePTA(permissions.BasePermission):
    """
    Permission to manage PTA information.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Only admin/principal can manage PTA information
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            allowed_roles = ['head', 'principal', 'vice_principal']
            return request.user.role in allowed_roles or request.user.is_staff

        # All staff can view PTA information
        return request.user.is_authenticated and request.user.role not in ['student', 'parent']


class CanViewFeeInformation(permissions.BasePermission):
    """
    Permission to view fee information.
    Parents can only view their own children's fee information.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Parents can access fee endpoints
        if request.user.role == 'parent':
            return True

        # Staff with financial permissions can access
        allowed_roles = ['head', 'principal', 'vice_principal',
                         'accountant', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Parent can view their child's fee information
        if request.user.role == 'parent':
            from students.models import Student
            try:
                parent = request.user.parent_profile
                return obj.father == parent or obj.mother == parent
            except:
                return False

        # Financial staff can view all
        allowed_roles = ['head', 'principal', 'vice_principal',
                         'accountant', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff


class CanCommunicateWithParents(permissions.BasePermission):
    """
    Permission to send communications to parents.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal',
                         'teacher', 'form_teacher', 'secretary']

        if request.method == 'POST':  # Sending communication
            return request.user.role in allowed_roles or request.user.is_staff

        # All staff can view communications
        return request.user.is_authenticated and request.user.role not in ['student']


class IsParentOfStudent(permissions.BasePermission):
    """
    Check if user is parent of a specific student.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # This permission is typically used with object-level checks
        return request.user.role == 'parent'

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.role != 'parent':
            return False

        from students.models import Student
        try:
            parent = request.user.parent_profile
            # Check if obj is a Student and parent is father/mother
            if isinstance(obj, Student):
                return obj.father == parent or obj.mother == parent

            # Check if obj has a student relationship
            if hasattr(obj, 'student'):
                student = obj.student
                return student.father == parent or student.mother == parent

            # Check if obj has a user that is a student
            if hasattr(obj, 'user') and hasattr(obj.user, 'student_profile'):
                student = obj.user.student_profile
                return student.father == parent or student.mother == parent
        except:
            return False

        return False