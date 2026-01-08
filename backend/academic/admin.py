from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    AcademicSession, AcademicTerm, Program, ClassLevel, Subject,
    Class, ClassSubject, Timetable, TimetableEntry
)
import os

@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    """Admin interface for AcademicSession model"""

    list_display = (
        'name',
        'start_date',
        'end_date',
        'status',
        'is_current',
        'get_duration_days',
        'created_at',
    )

    list_filter = (
        'status',
        'is_current',
    )

    search_fields = (
        'name',
        'description',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'get_duration_days',
    )

    fieldsets = (
        ('Session Information', {
            'fields': ('name', 'start_date', 'end_date', 'is_current', 'status')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_current', 'mark_as_active', 'mark_as_completed', 'mark_as_archived']

    def mark_as_current(self, request, queryset):
        """Mark selected sessions as current"""
        # First unmark all current sessions
        AcademicSession.objects.filter(is_current=True).update(is_current=False)

        # Mark selected as current
        queryset.update(is_current=True, status='active')
        self.message_user(request, f'{queryset.count()} session(s) marked as current.')

    mark_as_current.short_description = 'Mark as current session'

    def mark_as_active(self, request, queryset):
        """Mark selected sessions as active"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} session(s) marked as active.')

    mark_as_active.short_description = 'Mark as active'

    def mark_as_completed(self, request, queryset):
        """Mark selected sessions as completed"""
        updated = queryset.update(status='completed', is_current=False)
        self.message_user(request, f'{updated} session(s) marked as completed.')

    mark_as_completed.short_description = 'Mark as completed'

    def mark_as_archived(self, request, queryset):
        """Mark selected sessions as archived"""
        updated = queryset.update(status='archived', is_current=False)
        self.message_user(request, f'{updated} session(s) marked as archived.')

    mark_as_archived.short_description = 'Mark as archived'


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    """Admin interface for AcademicTerm model"""

    list_display = (
        'name',
        'session',
        'term',
        'start_date',
        'end_date',
        'status',
        'is_current',
        'total_school_days',
        'created_at',
    )

    list_filter = (
        'session',
        'term',
        'status',
        'is_current',
    )

    search_fields = (
        'name',
        'description',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'get_duration_days',
        'get_teaching_days',
    )

    fieldsets = (
        ('Term Information', {
            'fields': ('session', 'term', 'name', 'start_date', 'end_date', 'is_current', 'status')
        }),
        ('Academic Calendar', {
            'fields': ('total_school_days', 'total_teaching_weeks', 'holiday_weeks', 'examination_weeks'),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_current', 'mark_as_active', 'mark_as_completed']

    def mark_as_current(self, request, queryset):
        """Mark selected terms as current"""
        # First unmark all current terms
        AcademicTerm.objects.filter(is_current=True).update(is_current=False)

        # Mark selected as current
        for term in queryset:
            term.is_current = True
            term.status = 'active'
            term.save()
        self.message_user(request, f'{queryset.count()} term(s) marked as current.')

    mark_as_current.short_description = 'Mark as current term'

    def mark_as_active(self, request, queryset):
        """Mark selected terms as active"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} term(s) marked as active.')

    mark_as_active.short_description = 'Mark as active'

    def mark_as_completed(self, request, queryset):
        """Mark selected terms as completed"""
        updated = queryset.update(status='completed', is_current=False)
        self.message_user(request, f'{updated} term(s) marked as completed.')

    mark_as_completed.short_description = 'Mark as completed'


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    """Admin interface for Program model"""

    list_display = (
        'name',
        'program_type',
        'code',
        'duration_years',
        'curriculum',
        'is_active',
        'get_class_levels_count',
        'get_subjects_count',
        'created_at',
    )

    list_filter = (
        'program_type',
        'is_active',
        'curriculum',
    )

    search_fields = (
        'name',
        'code',
        'description',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Program Information', {
            'fields': ('name', 'program_type', 'code', 'duration_years', 'curriculum', 'is_active')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_programs', 'deactivate_programs']

    def activate_programs(self, request, queryset):
        """Activate selected programs"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} program(s) activated.')

    activate_programs.short_description = 'Activate selected programs'

    def deactivate_programs(self, request, queryset):
        """Deactivate selected programs"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} program(s) deactivated.')

    deactivate_programs.short_description = 'Deactivate selected programs'

    def get_class_levels_count(self, obj):
        return obj.class_levels.count()

    get_class_levels_count.short_description = 'Class Levels'

    def get_subjects_count(self, obj):
        return obj.subjects.count()

    get_subjects_count.short_description = 'Subjects'


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    """Admin interface for ClassLevel model"""

    list_display = (
        'name',
        'program',
        'level',
        'code',
        'min_age',
        'max_age',
        'order',
        'is_promotion_level',
        'is_active',
        'get_subjects_count',
        'created_at',
    )

    list_filter = (
        'program',
        'level',
        'is_promotion_level',
        'is_active',
    )

    search_fields = (
        'name',
        'code',
        'description',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'get_next_level',
    )

    fieldsets = (
        ('Level Information', {
            'fields': ('program', 'level', 'name', 'code', 'order')
        }),
        ('Age Requirements', {
            'fields': ('min_age', 'max_age'),
            'classes': ('collapse',)
        }),
        ('Academic Settings', {
            'fields': ('required_previous_level', 'is_promotion_level', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_levels', 'deactivate_levels', 'mark_as_promotion_level']

    def activate_levels(self, request, queryset):
        """Activate selected class levels"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} class level(s) activated.')

    activate_levels.short_description = 'Activate selected levels'

    def deactivate_levels(self, request, queryset):
        """Deactivate selected class levels"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} class level(s) deactivated.')

    deactivate_levels.short_description = 'Deactivate selected levels'

    def mark_as_promotion_level(self, request, queryset):
        """Mark selected levels as promotion levels"""
        updated = queryset.update(is_promotion_level=True)
        self.message_user(request, f'{updated} level(s) marked as promotion levels.')

    mark_as_promotion_level.short_description = 'Mark as promotion level'

    def get_subjects_count(self, obj):
        return obj.subjects.count()

    get_subjects_count.short_description = 'Subjects'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin interface for Subject model"""

    list_display = (
        'code',
        'name',
        'subject_type',
        'stream',
        'periods_per_week',
        'is_compulsory',
        'is_examinable',
        'is_active',
        'get_total_teaching_hours_display',
        'created_at',
    )

    list_filter = (
        'subject_type',
        'stream',
        'is_compulsory',
        'is_examinable',
        'is_active',
    )

    search_fields = (
        'name',
        'code',
        'short_name',
        'description',
    )

    filter_horizontal = ('programs', 'class_levels')

    readonly_fields = (
        'total_teaching_hours',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Subject Information', {
            'fields': ('name', 'code', 'short_name', 'subject_type', 'stream')
        }),
        ('Program & Level Association', {
            'fields': ('programs', 'class_levels'),
            'classes': ('collapse',)
        }),
        ('Teaching Schedule', {
            'fields': ('periods_per_week', 'minutes_per_period', 'total_teaching_hours'),
            'classes': ('collapse',)
        }),
        ('Assessment Settings', {
            'fields': ('has_continuous_assessment', 'ca_weight', 'exam_weight'),
            'classes': ('collapse',)
        }),
        ('Nigerian School Settings', {
            'fields': ('is_compulsory', 'is_examinable', 'is_practical', 'subject_group'),
            'classes': ('collapse',)
        }),
        ('Curriculum Information', {
            'fields': ('curriculum', 'syllabus'),
            'classes': ('collapse',)
        }),
        ('Status & Description', {
            'fields': ('is_active', 'created_by', 'description')
        }),
    )

    actions = ['activate_subjects', 'deactivate_subjects', 'mark_as_compulsory']

    def activate_subjects(self, request, queryset):
        """Activate selected subjects"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subject(s) activated.')

    activate_subjects.short_description = 'Activate selected subjects'

    def deactivate_subjects(self, request, queryset):
        """Deactivate selected subjects"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subject(s) deactivated.')

    deactivate_subjects.short_description = 'Deactivate selected subjects'

    def mark_as_compulsory(self, request, queryset):
        """Mark selected subjects as compulsory"""
        updated = queryset.update(is_compulsory=True)
        self.message_user(request, f'{updated} subject(s) marked as compulsory.')

    mark_as_compulsory.short_description = 'Mark as compulsory'

    def get_total_teaching_hours_display(self, obj):
        return f"{obj.total_teaching_hours} hrs"

    get_total_teaching_hours_display.short_description = 'Teaching Hours'


class ClassSubjectInline(admin.TabularInline):
    """Inline for ClassSubject in Class admin"""
    model = ClassSubject
    extra = 1
    fields = ('subject', 'teacher', 'co_teacher', 'periods_per_week', 'is_active', 'is_compulsory')
    autocomplete_fields = ['subject', 'teacher', 'co_teacher']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """Admin interface for Class model"""

    list_display = (
        'name',
        'code',
        'class_level',
        'session',
        'term',
        'class_teacher_info',
        'current_enrollment',
        'max_capacity',
        'available_seats',
        'status',
        'is_active',
        'created_at',
    )

    list_filter = (
        'session',
        'term',
        'class_level',
        'status',
        'is_active',
        'stream',
    )

    search_fields = (
        'name',
        'code',
        'room_number',
        'description',
    )

    readonly_fields = (
        'code',
        'slug',
        'current_enrollment',
        'created_at',
        'updated_at',
        'get_available_seats',
        'is_full',
    )

    fieldsets = (
        ('Academic Information', {
            'fields': ('session', 'term', 'class_level', 'name', 'code', 'slug')
        }),
        ('Class Details', {
            'fields': ('stream', 'room_number', 'building', 'floor')
        }),
        ('Capacity & Enrollment', {
            'fields': ('max_capacity', 'current_enrollment', 'get_available_seats', 'is_full')
        }),
        ('Class Teachers', {
            'fields': ('class_teacher', 'assistant_class_teacher'),
            'classes': ('collapse',)
        }),
        ('Dates & Status', {
            'fields': ('start_date', 'end_date', 'status', 'is_active')
        }),
        ('Additional Information', {
            'fields': ('description', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ClassSubjectInline]

    def class_teacher_info(self, obj):
        """Display class teacher information"""
        if obj.class_teacher:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:users_user_change', args=[obj.class_teacher.id]),
                obj.class_teacher.get_full_name()
            )
        return 'Not assigned'

    class_teacher_info.short_description = 'Class Teacher'

    def available_seats(self, obj):
        """Display available seats with color coding"""
        seats = obj.get_available_seats()
        if seats > 10:
            color = 'green'
        elif seats > 0:
            color = 'orange'
        else:
            color = 'red'

        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color,
            seats
        )

    available_seats.short_description = 'Available Seats'

    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related(
            'session', 'term', 'class_level', 'class_teacher'
        ).prefetch_related('subjects')


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    """Admin interface for ClassSubject model"""

    list_display = (
        'class_obj',
        'subject',
        'teacher_info',
        'co_teacher_info',
        'periods_per_week',
        'is_active',
        'is_compulsory',
        'created_at',
    )

    list_filter = (
        'is_active',
        'is_compulsory',
        'class_obj__session',
        'class_obj__term',
        'class_obj__class_level',
    )

    search_fields = (
        'class_obj__name',
        'subject__name',
        'teacher__first_name',
        'teacher__last_name',
        'notes',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Assignment Information', {
            'fields': ('class_obj', 'subject', 'teacher', 'co_teacher')
        }),
        ('Teaching Schedule', {
            'fields': ('periods_per_week', 'preferred_days', 'preferred_times'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('Assessment Settings', {
            'fields': ('ca_required', 'exam_required'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_compulsory')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def teacher_info(self, obj):
        """Display teacher information"""
        if obj.teacher:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:users_user_change', args=[obj.teacher.id]),
                obj.teacher.get_full_name()
            )
        return 'Not assigned'

    teacher_info.short_description = 'Teacher'

    def co_teacher_info(self, obj):
        """Display co-teacher information"""
        if obj.co_teacher:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:users_user_change', args=[obj.co_teacher.id]),
                obj.co_teacher.get_full_name()
            )
        return 'Not assigned'

    co_teacher_info.short_description = 'Co-Teacher'

    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related(
            'class_obj', 'subject', 'teacher', 'co_teacher'
        )


class TimetableEntryInline(admin.TabularInline):
    """Inline for TimetableEntry in Timetable admin"""
    model = TimetableEntry
    extra = 5
    fields = ('day', 'period_number', 'subject', 'teacher', 'class_obj', 'room', 'entry_type', 'is_active')
    autocomplete_fields = ['subject', 'teacher', 'class_obj']


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    """Admin interface for Timetable model"""

    list_display = (
        'name',
        'code',
        'session',
        'term',
        'scope',
        'scope_target',
        'status',
        'is_active',
        'is_locked',
        'created_at',
    )

    list_filter = (
        'session',
        'term',
        'scope',
        'status',
        'is_active',
        'is_locked',
    )

    search_fields = (
        'name',
        'code',
        'description',
    )

    readonly_fields = (
        'code',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Timetable Information', {
            'fields': ('name', 'code', 'session', 'term', 'scope')
        }),
        ('Scope Target', {
            'fields': ('program', 'class_level', 'class_obj', 'teacher'),
            'classes': ('collapse',)
        }),
        ('Timetable Configuration', {
            'fields': ('days', 'periods_per_day', 'period_duration', 'break_periods', 'lunch_period',
                       'assembly_period'),
            'classes': ('collapse',)
        }),
        ('Schedule Times', {
            'fields': ('start_time', 'end_time'),
            'classes': ('collapse',)
        }),
        ('Status & Version', {
            'fields': ('status', 'is_active', 'is_locked', 'version', 'parent_timetable')
        }),
        ('Approval Workflow', {
            'fields': ('approved_by', 'approved_date'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('description', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    inlines = [TimetableEntryInline]

    def scope_target(self, obj):
        """Display scope target information"""
        if obj.scope == 'program' and obj.program:
            return obj.program.name
        elif obj.scope == 'class_level' and obj.class_level:
            return obj.class_level.name
        elif obj.scope == 'class' and obj.class_obj:
            return obj.class_obj.name
        elif obj.scope == 'teacher' and obj.teacher:
            return obj.teacher.get_full_name()
        return 'N/A'

    scope_target.short_description = 'Target'

    actions = ['publish_timetables', 'activate_timetables', 'lock_timetables', 'duplicate_timetables']

    def publish_timetables(self, request, queryset):
        """Publish selected timetables"""
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} timetable(s) published.')

    publish_timetables.short_description = 'Publish selected timetables'

    def activate_timetables(self, request, queryset):
        """Activate selected timetables"""
        for timetable in queryset:
            timetable.is_active = True
            timetable.save()
        self.message_user(request, f'{queryset.count()} timetable(s) activated.')

    activate_timetables.short_description = 'Activate selected timetables'

    def lock_timetables(self, request, queryset):
        """Lock selected timetables"""
        updated = queryset.update(is_locked=True)
        self.message_user(request, f'{updated} timetable(s) locked.')

    lock_timetables.short_description = 'Lock selected timetables'

    def duplicate_timetables(self, request, queryset):
        """Duplicate selected timetables"""
        for timetable in queryset:
            timetable.pk = None
            timetable.code = f"{timetable.code}-COPY"
            timetable.name = f"{timetable.name} (Copy)"
            timetable.is_active = False
            timetable.is_locked = False
            timetable.status = 'draft'
            timetable.save()
        self.message_user(request, f'{queryset.count()} timetable(s) duplicated.')

    duplicate_timetables.short_description = 'Duplicate selected timetables'


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    """Admin interface for TimetableEntry model"""

    list_display = (
        'timetable',
        'day',
        'period_number',
        'subject',
        'teacher_info',
        'class_obj',
        'room',
        'entry_type',
        'is_active',
        'created_at',
    )

    list_filter = (
        'timetable',
        'day',
        'entry_type',
        'is_active',
    )

    search_fields = (
        'timetable__name',
        'subject__name',
        'teacher__first_name',
        'teacher__last_name',
        'room',
        'notes',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Entry Information', {
            'fields': ('timetable', 'day', 'period_number', 'entry_type')
        }),
        ('Subject Assignment', {
            'fields': ('subject', 'teacher', 'class_obj'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('room',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_locked')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def teacher_info(self, obj):
        """Display teacher information"""
        if obj.teacher:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:users_user_change', args=[obj.teacher.id]),
                obj.teacher.get_full_name()
            )
        return 'Not assigned'

    teacher_info.short_description = 'Teacher'

    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related(
            'timetable', 'subject', 'teacher', 'class_obj'
        )


# @admin.register(StudentEnrollment)
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
    )

    search_fields = (
        'student__first_name',
        'student__last_name',
        'student__registration_number',
        'enrollment_number',
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
        """Display student information with link"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:users_user_change', args=[obj.student.id]),
            obj.student.get_full_name()
        )

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