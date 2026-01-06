from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import random
import string

class CustomUserManager(BaseUserManager):
    """Custom user manager to handle user creation with registration numbers"""
    
    def create_user(self, registration_number=None, email=None, password=None, **extra_fields):
        """Create and save a regular user with registration number"""
        if not registration_number:
            # Generate registration number from first name if not provided
            if 'first_name' in extra_fields and extra_fields['first_name']:
                clean_name = ''.join(e for e in extra_fields['first_name'] if e.isalnum())
                prefix = clean_name[:4].lower() if clean_name else 'user'
                while len(prefix) < 4:
                    prefix += 'x'
                random_digits = ''.join(random.choices(string.digits, k=4))
                registration_number = f"{prefix}{random_digits}"
            else:
                raise ValueError('Either registration_number or first_name must be set')
        
        # Set registration number in extra_fields
        extra_fields['registration_number'] = registration_number
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, registration_number=None, email=None, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'head')  # Head of School is superuser
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(registration_number, email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model for School Management System (Nigeria Context)"""
    
    # Remove username field from AbstractUser
    username = None
    
    # Role Choices
    ROLE_CHOICES = (
        ('head', 'Head of School/Proprietor'),
        ('principal', 'Principal'),
        ('vice_principal', 'Vice Principal'),
        ('teacher', 'Teacher'),
        ('form_teacher', 'Form Teacher'),
        ('subject_teacher', 'Subject Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent/Guardian'),
        ('accountant', 'Accountant/Bursar'),
        ('secretary', 'Secretary'),
        ('librarian', 'Librarian'),
        ('laboratory', 'Laboratory Technician'),
        ('security', 'Security Personnel'),
        ('cleaner', 'Cleaner'),
    )
    
    # Gender Choices
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    
    # Nigerian States
    NIGERIAN_STATES = (
        ('abia', 'Abia'), ('adamawa', 'Adamawa'), ('akwa_ibom', 'Akwa Ibom'),
        ('anambra', 'Anambra'), ('bauchi', 'Bauchi'), ('bayelsa', 'Bayelsa'),
        ('benue', 'Benue'), ('borno', 'Borno'), ('cross_river', 'Cross River'),
        ('delta', 'Delta'), ('ebonyi', 'Ebonyi'), ('edo', 'Edo'),
        ('ekiti', 'Ekiti'), ('enugu', 'Enugu'), ('gombe', 'Gombe'),
        ('imo', 'Imo'), ('jigawa', 'Jigawa'), ('kaduna', 'Kaduna'),
        ('kano', 'Kano'), ('katsina', 'Katsina'), ('kebbi', 'Kebbi'),
        ('kogi', 'Kogi'), ('kwara', 'Kwara'), ('lagos', 'Lagos'),
        ('nasarawa', 'Nasarawa'), ('niger', 'Niger'), ('ogun', 'Ogun'),
        ('ondo', 'Ondo'), ('osun', 'Osun'), ('oyo', 'Oyo'),
        ('plateau', 'Plateau'), ('rivers', 'Rivers'), ('sokoto', 'Sokoto'),
        ('taraba', 'Taraba'), ('yobe', 'Yobe'), ('zamfara', 'Zamfara'),
        ('fct', 'Federal Capital Territory'),
    )
    
    # Core User Fields (Keep These)
    registration_number = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Auto-generated: first 4 letters of first name + 4 digits"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    alternative_phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Address Information (Keep These)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_of_origin = models.CharField(max_length=50, choices=NIGERIAN_STATES, blank=True)
    lga = models.CharField(max_length=100, blank=True, verbose_name="Local Government Area")
    nationality = models.CharField(max_length=50, default='Nigerian')
    
    # Status & Tracking (Keep These)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    login_count = models.IntegerField(default=0)
    
    # Timestamps (Keep These)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Set custom manager
    objects = CustomUserManager()
    
    # Use registration_number as the username field for authentication
    USERNAME_FIELD = 'registration_number'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.registration_number} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        """Auto-generate registration number if not set"""
        if not self.registration_number:
            # Generate from first name (first 4 letters) + 4 random digits
            if self.first_name:
                # Clean the first name
                clean_name = ''.join(e for e in self.first_name if e.isalnum())
                prefix = clean_name[:4].lower() if clean_name else 'user'
            else:
                prefix = 'user'
            
            # Ensure prefix is at least 4 characters
            while len(prefix) < 4:
                prefix += 'x'
            
            # Generate 4 random digits
            random_digits = ''.join(random.choices(string.digits, k=4))
            self.registration_number = f"{prefix}{random_digits}"
        
        super().save(*args, **kwargs)
    
    def get_display_name(self):
        """Get display name for the user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.registration_number
    
    def can_change_password(self):
        """Check if user can change password themselves"""
        # Only admin/principal/head can change passwords
        return self.role in ['head', 'principal', 'vice_principal']
    
    
    
