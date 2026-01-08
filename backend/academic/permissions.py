from rest_framework import permissions


class IsAcademicAdmin(permissions.BasePermission):
    """
    Permission for academic administrators (Head, Principal, Vice Principal, Secretary).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff


class CanManageAcademicStructure(permissions.BasePermission):
    """
    Permission to manage academic structure (Sessions, Terms, Programs, Class Levels).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Only admin/principal can create/update academic structure
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            allowed_roles = ['head', 'principal', 'vice_principal']
            return request.user.role in allowed_roles or request.user.is_staff

        # All staff can view academic structure
        return request.user.is_authenticated and request.user.role not in ['student', 'parent']


class CanManageSubjects(permissions.BasePermission):
    """
    Permission to manage subjects.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Only teaching staff and above can manage subjects
        allowed_roles = ['head', 'principal', 'vice_principal',
                         'teacher', 'form_teacher', 'subject_teacher']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Only admin/principal can create/delete subjects
            admin_roles = ['head', 'principal', 'vice_principal']
            return request.user.role in admin_roles or request.user.is_staff

        # All teaching staff can view subjects
        return request.user.role in allowed_roles


class CanManageClasses(permissions.BasePermission):
    """
    Permission to manage classes.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal', 'secretary']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user.role in allowed_roles or request.user.is_staff

        # All staff can view classes
        return request.user.is_authenticated and request.user.role not in ['student', 'parent']


class CanManageTimetables(permissions.BasePermission):
    """
    Permission to manage timetables.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal', 'secretary']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user.role in allowed_roles or request.user.is_staff

        # Teachers can view timetables
        if request.method == 'GET':
            view_roles = ['head', 'principal', 'vice_principal',
                          'teacher', 'form_teacher', 'subject_teacher',
                          'secretary', 'student', 'parent']
            return request.user.role in view_roles

        return False


class CanViewTimetable(permissions.BasePermission):
    """
    Permission to view timetables.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # All authenticated users can view timetables (with appropriate filters)
        return request.user.is_authenticated


class CanEditTimetable(permissions.BasePermission):
    """
    Permission to edit timetables.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal', 'secretary']
        return request.user.role in allowed_roles or request.user.is_staff


class CanViewClassInformation(permissions.BasePermission):
    """
    Permission to view class information.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # All staff can view class information
        if request.user.role not in ['student', 'parent']:
            return True

        # Students and parents need object-level permission
        return True

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Staff can view all classes
        if request.user.role not in ['student', 'parent']:
            return True

        # Students can view their own class
        if request.user.role == 'student':
            from students.models import StudentEnrollment
            return StudentEnrollment.objects.filter(
                student=request.user,
                class_obj=obj,
                status='active'
            ).exists()

        # Parents can view their children's classes
        if request.user.role == 'parent':
            try:
                parent = request.user.parent_profile
                children = parent.get_children()
                from students.models import StudentEnrollment
                return StudentEnrollment.objects.filter(
                    student__in=[child.user for child in children],
                    class_obj=obj,
                    status='active'
                ).exists()
            except:
                return False

        return False


class CanManageStudentEnrollment(permissions.BasePermission):
    """
    Permission to manage student enrollments.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal',
                         'teacher', 'form_teacher', 'secretary']

        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            admin_roles = ['head', 'principal', 'vice_principal', 'secretary']
            return request.user.role in admin_roles or request.user.is_staff

        return request.user.role in allowed_roles


class CanViewStudentEnrollment(permissions.BasePermission):
    """
    Permission to view enrollment records.
    Students can only view their own enrollments.
    Parents can view their children's enrollments.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Staff can view all
        if request.user.role not in ['student', 'parent']:
            return True

        # Students can view their own
        if request.user.role == 'student' and obj.student == request.user:
            return True

        # Parents can view their children's
        if request.user.role == 'parent':
            from students.models import Student
            try:
                parent = request.user.parent_profile
                children = Student.objects.filter(
                    models.Q(father=parent) | models.Q(mother=parent)
                )
                student_users = [child.user for child in children]
                return obj.student in student_users
            except:
                pass

        return False


class CanAssignTeachersToSubjects(permissions.BasePermission):
    """
    Permission to assign teachers to subjects.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class CanViewSubjectInformation(permissions.BasePermission):
    """
    Permission to view subject information.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # All authenticated users can view subjects
        return request.user.is_authenticated


class IsSubjectTeacher(permissions.BasePermission):
    """
    Permission for subject teachers.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in ['subject_teacher', 'teacher', 'form_teacher',
                                     'head', 'principal', 'vice_principal']


class CanCreateClassSubjectAssignment(permissions.BasePermission):
    """
    Permission to create class-subject assignments.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff


class CanEditOwnClassSubjectAssignment(permissions.BasePermission):
    """
    Permission for teachers to edit their own class-subject assignments.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Admin can edit any assignment
        if request.user.role in ['head', 'principal', 'vice_principal'] or request.user.is_staff:
            return True

        # Teachers can edit their own assignments
        if request.user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            return obj.teacher == request.user or obj.co_teacher == request.user

        return False


class AcademicHierarchyPermission(permissions.BasePermission):
    """
    Permission based on academic hierarchy.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Head can do everything
        if request.user.role == 'head':
            return True

        # Principal can do everything except manage Head
        if request.user.role == 'principal':
            return True

        # Vice Principal can manage below their level
        if request.user.role == 'vice_principal':
            return True

        return False


class IsClassTeacher(permissions.BasePermission):
    """
    Permission for class teachers to manage their own class.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Check if user is class teacher of this class
        if hasattr(obj, 'class_teacher') and obj.class_teacher == request.user:
            return True

        # Check if user is assistant class teacher
        if hasattr(obj, 'assistant_class_teacher') and obj.assistant_class_teacher == request.user:
            return True

        # Admin override
        admin_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in admin_roles or request.user.is_staff


class CanAssignClassTeacher(permissions.BasePermission):
    """
    Permission to assign class teachers.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Only admin/principal can assign class teachers
        allowed_roles = ['head', 'principal', 'vice_principal']
        return request.user.role in allowed_roles or request.user.is_staff