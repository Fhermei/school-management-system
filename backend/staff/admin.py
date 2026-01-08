from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Staff, TeacherProfile, StaffAttendance, StaffPermission


class TeacherProfileInline(admin.StackedInline):
    """Inline for TeacherProfile in Staff admin"""
    model = TeacherProfile
    extra = 0
    can_delete = False
    fields = ('teacher_type', 'subjects', 'stream_specialization',
              'class_levels', 'max_periods_per_week', 'current_periods_per_week',
              'years_of_experience')
    filter_horizontal = ('subjects', 'class_levels')
    classes = ('collapse',)


class StaffPermissionInline(admin.StackedInline):
    """Inline for StaffPermission in Staff admin"""
    model = StaffPermission
    extra = 0
    can_delete = False
    fieldsets = (
        (None, {
            'fields': ('can_view_all_results', 'can_edit_results', 'can_approve_results', 'can_generate_reports')
        }),
        ('Student Management', {
            'fields': ('can_add_students', 'can_edit_students', 'can_view_all_students'),
            'classes': ('collapse',)
        }),
        ('Parent Management', {
            'fields': ('can_add_parents', 'can_edit_parents'),
            'classes': ('collapse',)
        }),
        ('Staff Management', {
            'fields': ('can_add_staff', 'can_edit_staff', 'can_view_all_staff'),
            'classes': ('collapse',)
        }),
        ('Financial Permissions', {
            'fields': ('can_view_finances', 'can_edit_finances', 'can_generate_financial_reports'),
            'classes': ('collapse',)
        }),
        ('System Administration', {
            'fields': ('can_manage_system_settings', 'can_view_audit_logs', 'can_manage_backups'),
            'classes': ('collapse',)
        }),
        ('Communication Permissions', {
            'fields': ('can_send_broadcast_messages', 'can_send_individual_messages'),
            'classes': ('collapse',)
        }),
    )
    classes = ('collapse',)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    """Admin interface for Staff model"""

    list_display = (
        'staff_id',
        'get_full_name',
        'department',
        'employment_type',
        'is_active_display',
        'employment_date',
    )

    list_filter = (
        'department',
        'employment_type',
        'is_active',
        'is_on_leave',
        'is_retired',
    )

    search_fields = (
        'staff_id',
        'user__first_name',
        'user__last_name',
        'user__email',
        'user__phone_number',
    )

    readonly_fields = (
        'staff_id',
        'created_at',
        'updated_at',
        'leave_days_remaining',
    )

    list_per_page = 50

    fieldsets = (
        ('Staff Information', {
            'fields': ('user', 'staff_id', 'employment_date', 'employment_type')
        }),

        ('Department & Role', {
            'fields': ('department',)
        }),

        ('Qualification', {
            'fields': ('highest_qualification', 'qualification_institution',
                       'year_of_graduation', 'professional_certifications',
                       'trcn_number', 'specialization'),
            'classes': ('collapse',)
        }),

        ('Bank & Salary', {
            'fields': ('bank_name', 'account_name', 'account_number',
                       'basic_salary', 'salary_scale'),
            'classes': ('collapse',)
        }),

        ('Leave Management', {
            'fields': ('annual_leave_days', 'leave_days_taken',
                       'leave_days_remaining', 'is_on_leave',
                       'leave_start_date', 'leave_end_date'),
        }),

        ('Next of Kin', {
            'fields': ('next_of_kin_name', 'next_of_kin_relationship',
                       'next_of_kin_phone', 'next_of_kin_address'),
            'classes': ('collapse',)
        }),

        ('Health Information', {
            'fields': ('blood_group', 'genotype', 'medical_conditions'),
            'classes': ('collapse',)
        }),

        ('Performance & Status', {
            'fields': ('performance_rating', 'last_appraisal_date',
                       'is_active', 'is_retired', 'retirement_date'),
        }),
    )

    inlines = [TeacherProfileInline, StaffPermissionInline]

    # Custom display methods
    def get_full_name(self, obj):
        if not obj or not obj.user:
            return "N/A"
        try:
            name = obj.user.get_full_name()
            if not name:
                name = f"{obj.user.first_name or ''} {obj.user.last_name or ''}".strip()
            return name
        except Exception:
            return "N/A"

    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'user__first_name'

    def is_active_display(self, obj):
        if not obj:
            return "N/A"

        if obj.is_active:
            if obj.is_on_leave:
                return "On Leave"
            elif obj.is_retired:
                return "Retired"
            else:
                return "Active"
        else:
            return "Inactive"

    is_active_display.short_description = 'Status'

    # Admin actions
    actions = ['activate_staff', 'deactivate_staff', 'mark_as_on_leave',
               'mark_as_retired', 'reset_leave_balance', 'generate_staff_id']

    def activate_staff(self, request, queryset):
        """Activate selected staff"""
        updated = queryset.update(is_active=True, is_on_leave=False)
        self.message_user(request, f'{updated} staff member(s) activated.')

    activate_staff.short_description = 'Activate selected staff'

    def deactivate_staff(self, request, queryset):
        """Deactivate selected staff"""
        updated = queryset.update(is_active=False, is_on_leave=False)
        self.message_user(request, f'{updated} staff member(s) deactivated.')

    deactivate_staff.short_description = 'Deactivate selected staff'

    def mark_as_on_leave(self, request, queryset):
        """Mark selected staff as on leave"""
        updated = queryset.update(is_on_leave=True)
        self.message_user(request, f'{updated} staff member(s) marked as on leave.')

    mark_as_on_leave.short_description = 'Mark as on leave'

    def mark_as_retired(self, request, queryset):
        """Mark selected staff as retired"""
        updated = queryset.update(
            is_retired=True,
            is_active=False,
            is_on_leave=False,
            retirement_date=timezone.now().date()
        )
        self.message_user(request, f'{updated} staff member(s) marked as retired.')

    mark_as_retired.short_description = 'Mark as retired'

    def reset_leave_balance(self, request, queryset):
        """Reset leave balance for selected staff"""
        for staff in queryset:
            staff.leave_days_taken = 0
            staff.leave_days_remaining = staff.annual_leave_days
            staff.save()
        self.message_user(request, f'Leave balance reset for {queryset.count()} staff member(s).')

    reset_leave_balance.short_description = 'Reset leave balance'

    def generate_staff_id(self, request, queryset):
        """Generate staff ID for selected staff"""
        for staff in queryset:
            if not staff.staff_id:
                staff.save()
        self.message_user(request, f'Staff ID generated for {queryset.count()} staff member(s).')

    generate_staff_id.short_description = 'Generate Staff ID'

    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('user')


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    """Admin interface for TeacherProfile model"""

    list_display = (
        'get_staff_name',
        'teacher_type',
        'subjects_display',
        'stream_specialization',
        'years_of_experience',
        'workload_display',
    )

    list_filter = (
        'teacher_type',
        'stream_specialization',
    )

    search_fields = (
        'staff__user__first_name',
        'staff__user__last_name',
        'staff__staff_id',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    filter_horizontal = ('subjects', 'class_levels', 'assigned_classes')

    fieldsets = (
        ('Teacher Information', {
            'fields': ('staff', 'teacher_type')
        }),

        ('Teaching Subjects', {
            'fields': ('subjects',),
        }),

        ('Stream & Level Specialization', {
            'fields': ('stream_specialization', 'class_levels'),
        }),

        ('Class Assignments', {
            'fields': ('assigned_classes',),
            'description': 'Classes where teacher serves as class teacher'
        }),

        ('Workload Management', {
            'fields': ('max_periods_per_week', 'current_periods_per_week')
        }),

        ('Experience & Development', {
            'fields': ('years_of_experience', 'previous_schools',
                       'workshops_attended', 'training_certificates'),
            'classes': ('collapse',)
        }),

        ('Teaching Resources', {
            'fields': ('has_teaching_materials', 'teaching_materials_description'),
            'classes': ('collapse',)
        }),
    )

    # Custom display methods
    def get_staff_name(self, obj):
        if not obj or not obj.staff or not obj.staff.user:
            return "N/A"
        try:
            name = obj.staff.user.get_full_name()
            if not name:
                name = f"{obj.staff.user.first_name or ''} {obj.staff.user.last_name or ''}".strip()
            return name
        except Exception:
            return "N/A"

    get_staff_name.short_description = 'Teacher Name'
    get_staff_name.admin_order_field = 'staff__user__first_name'

    def subjects_display(self, obj):
        if not obj:
            return "0"
        try:
            count = obj.subjects.count()
            return str(count)
        except Exception:
            return "0"

    subjects_display.short_description = 'Subjects'

    def workload_display(self, obj):
        if not obj:
            return "N/A"
        try:
            return f"{obj.current_periods_per_week}/{obj.max_periods_per_week}"
        except Exception:
            return "N/A"

    workload_display.short_description = 'Periods'

    actions = ['clear_assigned_classes']

    def clear_assigned_classes(self, request, queryset):
        """Clear assigned classes for selected teachers"""
        for teacher in queryset:
            teacher.assigned_classes.clear()
            teacher.save()
        self.message_user(request, f'Assigned classes cleared for {queryset.count()} teacher(s).')

    clear_assigned_classes.short_description = 'Clear assigned classes'

    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('staff__user')


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    """Admin interface for StaffAttendance model"""

    list_display = (
        'staff_name',
        'date',
        'status_display',
        'check_in_time',
        'check_out_time',
        'hours_worked_display',
        'is_verified_display',
    )

    list_filter = (
        'date',
        'status',
        'is_verified',
        'staff__department',
    )

    search_fields = (
        'staff__user__first_name',
        'staff__user__last_name',
        'staff__staff_id',
        'remarks',
    )

    readonly_fields = (
        'hours_worked',
        'created_at',
        'updated_at',
    )

    date_hierarchy = 'date'
    list_per_page = 50

    fieldsets = (
        ('Attendance Information', {
            'fields': ('staff', 'date', 'status')
        }),

        ('Time Tracking', {
            'fields': ('check_in_time', 'check_out_time', 'hours_worked')
        }),

        ('Leave Details', {
            'fields': ('leave_type', 'leave_days_deducted'),
            'classes': ('collapse',)
        }),

        ('Remarks & Verification', {
            'fields': ('remarks', 'recorded_by', 'is_verified',
                       'verified_by', 'verification_date')
        }),
    )

    # Custom display methods - SIMPLIFIED to avoid format_html issues
    def staff_name(self, obj):
        if not obj or not obj.staff or not obj.staff.user:
            return "N/A"
        try:
            name = obj.staff.user.get_full_name()
            if not name:
                name = f"{obj.staff.user.first_name or ''} {obj.staff.user.last_name or ''}".strip()
            return name
        except Exception:
            return "N/A"

    staff_name.short_description = 'Staff Name'
    staff_name.admin_order_field = 'staff__user__first_name'

    def status_display(self, obj):
        if not obj:
            return "N/A"
        try:
            return obj.get_status_display() or str(obj.status)
        except Exception:
            return str(obj.status) if obj.status else "N/A"

    status_display.short_description = 'Status'

    def hours_worked_display(self, obj):
        if not obj:
            return "-"
        try:
            if hasattr(obj, 'hours_worked') and obj.hours_worked is not None:
                if obj.hours_worked > 0:
                    return f"{obj.hours_worked:.1f} hrs"
        except Exception:
            pass
        return "-"

    hours_worked_display.short_description = 'Hours'

    def is_verified_display(self, obj):
        if not obj:
            return "N/A"

        try:
            return "Verified" if obj.is_verified else "Pending"
        except Exception:
            return "N/A"

    is_verified_display.short_description = 'Verified'

    # Admin actions
    actions = ['verify_attendance', 'mark_as_present', 'mark_as_absent',
               'calculate_hours']

    def verify_attendance(self, request, queryset):
        """Verify selected attendance records"""
        try:
            staff_profile = request.user.staff_profile
        except AttributeError:
            staff_profile = None

        updated = queryset.update(
            is_verified=True,
            verified_by=staff_profile,
            verification_date=timezone.now()
        )
        self.message_user(request, f'{updated} attendance record(s) verified.')

    verify_attendance.short_description = 'Verify selected attendance'

    def mark_as_present(self, request, queryset):
        """Mark selected records as present"""
        updated = queryset.update(status='present')
        self.message_user(request, f'{updated} record(s) marked as present.')

    mark_as_present.short_description = 'Mark as present'

    def mark_as_absent(self, request, queryset):
        """Mark selected records as absent"""
        updated = queryset.update(status='absent')
        self.message_user(request, f'{updated} record(s) marked as absent.')

    mark_as_absent.short_description = 'Mark as absent'

    def calculate_hours(self, request, queryset):
        """Calculate hours worked for selected records"""
        count = 0
        for record in queryset:
            if record.check_in_time and record.check_out_time:
                record.save()
                count += 1
        self.message_user(request, f'Hours calculated for {count} record(s).')

    calculate_hours.short_description = 'Calculate hours worked'

    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related(
            'staff__user', 'recorded_by__user', 'verified_by__user'
        )


@admin.register(StaffPermission)
class StaffPermissionAdmin(admin.ModelAdmin):
    """Admin interface for StaffPermission model"""

    list_display = (
        'staff_name',
        'permission_summary',
        'can_edit_results',
        'can_add_students',
        'can_add_staff',
        'can_edit_finances',
    )

    list_filter = (
        'can_edit_results',
        'can_approve_results',
        'can_add_staff',
        'can_edit_finances',
        'can_manage_system_settings',
    )

    search_fields = (
        'staff__user__first_name',
        'staff__user__last_name',
        'staff__staff_id',
    )

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Staff Information', {
            'fields': ('staff',)
        }),

        ('Academic Permissions', {
            'fields': ('can_view_all_results', 'can_edit_results',
                       'can_approve_results', 'can_generate_reports')
        }),

        ('Student Management', {
            'fields': ('can_add_students', 'can_edit_students', 'can_view_all_students')
        }),

        ('Parent Management', {
            'fields': ('can_add_parents', 'can_edit_parents')
        }),

        ('Staff Management', {
            'fields': ('can_add_staff', 'can_edit_staff', 'can_view_all_staff')
        }),

        ('Financial Permissions', {
            'fields': ('can_view_finances', 'can_edit_finances',
                       'can_generate_financial_reports')
        }),

        ('System Administration', {
            'fields': ('can_manage_system_settings', 'can_view_audit_logs',
                       'can_manage_backups')
        }),

        ('Communication Permissions', {
            'fields': ('can_send_broadcast_messages', 'can_send_individual_messages')
        }),
    )

    # Custom display methods
    def staff_name(self, obj):
        if not obj or not obj.staff or not obj.staff.user:
            return "N/A"
        try:
            name = obj.staff.user.get_full_name()
            if not name:
                name = f"{obj.staff.user.first_name or ''} {obj.staff.user.last_name or ''}".strip()
            return name
        except Exception:
            return "N/A"

    staff_name.short_description = 'Staff Name'
    staff_name.admin_order_field = 'staff__user__first_name'

    def permission_summary(self, obj):
        """Show a summary of key permissions"""
        if not obj:
            return "Basic"

        try:
            permissions = []
            if obj.can_edit_results:
                permissions.append('Edit Results')
            if obj.can_add_students:
                permissions.append('Add Students')
            if obj.can_add_staff:
                permissions.append('Add Staff')
            if obj.can_edit_finances:
                permissions.append('Edit Finances')

            if permissions:
                return ', '.join(permissions[:3]) + ('...' if len(permissions) > 3 else '')
            return 'Basic'
        except Exception:
            return "Basic"

    permission_summary.short_description = 'Key Permissions'

    actions = ['reset_to_default', 'grant_admin_permissions', 'grant_teacher_permissions']

    def reset_to_default(self, request, queryset):
        """Reset permissions to default based on role"""
        for permission in queryset:
            permission.save()
        self.message_user(request, f'Permissions reset for {queryset.count()} staff member(s).')

    reset_to_default.short_description = 'Reset to default permissions'

    def grant_admin_permissions(self, request, queryset):
        """Grant admin permissions to selected staff"""
        for permission in queryset:
            permission.can_view_all_results = True
            permission.can_edit_results = True
            permission.can_approve_results = True
            permission.can_add_students = True
            permission.can_add_staff = True
            permission.can_edit_finances = True
            permission.save()
        self.message_user(request, f'Admin permissions granted to {queryset.count()} staff member(s).')

    grant_admin_permissions.short_description = 'Grant admin permissions'

    def grant_teacher_permissions(self, request, queryset):
        """Grant teacher permissions to selected staff"""
        for permission in queryset:
            permission.can_view_all_results = False
            permission.can_edit_results = True
            permission.can_approve_results = False
            permission.can_add_students = True
            permission.can_add_staff = False
            permission.can_edit_finances = False
            permission.save()
        self.message_user(request, f'Teacher permissions granted to {queryset.count()} staff member(s).')

    grant_teacher_permissions.short_description = 'Grant teacher permissions'

    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('staff__user')