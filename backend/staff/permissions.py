from rest_framework import permissions


class IsAdminOrPrincipal(permissions.BasePermission):
    """
    Permission for admin and principal users.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class CanManageStaff(permissions.BasePermission):
    """
    Permission to manage staff records.
    Only admin/principal can create/update/delete staff.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user.role in allowed_roles or request.user.is_staff

        # All staff can view staff directory (excluding sensitive info)
        return request.user.is_authenticated


class CanViewStaffDetails(permissions.BasePermission):
    """
    Permission to view detailed staff information.
    Staff can view their own details, admin can view all.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Staff can view their own profile
        if obj.user == request.user:
            return True

        # Admin/Principal can view all staff
        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class CanEditStaffProfile(permissions.BasePermission):
    """
    Permission to edit staff profiles.
    Staff can edit limited fields of their own profile.
    Admin can edit all fields.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Staff can edit limited fields of their own profile
        if obj.user == request.user and request.method in ['PUT', 'PATCH']:
            # Define allowed fields for self-editing
            allowed_fields = [
                'phone_number', 'alternative_phone', 'profile_picture',
                'address', 'city', 'bank_name', 'account_name', 'account_number',
                'next_of_kin_name', 'next_of_kin_relationship', 'next_of_kin_phone',
                'next_of_kin_address', 'medical_conditions'
            ]

            # Check if only allowed fields are being updated
            for field in request.data.keys():
                if field not in allowed_fields and field != 'user':
                    return False
            return True

        # Admin/Principal can edit any staff profile
        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class CanManageTeacherProfile(permissions.BasePermission):
    """
    Permission to manage teacher profiles.
    Only admin/principal can create/update teacher profiles.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user.role in allowed_roles or request.user.is_staff

        # Teachers can view their own profile and profiles of colleagues in their department
        return request.user.is_authenticated and request.user.role not in ['student', 'parent']


class CanManageAttendance(permissions.BasePermission):
    """
    Permission to manage staff attendance.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal', 'secretary']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user.role in allowed_roles or request.user.is_staff

        # All staff can view attendance records (with appropriate filters)
        return request.user.is_authenticated and request.user.role not in ['student', 'parent']


class CanViewOwnAttendance(permissions.BasePermission):
    """
    Permission for staff to view their own attendance.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Staff can view their own attendance
        if obj.staff.user == request.user:
            return True

        # Admin/Principal/Secretary can view all attendance
        allowed_roles = ['head', 'principal', 'vice_principal', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff


class CanManagePermissions(permissions.BasePermission):
    """
    Permission to manage staff permissions.
    Only admin/principal can manage permissions.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user.role in allowed_roles or request.user.is_staff

        # Admin/Principal can view permissions
        return request.user.role in allowed_roles or request.user.is_staff


class IsTeachingStaff(permissions.BasePermission):
    """
    Permission for teaching staff only.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        teaching_roles = ['teacher', 'form_teacher', 'subject_teacher',
                          'head', 'principal', 'vice_principal']
        return request.user.role in teaching_roles


class IsNonTeachingStaff(permissions.BasePermission):
    """
    Permission for non-teaching staff only.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        non_teaching_roles = ['accountant', 'secretary', 'librarian',
                              'laboratory', 'security', 'cleaner']
        return request.user.role in non_teaching_roles


class CanViewSalaryInfo(permissions.BasePermission):
    """
    Permission to view salary information.
    Staff can view their own salary, admin/accountant can view all.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Staff can view their own salary
        if obj.user == request.user:
            return True

        # Admin/Accountant can view all salaries
        allowed_roles = ['head', 'principal', 'vice_principal', 'accountant']
        return request.user.role in allowed_roles or request.user.is_staff


class CanManageLeave(permissions.BasePermission):
    """
    Permission to manage staff leave.
    Staff can apply for their own leave.
    Admin can approve/manage all leave.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Staff can apply for their own leave
        if request.method == 'POST' and 'staff' in request.data:
            try:
                from staff.models import Staff
                staff = Staff.objects.get(pk=request.data['staff'])
                if staff.user == request.user:
                    return True
            except:
                pass

        # Admin/Principal can manage all leave
        allowed_roles = ['head', 'principal', 'vice_principal', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff