from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
import random
import string


class AcademicSession(models.Model):
    """
    Academic Session Model
    Represents a full academic year (e.g., 2024/2025)
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Academic session name (e.g., 2024/2025 Academic Session)"
    )

    start_date = models.DateField(help_text="Session start date")
    end_date = models.DateField(help_text="Session end date")
    is_current = models.BooleanField(default=False, help_text="Is this the current academic session?")

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming', help_text="Session status")
    description = models.TextField(blank=True, help_text="Additional notes about the session")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Academic Session'
        verbose_name_plural = 'Academic Sessions'
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Ensure only one session is marked as current"""
        if self.is_current:
            # Unmark other sessions
            AcademicSession.objects.filter(is_current=True).update(is_current=False)

        # Validate dates
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")

        super().save(*args, **kwargs)

    def get_duration_days(self):
        """Calculate session duration in days"""
        return (self.end_date - self.start_date).days

    def is_active_today(self):
        """Check if session is active today"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class AcademicTerm(models.Model):
    """
    Academic Term Model
    Represents a term within an academic session
    """

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name='terms',
        help_text="Parent academic session"
    )

    TERM_CHOICES = [
        ('first', 'First Term'),
        ('second', 'Second Term'),
        ('third', 'Third Term'),
    ]

    term = models.CharField(max_length=20, choices=TERM_CHOICES, help_text="Term name")
    name = models.CharField(max_length=100, help_text="Term display name (e.g., First Term 2024/2025)")
    start_date = models.DateField(help_text="Term start date")
    end_date = models.DateField(help_text="Term end date")
    is_current = models.BooleanField(default=False, help_text="Is this the current term?")

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming', help_text="Term status")

    # Academic Calendar Information
    total_school_days = models.IntegerField(default=0, help_text="Total number of school days in term")
    total_teaching_weeks = models.IntegerField(default=0, help_text="Total number of teaching weeks")
    holiday_weeks = models.IntegerField(default=0, help_text="Number of holiday weeks")
    examination_weeks = models.IntegerField(default=0, help_text="Number of examination weeks")
    description = models.TextField(blank=True, help_text="Term activities and important dates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session__start_date', 'term']
        verbose_name = 'Academic Term'
        verbose_name_plural = 'Academic Terms'
        unique_together = ['session', 'term']
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} - {self.session.name}"

    def save(self, *args, **kwargs):
        """Ensure only one term is marked as current"""
        if self.is_current:
            # Unmark other terms
            AcademicTerm.objects.filter(is_current=True).update(is_current=False)

        # Validate dates
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")

        # Ensure term dates are within session dates
        if (self.start_date < self.session.start_date or
                self.end_date > self.session.end_date):
            raise ValidationError("Term dates must be within session dates")

        # Auto-generate name if not provided
        if not self.name:
            self.name = f"{self.get_term_display()} {self.session.name}"

        super().save(*args, **kwargs)

    def get_duration_days(self):
        """Calculate term duration in days"""
        return (self.end_date - self.start_date).days

    def get_teaching_days(self):
        """Calculate actual teaching days"""
        return self.total_school_days - (self.examination_weeks * 5)  # Assuming 5-day weeks

    def is_active_today(self):
        """Check if term is active today"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class Program(models.Model):
    """
    Academic Program Model
    Represents different academic programs in the school
    """

    PROGRAM_CHOICES = [
        ('pre_school', 'Pre-School (Creche, Nursery, KG)'),
        ('primary', 'Primary School (Basic 1-6)'),
        ('junior_secondary', 'Junior Secondary School (JSS 1-3)'),
        ('senior_secondary', 'Senior Secondary School (SSS 1-3)'),
        ('special_education', 'Special Education'),
        ('adult_education', 'Adult Education'),
        ('vocational', 'Vocational Training'),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="Program name (e.g., Primary Education)")
    program_type = models.CharField(max_length=30, choices=PROGRAM_CHOICES, help_text="Type of academic program")
    code = models.CharField(max_length=20, unique=True, help_text="Program code (e.g., PRI, JSS, SSS)")
    description = models.TextField(blank=True, help_text="Program description and objectives")
    duration_years = models.IntegerField(default=0, help_text="Program duration in years")

    # Curriculum Information
    curriculum = models.CharField(max_length=100, blank=True,
                                  help_text="Curriculum followed (e.g., Nigerian, British, American)")
    is_active = models.BooleanField(default=True, help_text="Is this program currently active?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['program_type', 'name']
        verbose_name = 'Academic Program'
        verbose_name_plural = 'Academic Programs'

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        """Auto-generate code if not provided"""
        if not self.code:
            # Generate code from program type
            code_map = {
                'pre_school': 'PRE',
                'primary': 'PRI',
                'junior_secondary': 'JSS',
                'senior_secondary': 'SSS',
                'special_education': 'SPE',
                'adult_education': 'ADE',
                'vocational': 'VOC',
            }
            self.code = code_map.get(self.program_type, 'GEN')

        super().save(*args, **kwargs)

    def get_class_levels(self):
        """Get all class levels in this program"""
        return self.class_levels.all()

    def get_active_subjects(self):
        """Get all subjects in this program"""
        return Subject.objects.filter(programs=self, is_active=True)


class ClassLevel(models.Model):
    """
    Class Level Model
    Represents specific class levels within a program
    """

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='class_levels',
        help_text="Parent academic program"
    )

    LEVEL_CHOICES = [
        # Pre-School Levels
        ('creche', 'Creche (0-2 years)'),
        ('playgroup', 'Playgroup (2-3 years)'),
        ('nursery_1', 'Nursery 1 (3-4 years)'),
        ('nursery_2', 'Nursery 2 (4-5 years)'),
        ('kg_1', 'Kindergarten 1 (KG 1)'),
        ('kg_2', 'Kindergarten 2 (KG 2)'),

        # Primary School Levels
        ('primary_1', 'Primary 1 (Basic 1)'),
        ('primary_2', 'Primary 2 (Basic 2)'),
        ('primary_3', 'Primary 3 (Basic 3)'),
        ('primary_4', 'Primary 4 (Basic 4)'),
        ('primary_5', 'Primary 5 (Basic 5)'),
        ('primary_6', 'Primary 6 (Basic 6)'),

        # Junior Secondary Levels
        ('jss_1', 'JSS 1 (Junior Secondary 1)'),
        ('jss_2', 'JSS 2 (Junior Secondary 2)'),
        ('jss_3', 'JSS 3 (Junior Secondary 3)'),

        # Senior Secondary Levels
        ('sss_1', 'SSS 1 (Senior Secondary 1)'),
        ('sss_2', 'SSS 2 (Senior Secondary 2)'),
        ('sss_3', 'SSS 3 (Senior Secondary 3)'),
    ]

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, help_text="Class level")
    name = models.CharField(max_length=100, help_text="Level display name (e.g., Primary 1)")
    code = models.CharField(max_length=20, unique=True, help_text="Level code (e.g., P1, JSS1, SSS1)")
    order = models.IntegerField(default=0, help_text="Sorting order within program")

    # Age Information
    min_age = models.IntegerField(default=0, help_text="Minimum age for this level")
    max_age = models.IntegerField(default=0, help_text="Maximum age for this level")

    # Academic Requirements
    required_previous_level = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_levels',
        help_text="Previous level required for promotion"
    )
    is_promotion_level = models.BooleanField(default=False, help_text="Is this a promotion/examination level?")
    is_active = models.BooleanField(default=True, help_text="Is this level currently active?")
    description = models.TextField(blank=True, help_text="Level description and objectives")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['program__program_type', 'order']
        verbose_name = 'Class Level'
        verbose_name_plural = 'Class Levels'
        unique_together = ['program', 'level']

    def __str__(self):
        return f"{self.name} - {self.program.name}"

    def save(self, *args, **kwargs):
        """Auto-generate code and name if not provided"""
        if not self.code:
            # Generate code from level
            code_map = {
                'creche': 'CRE',
                'playgroup': 'PLG',
                'nursery_1': 'NUR1',
                'nursery_2': 'NUR2',
                'kg_1': 'KG1',
                'kg_2': 'KG2',
                'primary_1': 'P1',
                'primary_2': 'P2',
                'primary_3': 'P3',
                'primary_4': 'P4',
                'primary_5': 'P5',
                'primary_6': 'P6',
                'jss_1': 'JSS1',
                'jss_2': 'JSS2',
                'jss_3': 'JSS3',
                'sss_1': 'SSS1',
                'sss_2': 'SSS2',
                'sss_3': 'SSS3',
            }
            self.code = code_map.get(self.level, self.level.upper())

        if not self.name:
            # Generate name from level
            name_map = {
                'creche': 'Creche',
                'playgroup': 'Playgroup',
                'nursery_1': 'Nursery 1',
                'nursery_2': 'Nursery 2',
                'kg_1': 'Kindergarten 1',
                'kg_2': 'Kindergarten 2',
                'primary_1': 'Primary 1',
                'primary_2': 'Primary 2',
                'primary_3': 'Primary 3',
                'primary_4': 'Primary 4',
                'primary_5': 'Primary 5',
                'primary_6': 'Primary 6',
                'jss_1': 'JSS 1',
                'jss_2': 'JSS 2',
                'jss_3': 'JSS 3',
                'sss_1': 'SSS 1',
                'sss_2': 'SSS 2',
                'sss_3': 'SSS 3',
            }
            self.name = name_map.get(self.level, self.level.replace('_', ' ').title())

        super().save(*args, **kwargs)

    def get_next_level(self):
        """Get the next level for promotion"""
        try:
            return ClassLevel.objects.get(
                program=self.program,
                order=self.order + 1,
                is_active=True
            )
        except ClassLevel.DoesNotExist:
            return None


class Subject(models.Model):
    """
    Subject Model
    Represents academic subjects taught in the school
    """

    # Basic Information
    name = models.CharField(max_length=200, unique=True, help_text="Subject name (e.g., Mathematics)")
    code = models.CharField(max_length=20, unique=True, help_text="Subject code (e.g., MAT, ENG, PHY)")
    short_name = models.CharField(max_length=50, blank=True, help_text="Short name or abbreviation")

    # Academic Classification
    SUBJECT_TYPE_CHOICES = [
        ('core', 'Core Subject'),
        ('elective', 'Elective Subject'),
        ('vocational', 'Vocational Subject'),
        ('extra_curricular', 'Extra-Curricular'),
        ('religious', 'Religious Studies'),
        ('language', 'Language'),
        ('science', 'Science'),
        ('arts', 'Arts/Humanities'),
        ('commercial', 'Commercial/Business'),
        ('technical', 'Technical'),
        ('general', 'General Studies'),
    ]

    subject_type = models.CharField(max_length=30, choices=SUBJECT_TYPE_CHOICES, default='core',
                                    help_text="Type of subject")

    # Program and Level Association
    programs = models.ManyToManyField(
        Program,
        related_name='subjects',
        blank=True,
        help_text="Programs where this subject is taught"
    )

    class_levels = models.ManyToManyField(
        ClassLevel,
        related_name='subjects',
        blank=True,
        help_text="Class levels where this subject is taught"
    )

    # For Senior Secondary Streams
    STREAM_CHOICES = [
        ('science', 'Science Stream'),
        ('commercial', 'Commercial Stream'),
        ('arts', 'Arts/Humanities Stream'),
        ('general', 'General (All Streams)'),
        ('technical', 'Technical Stream'),
    ]

    stream = models.CharField(max_length=20, choices=STREAM_CHOICES, default='general',
                              help_text="Stream specialization (for Senior Secondary)")

    # Curriculum Information
    curriculum = models.CharField(max_length=100, blank=True,
                                  help_text="Curriculum specification (e.g., WAEC, NECO, BECE)")
    syllabus = models.FileField(upload_to='syllabus/', blank=True, null=True, help_text="Subject syllabus document")

    # Teaching Information
    periods_per_week = models.IntegerField(default=5, help_text="Number of teaching periods per week")
    minutes_per_period = models.IntegerField(default=40, help_text="Duration of each period in minutes")
    total_teaching_hours = models.IntegerField(default=0, help_text="Total teaching hours per term")

    # Assessment Information
    has_continuous_assessment = models.BooleanField(default=True,
                                                    help_text="Does this subject have continuous assessment?")
    ca_weight = models.IntegerField(default=30, help_text="Continuous assessment weight (%)")
    exam_weight = models.IntegerField(default=70, help_text="Examination weight (%)")

    # Nigerian Specific Fields
    is_compulsory = models.BooleanField(default=False, help_text="Is this a compulsory subject?")
    is_examinable = models.BooleanField(default=True, help_text="Is this subject examinable?")
    is_practical = models.BooleanField(default=False, help_text="Does this subject have practical components?")

    # Subject Grouping (for WAEC/NECO combinations)
    subject_group = models.CharField(max_length=100, blank=True, help_text="Subject group/combination")

    # Status
    is_active = models.BooleanField(default=True, help_text="Is this subject currently active?")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_subjects',
        help_text="User who created this subject"
    )
    description = models.TextField(blank=True, help_text="Subject description and objectives")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code', 'name']
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        indexes = [
            models.Index(fields=['subject_type']),
            models.Index(fields=['stream']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        """Auto-generate code and calculate teaching hours"""
        if not self.code:
            # Generate code from name
            words = self.name.split()
            if len(words) >= 2:
                self.code = ''.join(word[0].upper() for word in words[:3])
            else:
                self.code = self.name[:3].upper()

        # Calculate total teaching hours
        self.total_teaching_hours = (
                                            self.periods_per_week *
                                            self.minutes_per_period *
                                            13  # Assuming 13 weeks per term
                                    ) // 60

        super().save(*args, **kwargs)

    def get_program_names(self):
        """Get list of program names"""
        return [p.name for p in self.programs.all()]

    def get_class_level_names(self):
        """Get list of class level names"""
        return [cl.name for cl in self.class_levels.all()]

    def can_be_taught_by(self, teacher):
        """Check if a teacher can teach this subject"""
        from staff.models import TeacherProfile

        if not hasattr(teacher, 'staff_profile'):
            return False

        try:
            teacher_profile = teacher.staff_profile.teacher_profile
            subjects_list = teacher_profile.get_subjects_list()
            return self.code in subjects_list or self.name in subjects_list
        except TeacherProfile.DoesNotExist:
            return False


class Class(models.Model):
    """
    Class Model
    Represents a specific class section in a particular academic session
    """

    # Basic Information
    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name='classes',
        help_text="Academic session"
    )

    term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name='classes',
        help_text="Academic term"
    )

    class_level = models.ForeignKey(
        ClassLevel,
        on_delete=models.CASCADE,
        related_name='classes',
        help_text="Class level"
    )

    name = models.CharField(max_length=100, help_text="Class name (e.g., Primary 1A, JSS 1B)")
    code = models.CharField(max_length=20, help_text="Class code (e.g., P1A-2024-1)")
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text="URL-friendly class identifier")

    # Class Capacity
    max_capacity = models.IntegerField(default=40, help_text="Maximum number of students")
    current_enrollment = models.IntegerField(default=0, help_text="Current number of enrolled students")

    # Class Teachers
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes_taught',
        help_text="Primary class teacher"
    )

    assistant_class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_classes',
        help_text="Assistant class teacher"
    )

    # Location
    room_number = models.CharField(max_length=20, blank=True, help_text="Classroom number/building")
    building = models.CharField(max_length=100, blank=True, help_text="Building name")
    floor = models.CharField(max_length=20, blank=True, help_text="Floor/level")

    # Stream Information (for Senior Secondary)
    STREAM_CHOICES = [
        ('science', 'Science'),
        ('commercial', 'Commercial'),
        ('arts', 'Arts/Humanities'),
        ('general', 'General'),
        ('technical', 'Technical'),
    ]

    stream = models.CharField(max_length=20, choices=STREAM_CHOICES, blank=True,
                              help_text="Class stream (for Senior Secondary)")

    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('archived', 'Archived'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', help_text="Class status")
    is_active = models.BooleanField(default=True, help_text="Is this class currently active?")

    # Important Dates
    start_date = models.DateField(null=True, blank=True, help_text="Class start date")
    end_date = models.DateField(null=True, blank=True, help_text="Class end date")

    # Academic Information
    subjects = models.ManyToManyField(
        Subject,
        related_name='classes',
        through='ClassSubject',
        blank=True,
        help_text="Subjects offered in this class"
    )

    # Additional Information
    description = models.TextField(blank=True, help_text="Class description and notes")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_classes',
        help_text="User who created this class"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_level__order', 'name']
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        unique_together = ['session', 'term', 'class_level', 'name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['class_level']),
        ]

    def __str__(self):
        term_display = self.term.get_term_display() if self.term else "No Term"
        session_name = self.session.name if self.session else "No Session"
        return f"{self.name} - {session_name} ({term_display})"

    def save(self, *args, **kwargs):
        """Auto-generate code and slug"""
        if not self.code:
            # Generate unique class code
            year = self.session.start_date.year
            term_code = {'first': 'T1', 'second': 'T2', 'third': 'T3'}.get(self.term.term, 'TX')
            self.code = f"{self.class_level.code}-{self.name}-{year}-{term_code}"

        if not self.slug:
            self.slug = slugify(f"{self.code}-{self.session.name}")

        # Ensure term belongs to session
        if self.term.session != self.session:
            raise ValidationError("Term must belong to the selected session")

        super().save(*args, **kwargs)

    def get_available_seats(self):
        """Get number of available seats"""
        return self.max_capacity - self.current_enrollment

    def is_full(self):
        """Check if class is full"""
        return self.current_enrollment >= self.max_capacity

    def get_enrolled_students(self):
        """Get all students enrolled in this class"""
        # Use string reference
        from students.models import StudentEnrollment
        return StudentEnrollment.objects.filter(
            class_obj=self,
            status='active'
        ).select_related('student__user')

    def get_subject_teachers(self):
        """Get all teachers assigned to subjects in this class"""
        teachers = set()
        for class_subject in self.class_subjects.all():
            if class_subject.teacher:
                teachers.add(class_subject.teacher)
        return list(teachers)

    def can_enroll_student(self, student):
        """Check if a student can be enrolled in this class"""
        # Use string reference
        from students.models import Student
        from students.models import StudentEnrollment

        if not isinstance(student, Student):
            return False

        # Check age requirements
        if student.user.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - student.user.date_of_birth.year

            if (self.class_level.min_age and age < self.class_level.min_age) or \
                    (self.class_level.max_age and age > self.class_level.max_age):
                return False

        # Check if class is full
        if self.is_full():
            return False

        # Check if student is already enrolled in this session/term
        from students.models import StudentEnrollment
        existing_enrollment = StudentEnrollment.objects.filter(
            student=student.user,
            session=self.session,
            term=self.term,
            class_obj=self
        ).exists()

        if existing_enrollment:
            return False

        return True


class ClassSubject(models.Model):
    """
    Class-Subject Assignment Model
    Links subjects to specific classes with teacher assignments
    """

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_subjects',
        help_text="Class"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='class_assignments',
        help_text="Subject"
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_assignments',
        help_text="Assigned teacher"
    )

    co_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='co_teaching_assignments',
        help_text="Co-teacher"
    )

    # Academic Period
    start_date = models.DateField(null=True, blank=True, help_text="Teaching start date")
    end_date = models.DateField(null=True, blank=True, help_text="Teaching end date")

    # Teaching Schedule
    periods_per_week = models.IntegerField(default=0, help_text="Actual periods per week")
    preferred_days = models.CharField(max_length=100, blank=True, help_text="Preferred teaching days (comma-separated)")
    preferred_times = models.CharField(max_length=100, blank=True, help_text="Preferred teaching times")

    # Status
    is_active = models.BooleanField(default=True, help_text="Is this assignment currently active?")
    is_compulsory = models.BooleanField(default=False, help_text="Is this subject compulsory for this class?")

    # Assessment Settings
    ca_required = models.BooleanField(default=True, help_text="Continuous assessment required?")
    exam_required = models.BooleanField(default=True, help_text="Examination required?")

    # Notes
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_class_subjects',
        help_text="User who created this assignment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_obj', 'subject']
        verbose_name = 'Class Subject Assignment'
        verbose_name_plural = 'Class Subject Assignments'
        unique_together = ['class_obj', 'subject']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['teacher']),
        ]

    def __str__(self):
        return f"{self.class_obj.name} - {self.subject.name}"

    def save(self, *args, **kwargs):
        """Validate teacher assignment"""
        # Ensure teacher is a staff member
        if self.teacher and self.teacher.role not in ['teacher', 'form_teacher', 'subject_teacher',
                                                      'head', 'principal', 'vice_principal']:
            raise ValidationError("Assigned teacher must have a teaching role")

        # Ensure teacher can teach this subject
        if self.teacher and self.subject:
            if not self.subject.can_be_taught_by(self.teacher):
                raise ValidationError(f"Teacher {self.teacher.get_full_name()} cannot teach {self.subject.name}")

        # Set default periods if not specified
        if not self.periods_per_week:
            self.periods_per_week = self.subject.periods_per_week

        super().save(*args, **kwargs)

    def get_preferred_days_list(self):
        """Get list of preferred days"""
        if self.preferred_days:
            return [day.strip() for day in self.preferred_days.split(',')]
        return []

    def can_teacher_edit(self, teacher):
        """Check if teacher can edit this assignment"""
        return self.teacher == teacher or self.co_teacher == teacher


class Timetable(models.Model):
    """
    Timetable Model
    Weekly timetable for classes and teachers
    """

    # Basic Information
    name = models.CharField(max_length=200, help_text="Timetable name (e.g., Primary School Timetable Term 1 2024)")
    code = models.CharField(max_length=50, unique=True, help_text="Timetable code")
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='timetables',
                                help_text="Academic session")
    term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE, related_name='timetables',
                             help_text="Academic term")

    # Scope
    SCOPE_CHOICES = [
        ('school', 'Whole School'),
        ('program', 'Program'),
        ('class_level', 'Class Level'),
        ('class', 'Class'),
        ('teacher', 'Teacher'),
    ]

    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='class', help_text="Timetable scope")

    # Target (based on scope)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True, blank=True, related_name='timetables',
                                help_text="Target program (if scope is program)")
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='timetables', help_text="Target class level (if scope is class_level)")
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True, related_name='timetables',
                                  help_text="Target class (if scope is class)")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='timetables', help_text="Target teacher (if scope is teacher)")

    # Timetable Configuration
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]

    days = models.CharField(max_length=200, default='monday,tuesday,wednesday,thursday,friday',
                            help_text="School days (comma-separated)")
    periods_per_day = models.IntegerField(default=8, help_text="Number of periods per day")
    period_duration = models.IntegerField(default=40, help_text="Duration of each period in minutes")
    break_periods = models.CharField(max_length=100, default='4',
                                     help_text="Period numbers for breaks (comma-separated)")
    lunch_period = models.IntegerField(default=5, help_text="Lunch period number")
    assembly_period = models.IntegerField(default=1, help_text="Assembly period number")

    # Schedule Information
    start_time = models.TimeField(default='08:00', help_text="School start time")
    end_time = models.TimeField(default='15:00', help_text="School end time")

    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', help_text="Timetable status")
    is_active = models.BooleanField(default=False, help_text="Is this the active timetable?")
    is_locked = models.BooleanField(default=False, help_text="Is timetable locked from edits?")

    # Version Control
    version = models.CharField(max_length=20, default='1.0', help_text="Timetable version")
    parent_timetable = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='revisions', help_text="Parent timetable for versioning")

    # Approval Workflow
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_timetables', help_text="User who approved this timetable")
    approved_date = models.DateTimeField(null=True, blank=True, help_text="Approval date")

    # Additional Information
    description = models.TextField(blank=True, help_text="Timetable description and notes")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_timetables', help_text="User who created this timetable")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-session__start_date', '-term__term', 'name']
        verbose_name = 'Timetable'
        verbose_name_plural = 'Timetables'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['scope']),
        ]

    def __str__(self):
        return f"{self.name} - {self.session.name} ({self.term.get_term_display()})"

    def save(self, *args, **kwargs):
        """Auto-generate code and ensure only one active timetable per scope"""
        if not self.code:
            # Generate unique timetable code
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            scope_code = self.scope[:3].upper()
            self.code = f"TT-{scope_code}-{timestamp}"

        # Ensure only one active timetable per scope
        if self.is_active:
            # Find other active timetables with same scope and target
            filter_kwargs = {
                'is_active': True,
                'scope': self.scope,
                'session': self.session,
                'term': self.term,
            }

            # Add target filter based on scope
            if self.scope == 'program' and self.program:
                filter_kwargs['program'] = self.program
            elif self.scope == 'class_level' and self.class_level:
                filter_kwargs['class_level'] = self.class_level
            elif self.scope == 'class' and self.class_obj:
                filter_kwargs['class_obj'] = self.class_obj
            elif self.scope == 'teacher' and self.teacher:
                filter_kwargs['teacher'] = self.teacher

            # Exclude self from update
            if self.pk:
                filter_kwargs['pk__ne'] = self.pk

            # Deactivate other timetables
            Timetable.objects.filter(**filter_kwargs).update(is_active=False)

        # Validate scope-target consistency
        self._validate_scope_target()

        super().save(*args, **kwargs)

    def _validate_scope_target(self):
        """Validate that target matches scope"""
        if self.scope == 'program' and not self.program:
            raise ValidationError("Program scope requires a program target")
        elif self.scope == 'class_level' and not self.class_level:
            raise ValidationError("Class level scope requires a class level target")
        elif self.scope == 'class' and not self.class_obj:
            raise ValidationError("Class scope requires a class target")
        elif self.scope == 'teacher' and not self.teacher:
            raise ValidationError("Teacher scope requires a teacher target")

    def get_days_list(self):
        """Get list of days"""
        return [day.strip() for day in self.days.split(',')]

    def get_break_periods_list(self):
        """Get list of break periods"""
        return [int(p.strip()) for p in self.break_periods.split(',')]

    def generate_period_schedule(self):
        """Generate period schedule with times"""
        from datetime import datetime, timedelta

        schedule = []
        start_time = datetime.combine(datetime.today(), self.start_time)

        for period in range(1, self.periods_per_day + 1):
            period_end = start_time + timedelta(minutes=self.period_duration)

            schedule.append({
                'period': period,
                'start_time': start_time.time(),
                'end_time': period_end.time(),
                'is_break': period in self.get_break_periods_list(),
                'is_lunch': period == self.lunch_period,
                'is_assembly': period == self.assembly_period,
            })

            start_time = period_end

        return schedule


class TimetableEntry(models.Model):
    """
    Timetable Entry Model
    Individual period entries in a timetable
    """

    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='entries',
                                  help_text="Parent timetable")

    # Period Information
    day = models.CharField(max_length=20, choices=Timetable.DAY_CHOICES, help_text="Day of the week")
    period_number = models.IntegerField(help_text="Period number (1-10)")

    # Subject Assignment
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='timetable_entries', help_text="Subject for this period")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='timetable_periods', help_text="Teacher for this period")
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='timetable_entries', help_text="Class for this period")

    # Room Information
    room = models.CharField(max_length=50, blank=True, help_text="Room/venue")

    # Entry Type
    ENTRY_TYPE_CHOICES = [
        ('subject', 'Subject Teaching'),
        ('assembly', 'Assembly'),
        ('break', 'Break Time'),
        ('lunch', 'Lunch Break'),
        ('sports', 'Sports/Games'),
        ('club', 'Club Activity'),
        ('study', 'Study Period'),
        ('test', 'Test/Examination'),
        ('meeting', 'Staff Meeting'),
        ('other', 'Other Activity'),
    ]

    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES, default='subject',
                                  help_text="Type of timetable entry")

    # Status
    is_active = models.BooleanField(default=True, help_text="Is this entry active?")
    is_locked = models.BooleanField(default=False, help_text="Is this entry locked from changes?")

    # Notes
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_timetable_entries', help_text="User who created this entry")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['timetable', 'day', 'period_number']
        verbose_name = 'Timetable Entry'
        verbose_name_plural = 'Timetable Entries'
        unique_together = ['timetable', 'day', 'period_number', 'class_obj']
        indexes = [
            models.Index(fields=['day', 'period_number']),
            models.Index(fields=['teacher']),
            models.Index(fields=['subject']),
        ]

    def __str__(self):
        if self.subject:
            return f"{self.day} - Period {self.period_number}: {self.subject.name}"
        return f"{self.day} - Period {self.period_number}: {self.get_entry_type_display()}"

    def save(self, *args, **kwargs):
        """Validate timetable entry"""
        # Validate period number
        if self.period_number < 1 or self.period_number > self.timetable.periods_per_day:
            raise ValidationError(f"Period number must be between 1 and {self.timetable.periods_per_day}")

        # Validate teacher assignment
        if self.teacher and self.subject:
            if not self.subject.can_be_taught_by(self.teacher):
                raise ValidationError(f"Teacher {self.teacher.get_full_name()} cannot teach {self.subject.name}")

        super().save(*args, **kwargs)