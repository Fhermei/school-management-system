from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string
from django.db.models import Q


class Parent(models.Model):
    """
    Parent Model - Nigerian School System
    Parents can have multiple students
    """

    # Link to main User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        help_text="Linked user account"
    )

    # Parent Type
    PARENT_TYPE_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('relative', 'Relative'),
        ('other', 'Other'),
    ]

    parent_type = models.CharField(max_length=20, choices=PARENT_TYPE_CHOICES, default='father',
                                   help_text="Type of parent relationship")

    # Personal Information
    occupation = models.CharField(max_length=100, blank=True, help_text="Parent's occupation")
    employer = models.CharField(max_length=200, blank=True, help_text="Name of employer")
    employer_address = models.TextField(blank=True, help_text="Employer's address")
    office_phone = models.CharField(max_length=15, blank=True, help_text="Office phone number")

    # Marital Status
    MARITAL_STATUS_CHOICES = [
        ('married', 'Married'),
        ('single', 'Single'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]

    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, default='married',
                                      help_text="Marital status")

    # Emergency Contact (other than spouse)
    emergency_contact_name = models.CharField(max_length=100, blank=True, help_text="Emergency contact person")
    emergency_contact_phone = models.CharField(max_length=15, blank=True, help_text="Emergency contact phone")
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, help_text="Relationship to family")

    # Communication Preferences
    COMMUNICATION_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('phone', 'Phone Call'),
        ('whatsapp', 'WhatsApp'),
        ('in_person', 'In Person'),
    ]

    preferred_communication = models.CharField(max_length=20, choices=COMMUNICATION_CHOICES, default='whatsapp',
                                               help_text="Preferred communication method")
    receive_sms_alerts = models.BooleanField(default=True, help_text="Receive SMS alerts about child")
    receive_email_alerts = models.BooleanField(default=True, help_text="Receive email alerts about child")

    # Financial Information
    INCOME_RANGE_CHOICES = [
        ('below_500k', 'Below ₦500,000'),
        ('500k_1m', '₦500,000 - ₦1 Million'),
        ('1m_3m', '₦1 Million - ₦3 Million'),
        ('3m_5m', '₦3 Million - ₦5 Million'),
        ('above_5m', 'Above ₦5 Million'),
        ('prefer_not', 'Prefer not to say'),
    ]

    annual_income_range = models.CharField(max_length=50, blank=True, choices=INCOME_RANGE_CHOICES,
                                           help_text="Annual income range")

    # Parent ID
    parent_id = models.CharField(max_length=20, unique=True, blank=True, help_text="Unique parent ID")

    # Bank Information (for fee payments)
    bank_name = models.CharField(max_length=100, blank=True, help_text="Bank name")
    account_name = models.CharField(max_length=100, blank=True, help_text="Account name")
    account_number = models.CharField(max_length=20, blank=True, help_text="Bank account number")

    # PTA (Parent-Teacher Association) Information
    is_pta_member = models.BooleanField(default=False, help_text="Is parent a PTA member?")
    pta_position = models.CharField(max_length=100, blank=True, help_text="PTA position/role")
    pta_committee = models.CharField(max_length=100, blank=True, help_text="PTA committee membership")

    # Relationship with other parent (if applicable)
    spouse = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='spouse_of',
        help_text="Spouse/Other parent"
    )

    # Status
    is_active = models.BooleanField(default=True, help_text="Is parent active?")
    is_verified = models.BooleanField(default=False, help_text="Has parent been verified by school?")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name']
        verbose_name = 'Parent'
        verbose_name_plural = 'Parents'
        indexes = [
            models.Index(fields=['parent_id']),
            models.Index(fields=['parent_type']),
            models.Index(fields=['is_pta_member']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_parent_type_display()})"

    def save(self, *args, **kwargs):
        """Auto-generate parent ID"""
        if not self.parent_id:
            prefix = "PAR"
            while True:
                random_num = ''.join(random.choices(string.digits, k=6))
                parent_id = f"{prefix}{random_num}"
                if not Parent.objects.filter(parent_id=parent_id).exists():
                    self.parent_id = parent_id
                    break

        # Update user's role to parent if not already
        if self.user.role != 'parent':
            self.user.role = 'parent'
            self.user.save()

        super().save(*args, **kwargs)

    def get_children(self):
        """Get all children/students of this parent"""
        # Use string reference to avoid circular import
        from students.models import Student

        children = Student.objects.filter(
            Q(father=self) | Q(mother=self)
        ).distinct()
        return children

    def get_children_count(self):
        """Get number of children in school"""
        return self.get_children().count()

    def get_fee_summary(self):
        """Get total fee summary for all children"""
        children = self.get_children()

        total_fee = sum(child.total_fee_amount for child in children)
        total_paid = sum(child.amount_paid for child in children)
        total_balance = sum(child.balance_due for child in children)

        return {
            'total_children': children.count(),
            'total_fee': float(total_fee),
            'total_paid': float(total_paid),
            'total_balance': float(total_balance),
        }