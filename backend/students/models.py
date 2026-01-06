from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string

class Student(models.Model):
    """
    Student Model - Nigerian School System
    Extends the main User model with student-specific fields
    """
    
    # Link to main User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        help_text="Linked user account"
    )
    
    # Academic Information
    CLASS_LEVEL_CHOICES = [
        ('pre_nursery', 'Pre-Nursery'),
        ('nursery_1', 'Nursery 1'),
        ('nursery_2', 'Nursery 2'),
        ('kg_1', 'Kindergarten 1'),
        ('kg_2', 'Kindergarten 2'),
        ('primary_1', 'Primary 1'),
        ('primary_2', 'Primary 2'),
        ('primary_3', 'Primary 3'),
        ('primary_4', 'Primary 4'),
        ('primary_5', 'Primary 5'),
        ('primary_6', 'Primary 6'),
        ('jss_1', 'JSS 1 (JS 1)'),
        ('jss_2', 'JSS 2 (JS 2)'),
        ('jss_3', 'JSS 3 (JS 3)'),
        ('sss_1', 'SSS 1 (SS 1)'),
        ('sss_2', 'SSS 2 (SS 2)'),
        ('sss_3', 'SSS 3 (SS 3)'),
    ]
    
    class_level = models.CharField(
        max_length=20,
        choices=CLASS_LEVEL_CHOICES,
        default='primary_1',
        help_text="Current class/grade level"
    )
    
    # Secondary School Stream (Only for JSS 3 and above)
    STREAM_CHOICES = [
        ('science', 'Science'),
        ('commercial', 'Commercial'),
        ('art', 'Arts/Humanities'),
        ('general', 'General (No stream yet)'),
        ('technical', 'Technical'),
        ('none', 'Not Applicable (Primary School)'),
    ]
    
    stream = models.CharField(
        max_length=20,
        choices=STREAM_CHOICES,
        default='none',
        help_text="Secondary school stream (Science/Commercial/Arts)"
    )
    
    # School Information
    admission_date = models.DateField(
        default=timezone.now,
        help_text="Date student was admitted"
    )
    admission_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="School admission number (e.g., ADM/2024/001)"
    )
    student_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="School-specific student ID"
    )
    
    # House/Group System (Common in Nigerian Schools)
    HOUSE_CHOICES = [
        ('red', 'Red House'),
        ('blue', 'Blue House'),
        ('green', 'Green House'),
        ('yellow', 'Yellow House'),
        ('purple', 'Purple House'),
        ('orange', 'Orange House'),
        ('none', 'No House Assigned'),
    ]
    
    house = models.CharField(
        max_length=20,
        choices=HOUSE_CHOICES,
        default='none',
        help_text="House/Group assignment"
    )
    
    # Academic Performance
    previous_class = models.CharField(
        max_length=50,
        blank=True,
        help_text="Previous class attended"
    )
    previous_school = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of previous school"
    )
    transfer_certificate_no = models.CharField(
        max_length=50,
        blank=True,
        help_text="Transfer certificate number"
    )
    
    # Prefect/Leadership Roles
    is_prefect = models.BooleanField(
        default=False,
        help_text="Is this student a prefect?"
    )
    prefect_role = models.CharField(
        max_length=100,
        blank=True,
        help_text="Prefect role/position"
    )
    
    # Student Category
    STUDENT_CATEGORY_CHOICES = [
        ('day', 'Day Student'),
        ('boarding', 'Boarding Student'),
        ('special_needs', 'Special Needs Student'),
        ('scholarship', 'Scholarship Student'),
        ('repeat', 'Repeating Student'),
        ('new', 'New Student'),
    ]
    
    student_category = models.CharField(
        max_length=20,
        choices=STUDENT_CATEGORY_CHOICES,
        default='day',
        help_text="Student category/type"
    )
    
    # Parent/Legal Guardian Links
    father = models.ForeignKey(
        'parents.Parent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='father_of_students',
        help_text="Father/Guardian (Male)"
    )
    
    mother = models.ForeignKey(
        'parents.Parent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mother_of_students',
        help_text="Mother/Guardian (Female)"
    )
    
    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Emergency contact person"
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        blank=True,
        help_text="Emergency contact phone"
    )
    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True,
        help_text="Relationship to student"
    )
    
    # Fee Information
    FEE_STATUS_CHOICES = [
        ('paid_full', 'Paid in Full'),
        ('paid_partial', 'Partially Paid'),
        ('not_paid', 'Not Paid'),
        ('scholarship', 'On Scholarship'),
        ('exempted', 'Fee Exempted'),
    ]
    
    fee_status = models.CharField(
        max_length=20,
        choices=FEE_STATUS_CHOICES,
        default='not_paid',
        help_text="Current fee payment status"
    )
    
    total_fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total fee amount for the term"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Amount paid so far"
    )
    balance_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Remaining balance to pay"
    )
    
    # Fee Payment Evidence
    fee_payment_evidence = models.ImageField(
        upload_to='fee_evidence/',
        blank=True,
        null=True,
        help_text="Upload payment receipt/evidence"
    )
    last_payment_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date of last fee payment"
    )
    
    # Academic Progress
    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Current average score"
    )
    overall_grade = models.CharField(
        max_length=5,
        blank=True,
        help_text="Overall grade (A, B, C, etc.)"
    )
    position_in_class = models.PositiveIntegerField(
        default=0,
        help_text="Position in class (rank)"
    )
    
    # Health Information
    blood_group = models.CharField(
        max_length=5,
        blank=True,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ]
    )
    genotype = models.CharField(
        max_length=3,
        blank=True,
        choices=[
            ('AA', 'AA'), ('AS', 'AS'),
            ('SS', 'SS'), ('AC', 'AC'),
        ]
    )
    medical_conditions = models.TextField(
        blank=True,
        help_text="Any known medical conditions"
    )
    allergies = models.TextField(
        blank=True,
        help_text="Any allergies"
    )
    
    # Transportation
    TRANSPORT_CHOICES = [
        ('school_bus', 'School Bus'),
        ('parent_drop', 'Parent Drop-off'),
        ('public_transport', 'Public Transport'),
        ('walk', 'Walks to School'),
        ('other', 'Other'),
    ]
    
    transportation_mode = models.CharField(
        max_length=20,
        choices=TRANSPORT_CHOICES,
        default='parent_drop',
        help_text="Mode of transportation to school"
    )
    bus_route = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bus route (if using school bus)"
    )
    
    # Status Flags
    is_active = models.BooleanField(
        default=True,
        help_text="Is student currently active/enrolled?"
    )
    is_graduated = models.BooleanField(
        default=False,
        help_text="Has student graduated?"
    )
    graduation_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date of graduation"
    )
    
    # Attendance Tracking
    days_present = models.PositiveIntegerField(
        default=0,
        help_text="Total days present"
    )
    days_absent = models.PositiveIntegerField(
        default=0,
        help_text="Total days absent"
    )
    days_late = models.PositiveIntegerField(
        default=0,
        help_text="Total days late"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_level', 'user__first_name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        indexes = [
            models.Index(fields=['admission_number']),
            models.Index(fields=['class_level']),
            models.Index(fields=['stream']),
            models.Index(fields=['fee_status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_class_level_display()}"
    
    def save(self, *args, **kwargs):
        """Auto-generate fields and calculate balances"""
        
        # Auto-generate admission number if not set
        if not self.admission_number:
            year = timezone.now().year
            # Generate unique admission number
            while True:
                random_num = ''.join(random.choices(string.digits, k=4))
                admission_num = f"ADM/{year}/{random_num}"
                if not Student.objects.filter(admission_number=admission_num).exists():
                    self.admission_number = admission_num
                    break
        
        # Auto-generate student ID if not set
        if not self.student_id:
            prefix = "STU"
            while True:
                random_num = ''.join(random.choices(string.digits, k=6))
                student_id = f"{prefix}{random_num}"
                if not Student.objects.filter(student_id=student_id).exists():
                    self.student_id = student_id
                    break
        
        # Calculate balance
        self.balance_due = self.total_fee_amount - self.amount_paid
        
        # Update fee status based on payments
        if self.amount_paid >= self.total_fee_amount:
            self.fee_status = 'paid_full'
        elif self.amount_paid > 0:
            self.fee_status = 'paid_partial'
        else:
            self.fee_status = 'not_paid'
        
        # Update user's role to student if not already
        if self.user.role != 'student':
            self.user.role = 'student'
            self.user.save()
        
        super().save(*args, **kwargs)
    
    def get_parents(self):
        """Get both parents if available"""
        parents = []
        if self.father:
            parents.append(self.father)
        if self.mother:
            parents.append(self.mother)
        return parents
    
    def get_fee_summary(self):
        """Get fee payment summary"""
        return {
            'total_fee': float(self.total_fee_amount),
            'paid': float(self.amount_paid),
            'balance': float(self.balance_due),
            'status': self.get_fee_status_display(),
            'percentage_paid': (self.amount_paid / self.total_fee_amount * 100) if self.total_fee_amount > 0 else 0
        }
    
    def can_edit_profile(self, user):
        """
        Check if user can edit this student's profile
        Only admin/principal/accountant can edit student info
        """
        allowed_roles = ['head', 'principal', 'vice_principal', 'accountant', 'secretary']
        return user.role in allowed_roles or user.is_staff
    
    def get_academic_level(self):
        """Get academic level category"""
        if self.class_level in ['pre_nursery', 'nursery_1', 'nursery_2', 'kg_1', 'kg_2']:
            return 'Pre-School'
        elif self.class_level in ['primary_1', 'primary_2', 'primary_3', 'primary_4', 'primary_5', 'primary_6']:
            return 'Primary School'
        elif self.class_level in ['jss_1', 'jss_2', 'jss_3']:
            return 'Junior Secondary'
        else:
            return 'Senior Secondary'