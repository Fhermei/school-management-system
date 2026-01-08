from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Student, StudentEnrollment


class StudentEnrollmentInline(admin.TabularInline):
    """Inline for StudentEnrollment in Student admin"""
    model = StudentEnrollment
    extra = 0
    fields = ('class_obj', 'session', 'term', 'status', 'enrollment_date')
    readonly_fields = ('enrollment_date',)
    can_delete = False
    max_num = 10


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin configuration for Student model"""

    # ===============================
    # LIST VIEW CONFIG
    # ===============================
    list_display = (
        'get_full_name',
        'admission_number',
        'student_id',
        'get_class_level',
        'get_stream',
        'fee_status_badge',
        'is_prefect',
        'is_active',
        'created_at',
    )

    list_filter = (
        'class_level',
        'stream',
        'fee_status',
        'student_category',
        'house',
        'is_active',
        'is_prefect',
        'is_graduated',
    )

    search_fields = (
        'user__first_name',
        'user__last_name',
        'admission_number',
        'student_id',
        'father__user__first_name',
        'mother__user__first_name',
    )

    readonly_fields = (
        'admission_number',
        'student_id',
        'balance_due',
        'created_at',
        'updated_at',
    )

    list_per_page = 50

    # ===============================
    # FORM LAYOUT
    # ===============================
    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'admission_number', 'student_id'),
        }),
        ('Academic Information', {
            'fields': ('class_level', 'stream', 'house', 'student_category'),
        }),
        ('Parent Information', {
            'fields': ('father', 'mother'),
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone',
                      'emergency_contact_relationship'),
            'classes': ('collapse',),
        }),
        ('Fee Information', {
            'fields': (
                'total_fee_amount',
                'amount_paid',
                'balance_due',
                'fee_status',
                'fee_payment_evidence',
                'last_payment_date',
            ),
        }),
        ('Academic Performance', {
            'fields': ('average_score', 'overall_grade', 'position_in_class'),
            'classes': ('collapse',),
        }),
        ('Health Information', {
            'fields': ('blood_group', 'genotype', 'medical_conditions', 'allergies'),
            'classes': ('collapse',),
        }),
        ('Transportation', {
            'fields': ('transportation_mode', 'bus_route'),
            'classes': ('collapse',),
        }),
        ('Attendance', {
            'fields': ('days_present', 'days_absent', 'days_late'),
            'classes': ('collapse',),
        }),
        ('Prefect & Status', {
            'fields': (
                'is_prefect',
                'prefect_role',
                'is_active',
                'is_graduated',
                'graduation_date',
            ),
        }),
        ('Previous School Information', {
            'fields': ('previous_class', 'previous_school', 'transfer_certificate_no'),
            'classes': ('collapse',),
        }),
    )

    inlines = [StudentEnrollmentInline]

    # ===============================
    # CUSTOM DISPLAY METHODS
    # ===============================
    def get_full_name(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:users_user_change', args=[obj.user.id]),
            obj.user.get_full_name()
        )
    get_full_name.short_description = 'Student Name'
    get_full_name.admin_order_field = 'user__first_name'

    def get_class_level(self, obj):
        if obj.class_level:
            return obj.class_level.name
        return "Not assigned"
    get_class_level.short_description = 'Class'

    def get_stream(self, obj):
        return obj.get_stream_display()
    get_stream.short_description = 'Stream'

    def fee_status_badge(self, obj):
        color_map = {
            'paid_full': 'green',
            'paid_partial': 'orange',
            'not_paid': 'red',
            'scholarship': 'blue',
            'exempted': 'purple',
        }

        color = color_map.get(obj.fee_status, 'gray')
        label = obj.get_fee_status_display()

        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color,
            label,
        )
    fee_status_badge.short_description = 'Fee Status'

    # ===============================
    # ADMIN ACTIONS
    # ===============================
    actions = (
        'mark_as_paid_full',
        'mark_as_active',
        'mark_as_inactive',
        'mark_as_graduated',
        'mark_as_prefect',
        'reset_fee_balance',
    )

    def mark_as_paid_full(self, request, queryset):
        """Mark selected students as paid in full"""
        updated = queryset.update(fee_status='paid_full')
        self.message_user(
            request,
            f'{updated} student(s) marked as paid in full.'
        )
    mark_as_paid_full.short_description = 'Mark as paid in full'

    def mark_as_active(self, request, queryset):
        """Activate selected students"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} student(s) activated.'
        )
    mark_as_active.short_description = 'Activate selected students'

    def mark_as_inactive(self, request, queryset):
        """Deactivate selected students"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} student(s) deactivated.'
        )
    mark_as_inactive.short_description = 'Deactivate selected students'

    def mark_as_graduated(self, request, queryset):
        """Mark selected students as graduated"""
        from django.utils import timezone
        updated = queryset.update(
            is_graduated=True,
            is_active=False,
            graduation_date=timezone.now().date()
        )
        self.message_user(
            request,
            f'{updated} student(s) marked as graduated.'
        )
    mark_as_graduated.short_description = 'Mark as graduated'

    def mark_as_prefect(self, request, queryset):
        """Mark selected students as prefects"""
        updated = queryset.update(is_prefect=True)
        self.message_user(
            request,
            f'{updated} student(s) marked as prefects.'
        )
    mark_as_prefect.short_description = 'Mark as prefect'

    def reset_fee_balance(self, request, queryset):
        """Reset fee balance for selected students"""
        for student in queryset:
            student.amount_paid = 0
            student.balance_due = student.total_fee_amount
            student.fee_status = 'not_paid'
            student.save()
        self.message_user(
            request,
            f'Fee balance reset for {queryset.count()} student(s).'
        )
    reset_fee_balance.short_description = 'Reset fee balance'

    # ===============================
    # CUSTOM FILTERS AND QUERYSET
    # ===============================
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related(
            'user', 'class_level', 'father', 'mother'
        ).prefetch_related('enrollments')


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for StudentEnrollment model"""

    list_display = (
        'student_info',
        'class_obj',
        'session',
        'term',
        'enrollment_date',
        'status_badge',
        'is_repeating',
        'days_present',
        'average_score',
        'position',
        'created_at',
    )

    list_filter = (
        'session',
        'term',
        'status',
        'is_repeating',
        'class_obj',
        'class_obj__class_level',
    )

    search_fields = (
        'student__first_name',
        'student__last_name',
        'student__registration_number',
        'enrollment_number',
        'class_obj__name',
        'remarks',
    )

    readonly_fields = (
        'enrollment_number',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'class_obj', 'session', 'term', 'enrollment_number')
        }),
        ('Status & Dates', {
            'fields': ('enrollment_date', 'status', 'promotion_date'),
            'classes': ('collapse',)
        }),
        ('Academic Status', {
            'fields': ('is_repeating', 'is_promoted'),
            'classes': ('collapse',)
        }),
        ('Attendance & Performance', {
            'fields': ('days_present', 'days_absent', 'average_score', 'position'),
            'classes': ('collapse',)
        }),
        ('Approval Workflow', {
            'fields': ('enrolled_by', 'approved_by', 'approved_date'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )

    def student_info(self, obj):
        if obj.student and obj.student.user:
            name = obj.student.user.get_full_name()
            user_id = obj.student.user.id
        else:
            name = "Unknown Student"
            user_id = None

        if user_id:
            url = reverse('admin:users_user_change', args=[user_id])
            return format_html('<a href="{}">{}</a>', url, name)

        return name

    student_info.short_description = 'Student'
    student_info.admin_order_field = 'student__first_name'

    def status_badge(self, obj):
        """Display status with color coding"""
        color_map = {
            'pending': 'orange',
            'active': 'green',
            'inactive': 'gray',
            'withdrawn': 'red',
            'transferred': 'blue',
            'graduated': 'purple',
            'suspended': 'darkorange',
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['approve_enrollments', 'mark_as_active', 'mark_as_withdrawn',
               'mark_as_graduated', 'mark_as_suspended']

    def approve_enrollments(self, request, queryset):
        """Approve selected enrollments"""
        from django.utils import timezone
        for enrollment in queryset:
            enrollment.status = 'active'
            enrollment.approved_by = request.user
            enrollment.approved_date = timezone.now()
            enrollment.save()
        self.message_user(request, f'{queryset.count()} enrollment(s) approved.')

    approve_enrollments.short_description = 'Approve selected enrollments'

    def mark_as_active(self, request, queryset):
        """Mark selected enrollments as active"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} enrollment(s) marked as active.')

    mark_as_active.short_description = 'Mark as active'

    def mark_as_withdrawn(self, request, queryset):
        """Mark selected enrollments as withdrawn"""
        updated = queryset.update(status='withdrawn')
        self.message_user(request, f'{updated} enrollment(s) marked as withdrawn.')

    mark_as_withdrawn.short_description = 'Mark as withdrawn'

    def mark_as_graduated(self, request, queryset):
        """Mark selected enrollments as graduated"""
        updated = queryset.update(status='graduated')
        self.message_user(request, f'{updated} enrollment(s) marked as graduated.')

    mark_as_graduated.short_description = 'Mark as graduated'

    def mark_as_suspended(self, request, queryset):
        """Mark selected enrollments as suspended"""
        updated = queryset.update(status='suspended')
        self.message_user(request, f'{updated} enrollment(s) marked as suspended.')

    mark_as_suspended.short_description = 'Mark as suspended'
