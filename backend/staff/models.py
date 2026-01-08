from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from academic.models import Subject, ClassLevel
import random
import string


class Staff(models.Model):
    """
    Staff Model - Base model for all school staff members
    Inherits from User model with staff-specific fields and permissions
    """

    # Link to main User model (One-to-One relationship)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        help_text="Linked user account"
    )

    # Employment Information
    staff_id = models.CharField(max_length=20, unique=True, blank=True, help_text="Unique staff identification number")
    employment_date = models.DateField(default=timezone.now, help_text="Date staff was employed")

    # Employment Type
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('volunteer', 'Volunteer'),
        ('trainee', 'Trainee/Intern'),
    ]

    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time',
                                       help_text="Type of employment")

    # Department/Unit (for non-teaching staff)
    DEPARTMENT_CHOICES = [
        ('administration', 'Administration'),
        ('academic', 'Academic'),
        ('finance', 'Finance/Bursary'),
        ('library', 'Library'),
        ('laboratory', 'Laboratory'),
        ('ict', 'ICT/Computer'),
        ('security', 'Security'),
        ('maintenance', 'Maintenance'),
        ('transport', 'Transport'),
        ('health', 'Health Clinic'),
        ('counseling', 'Guidance & Counseling'),
        ('sports', 'Sports & Games'),
        ('none', 'Not Applicable'),
    ]

    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='none',
                                  help_text="Department/Unit assignment")

    # Qualification & Certification
    highest_qualification = models.CharField(max_length=100, blank=True,
                                             help_text="Highest educational qualification (e.g., B.Sc, M.Ed, PhD)")
    qualification_institution = models.CharField(max_length=200, blank=True,
                                                 help_text="Institution where qualification was obtained")
    year_of_graduation = models.IntegerField(blank=True, null=True, help_text="Year of graduation")
    professional_certifications = models.TextField(blank=True, help_text="Professional certifications (TRCN, etc.)")
    trcn_number = models.CharField(max_length=50, blank=True,
                                   help_text="Teachers Registration Council of Nigeria Number")
    specialization = models.TextField(blank=True, help_text="Areas of specialization/expertise")

    # Bank Information (for salary payments)
    bank_name = models.CharField(max_length=100, blank=True, help_text="Bank name for salary payments")
    account_name = models.CharField(max_length=100, blank=True, help_text="Account name as registered with bank")
    account_number = models.CharField(max_length=20, blank=True, help_text="Bank account number")

    # Salary Information
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Basic monthly salary")
    salary_scale = models.CharField(max_length=50, blank=True, help_text="Salary scale/grade level")

    # Leave Information
    annual_leave_days = models.IntegerField(default=21, help_text="Annual leave entitlement in days")
    leave_days_taken = models.IntegerField(default=0, help_text="Leave days already taken")
    leave_days_remaining = models.IntegerField(default=21, help_text="Remaining leave days")

    # Next of Kin Information
    next_of_kin_name = models.CharField(max_length=100, blank=True, help_text="Next of kin full name")
    next_of_kin_relationship = models.CharField(max_length=50, blank=True, help_text="Relationship to staff")
    next_of_kin_phone = models.CharField(max_length=15, blank=True, help_text="Next of kin phone number")
    next_of_kin_address = models.TextField(blank=True, help_text="Next of kin address")

    # Health Information
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    GENOTYPE_CHOICES = [
        ('AA', 'AA'), ('AS', 'AS'),
        ('SS', 'SS'), ('AC', 'AC'),
    ]

    blood_group = models.CharField(max_length=5, blank=True, choices=BLOOD_GROUP_CHOICES)
    genotype = models.CharField(max_length=3, blank=True, choices=GENOTYPE_CHOICES)
    medical_conditions = models.TextField(blank=True, help_text="Any known medical conditions")

    # Status Flags
    is_active = models.BooleanField(default=True, help_text="Is staff currently active/employed?")
    is_retired = models.BooleanField(default=False, help_text="Has staff retired?")
    retirement_date = models.DateField(blank=True, null=True, help_text="Date of retirement")
    is_on_leave = models.BooleanField(default=False, help_text="Is staff currently on leave?")
    leave_start_date = models.DateField(blank=True, null=True, help_text="Leave start date")
    leave_end_date = models.DateField(blank=True, null=True, help_text="Leave end date")

    # Performance & Ratings
    performance_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0,
                                             help_text="Overall performance rating (0-5)")
    last_appraisal_date = models.DateField(blank=True, null=True, help_text="Date of last performance appraisal")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name']
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'
        indexes = [
            models.Index(fields=['staff_id']),
            models.Index(fields=['employment_type']),
            models.Index(fields=['department']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.staff_id} ({self.user.get_role_display()})"

    def save(self, *args, **kwargs):
        """Auto-generate staff ID and update leave balance"""
        # Auto-generate staff ID if not set
        if not self.staff_id:
            prefix = "STF"
            while True:
                random_num = ''.join(random.choices(string.digits, k=6))
                staff_id = f"{prefix}{random_num}"
                if not Staff.objects.filter(staff_id=staff_id).exists():
                    self.staff_id = staff_id
                    break

        # Calculate remaining leave days
        self.leave_days_remaining = self.annual_leave_days - self.leave_days_taken

        super().save(*args, **kwargs)

    def get_staff_type(self):
        """Get staff type based on user role"""
        teaching_roles = ['teacher', 'form_teacher', 'subject_teacher', 'head',
                          'principal', 'vice_principal']

        if self.user.role in teaching_roles:
            return 'teaching'
        else:
            return 'non_teaching'

    def get_monthly_salary(self):
        """Calculate total monthly salary with allowances"""
        # Basic implementation - extend with allowances in production
        return self.basic_salary


class TeacherProfile(models.Model):
    """
    Teacher Profile Model - Extended profile for teaching staff
    Linked to Staff model for teachers, form teachers, and subject teachers
    """

    # Link to Staff
    staff = models.OneToOneField(
        Staff,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        help_text="Linked staff profile"
    )

    # Teacher Type
    TEACHER_TYPE_CHOICES = [
        ('class_teacher', 'Class Teacher'),
        ('subject_teacher', 'Subject Teacher'),
        ('both', 'Class & Subject Teacher'),
        ('head_of_department', 'Head of Department'),
        ('vice_principal_academic', 'Vice Principal (Academic)'),
        ('principal', 'Principal'),
        ('head', 'Head of School'),
    ]

    teacher_type = models.CharField(max_length=30, choices=TEACHER_TYPE_CHOICES, default='subject_teacher',
                                    help_text="Type of teaching role")

    # Subjects (Many-to-Many relationship for multiple subjects)
    subjects = models.ManyToManyField(
        Subject,
        related_name='teachers',
        blank=True,
        help_text="Subjects teacher can teach"
    )

    # Stream Specialization (for Senior Secondary)
    STREAM_CHOICES = [
        ('science', 'Science'),
        ('commercial', 'Commercial'),
        ('arts', 'Arts/Humanities'),
        ('general', 'General (All Streams)'),
        ('none', 'Not Applicable'),
    ]

    stream_specialization = models.CharField(max_length=20, choices=STREAM_CHOICES, default='none',
                                             help_text="Stream specialization for Senior Secondary")

    # Class Levels Teacher Can Teach
    class_levels = models.ManyToManyField(
        ClassLevel,
        related_name='teachers',
        blank=True,
        help_text="Class levels teacher can teach"
    )

    # Assigned Classes as Class Teacher
    assigned_classes = models.ManyToManyField(
        'academic.Class',
        related_name='class_teachers',
        blank=True,
        help_text="Classes assigned as class teacher"
    )

    # Maximum Load
    max_periods_per_week = models.IntegerField(default=40, help_text="Maximum teaching periods per week")
    current_periods_per_week = models.IntegerField(default=0, help_text="Current teaching periods per week")

    # Teaching Experience
    years_of_experience = models.IntegerField(default=0, help_text="Total years of teaching experience")
    previous_schools = models.TextField(blank=True, help_text="Previous schools taught at")

    # Professional Development
    workshops_attended = models.TextField(blank=True, help_text="Professional development workshops attended")
    training_certificates = models.TextField(blank=True, help_text="Training certificates obtained")

    # Teaching Materials/Resources
    has_teaching_materials = models.BooleanField(default=False, help_text="Has personal teaching materials")
    teaching_materials_description = models.TextField(blank=True,
                                                      help_text="Description of teaching materials available")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['staff__user__first_name']
        verbose_name = 'Teacher Profile'
        verbose_name_plural = 'Teacher Profiles'

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_teacher_type_display()}"

    def save(self, *args, **kwargs):
        """Validate teacher assignments and update staff role"""
        # Ensure staff user has appropriate teacher role
        if self.staff.user.role not in ['teacher', 'form_teacher', 'subject_teacher',
                                        'head', 'principal', 'vice_principal']:
            # Set to subject teacher by default if not already a teaching role
            self.staff.user.role = 'subject_teacher'
            self.staff.user.save()

        super().save(*args, **kwargs)

    def get_subjects_list(self):
        """Return list of subject codes"""
        return [subject.code for subject in self.subjects.all()]

    def get_class_levels_list(self):
        """Return list of class level codes"""
        return [level.code for level in self.class_levels.all()]

    def can_teach_subject_in_stream(self, subject, stream, class_level):
        """
        Check if teacher can teach a specific subject in a stream and class level

        Args:
            subject: Subject object
            stream: Science, Commercial, or Arts
            class_level: ClassLevel object
        """
        # Check if teacher has the subject
        if subject not in self.subjects.all():
            return False

        # Check if teacher can teach at this class level
        if class_level not in self.class_levels.all():
            return False

        # For Senior Secondary, check stream compatibility
        if class_level.level.startswith('sss_'):
            if self.stream_specialization == 'general':
                return True
            elif self.stream_specialization == stream:
                return True
            else:
                return False

        # For other levels, no stream restriction
        return True

    def is_class_teacher_of(self, student):
        """
        Check if this teacher is class teacher for a specific student
        """
        # Use string reference to avoid circular import
        from students.models import Student  # <-- Import here

        if not isinstance(student, Student):
            return False

        # Check if student's class is in teacher's assigned classes
        if student.class_level:
            return self.assigned_classes.filter(
                class_level=student.class_level
            ).exists()
        return False

    def get_workload_percentage(self):
        """Calculate current workload as percentage of maximum"""
        if self.max_periods_per_week > 0:
            return (self.current_periods_per_week / self.max_periods_per_week) * 100
        return 0


class StaffAttendance(models.Model):
    """
    Staff Attendance Tracking Model
    Records daily attendance for all staff members
    """

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Staff member"
    )

    date = models.DateField(default=timezone.now, help_text="Attendance date")

    ATTENDANCE_STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
        ('off_duty', 'Off Duty'),
        ('sick', 'Sick Leave'),
        ('emergency', 'Emergency Leave'),
        ('training', 'Training/Workshop'),
        ('other', 'Other'),
    ]

    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS_CHOICES, default='present',
                              help_text="Attendance status")
    check_in_time = models.TimeField(blank=True, null=True, help_text="Check-in time")
    check_out_time = models.TimeField(blank=True, null=True, help_text="Check-out time")
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2, default=0.00, help_text="Total hours worked")

    # Leave Information (if applicable)
    LEAVE_TYPE_CHOICES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('casual', 'Casual Leave'),
        ('compassionate', 'Compassionate Leave'),
        ('study', 'Study Leave'),
        ('unpaid', 'Unpaid Leave'),
    ]

    leave_type = models.CharField(max_length=50, blank=True, choices=LEAVE_TYPE_CHOICES)
    leave_days_deducted = models.IntegerField(default=0, help_text="Number of leave days deducted")

    # Remarks/Notes
    remarks = models.TextField(blank=True, help_text="Additional remarks or notes")

    recorded_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_attendances',
        help_text="Staff who recorded this attendance"
    )

    # Verification
    is_verified = models.BooleanField(default=False, help_text="Has attendance been verified by supervisor?")
    verified_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_attendances',
        help_text="Supervisor who verified attendance"
    )
    verification_date = models.DateTimeField(blank=True, null=True, help_text="Date and time of verification")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'staff__user__first_name']
        verbose_name = 'Staff Attendance'
        verbose_name_plural = 'Staff Attendances'
        unique_together = ['staff', 'date']
        indexes = [
            models.Index(fields=['staff', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.date} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Calculate hours worked and update leave balance"""
        # Calculate hours worked if both check-in and check-out times exist
        if self.check_in_time and self.check_out_time:
            from datetime import datetime, date

            # Create datetime objects for calculation
            check_in_dt = datetime.combine(date.today(), self.check_in_time)
            check_out_dt = datetime.combine(date.today(), self.check_out_time)

            # Calculate difference in hours
            time_diff = check_out_dt - check_in_dt
            self.hours_worked = time_diff.total_seconds() / 3600  # Convert to hours

        # Update staff leave balance if leave was taken
        if self.status in ['leave', 'sick', 'emergency'] and self.leave_days_deducted > 0:
            self.staff.leave_days_taken += self.leave_days_deducted
            self.staff.save()

        super().save(*args, **kwargs)


class StaffPermission(models.Model):
    """
    Staff Permission Model
    Defines specific permissions for staff roles beyond Django's built-in
    """

    staff = models.OneToOneField(
        Staff,
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text="Staff member"
    )

    # Academic Permissions
    can_view_all_results = models.BooleanField(default=False, help_text="Can view all students' results")
    can_edit_results = models.BooleanField(default=False, help_text="Can edit examination results")
    can_approve_results = models.BooleanField(default=False, help_text="Can approve final results")
    can_generate_reports = models.BooleanField(default=False, help_text="Can generate academic reports")

    # Student Management Permissions
    can_add_students = models.BooleanField(default=False, help_text="Can add new students")
    can_edit_students = models.BooleanField(default=False, help_text="Can edit student profiles")
    can_view_all_students = models.BooleanField(default=False, help_text="Can view all students")

    # Parent Management Permissions
    can_add_parents = models.BooleanField(default=False, help_text="Can add new parents")
    can_edit_parents = models.BooleanField(default=False, help_text="Can edit parent profiles")

    # Staff Management Permissions
    can_add_staff = models.BooleanField(default=False, help_text="Can add new staff")
    can_edit_staff = models.BooleanField(default=False, help_text="Can edit staff profiles")
    can_view_all_staff = models.BooleanField(default=False, help_text="Can view all staff")

    # Financial Permissions
    can_view_finances = models.BooleanField(default=False, help_text="Can view financial records")
    can_edit_finances = models.BooleanField(default=False, help_text="Can edit financial records")
    can_generate_financial_reports = models.BooleanField(default=False, help_text="Can generate financial reports")

    # System Administration Permissions
    can_manage_system_settings = models.BooleanField(default=False, help_text="Can manage system settings")
    can_view_audit_logs = models.BooleanField(default=False, help_text="Can view system audit logs")
    can_manage_backups = models.BooleanField(default=False, help_text="Can manage system backups")

    # Communication Permissions
    can_send_broadcast_messages = models.BooleanField(default=False, help_text="Can send broadcast messages")
    can_send_individual_messages = models.BooleanField(default=True, help_text="Can send individual messages")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Staff Permission'
        verbose_name_plural = 'Staff Permissions'

    def __str__(self):
        return f"Permissions for {self.staff.user.get_full_name()}"