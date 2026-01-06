from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

class CustomUserAdmin(UserAdmin):
    """Custom admin interface for User model"""
    
    # Display fields in list view - Remove username
    list_display = ('registration_number', 'email', 'role', 
                    'get_full_name', 'is_active', 'is_staff', 'last_login')
    
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 
                   'gender', 'state_of_origin')
    search_fields = ('registration_number', 'email', 
                     'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('registration_number', 'last_login', 'login_count', 
                      'created_at', 'updated_at')
    
    # Fieldsets for different user roles
    fieldsets = (
        ('Login Credentials', {
            'fields': ('registration_number', 'password')  
        }),
        ('Personal Information', {
            'fields': (('first_name', 'last_name'), 'email', 'gender', 
                      'date_of_birth', 'phone_number', 'alternative_phone',
                      'profile_picture')
        }),
        ('Nigerian Details', {
            'fields': ('address', 'city', 'state_of_origin', 'lga', 'nationality')
        }),
        ('Role & Status', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 
                      'is_verified', 'groups', 'user_permissions')
        }),        
        ('System Information', {
            'fields': ('last_login', 'last_login_ip', 'login_count', 
                      'created_at', 'updated_at')
        }),
    )
    
    # Fields for adding new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('registration_number', 'email', 'role', 'password1', 'password2',
                      'first_name', 'last_name', 'phone_number'),
        }),
    )
    
    # Custom methods for display
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def profile_image(self, obj):
        if obj.profile_picture:
            return format_html(f'<img src="{obj.profile_picture.url}" width="50" height="50" />')
        return "No Image"
    profile_image.short_description = 'Profile Picture'
    
    # Actions for admin
    actions = ['activate_users', 'deactivate_users', 'verify_users']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} users activated successfully.")
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} users deactivated successfully.")
    deactivate_users.short_description = "Deactivate selected users"
    
    def verify_users(self, request, queryset):
        """Verify selected users"""
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} users verified successfully.")
    verify_users.short_description = "Verify selected users"

admin.site.register(User, CustomUserAdmin)


    