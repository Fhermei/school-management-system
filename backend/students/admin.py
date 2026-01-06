from django.contrib import admin
from django.utils.html import format_html
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin configuration for Student model"""

    # ===============================
    # LIST VIEW CONFIG
    # ===============================
    list_display = (
        'get_full_name',
        'admission_number',
        'get_class',
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
        'is_active',
        'is_prefect',
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
        ('Attendance', {
            'fields': ('days_present', 'days_absent', 'days_late'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': (
                'is_active',
                'is_graduated',
                'graduation_date',
                'is_prefect',
                'prefect_role',
            ),
        }),
    )

    # ===============================
    # CUSTOM DISPLAY METHODS
    # ===============================
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Student Name'
    get_full_name.admin_order_field = 'user__first_name'

    def get_class(self, obj):
        return obj.get_class_level_display()
    get_class.short_description = 'Class'

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
    )

    def mark_as_paid_full(self, request, queryset):
        updated = queryset.update(fee_status='paid_full')
        self.message_user(
            request,
            f'{updated} student(s) marked as paid in full.'
        )
    mark_as_paid_full.short_description = 'Mark selected students as paid in full'

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} student(s) activated.'
        )
    mark_as_active.short_description = 'Activate selected students'

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} student(s) deactivated.'
        )
    mark_as_inactive.short_description = 'Deactivate selected students'
