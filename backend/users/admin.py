from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import User


class CustomUserAdmin(UserAdmin):
    """Custom admin interface for User model"""

    # Display fields in list view
    list_display = ('registration_number', 'email', 'role',
                    'get_full_name', 'is_active', 'is_staff',
                    'is_verified', 'last_login', 'created_at')

    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser',
                   'gender', 'state_of_origin', 'is_verified')

    search_fields = ('registration_number', 'email',
                     'first_name', 'last_name', 'phone_number')

    ordering = ('-created_at',)

    readonly_fields = ('registration_number', 'last_login', 'login_count',
                       'last_login_ip', 'created_at', 'updated_at')

    # Fieldsets for different user roles
    fieldsets = (
        ('Login Credentials', {
            'fields': ('registration_number', 'email', 'password')
        }),

        ('Personal Information', {
            'fields': (('first_name', 'last_name'), 'gender',
                       'date_of_birth', 'phone_number', 'alternative_phone',
                       'profile_picture')
        }),

        ('Nigerian Details', {
            'fields': ('address', 'city', 'state_of_origin', 'lga', 'nationality')
        }),

        ('Role & Status', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser',
                       'is_verified')
        }),

        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),

        ('System Information', {
            'fields': ('last_login', 'last_login_ip', 'login_count',
                       'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Fields for adding new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('registration_number', 'email', 'role', 'password1', 'password2',
                       'first_name', 'last_name', 'gender', 'phone_number', 'is_active'),
        }),
    )

    # Custom methods for display
    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'

    def profile_image(self, obj):
        if obj.profile_picture:
            return format_html(
                f'<img src="{obj.profile_picture.url}" width="50" height="50" style="border-radius: 50%;" />')
        return "No Image"

    profile_image.short_description = 'Profile'

    # Custom actions
    actions = ['activate_users', 'deactivate_users', 'verify_users',
               'make_staff', 'remove_staff']

    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated successfully.")

    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated successfully.")

    deactivate_users.short_description = "Deactivate selected users"

    def verify_users(self, request, queryset):
        """Verify selected users"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} user(s) verified successfully.")

    verify_users.short_description = "Verify selected users"

    def make_staff(self, request, queryset):
        """Make selected users staff"""
        updated = queryset.update(is_staff=True)
        self.message_user(request, f"{updated} user(s) granted staff status.")

    make_staff.short_description = "Grant staff status"

    def remove_staff(self, request, queryset):
        """Remove staff status from selected users"""
        # Prevent removing staff status from superusers
        non_superusers = queryset.filter(is_superuser=False)
        updated = non_superusers.update(is_staff=False)
        self.message_user(request, f"{updated} user(s) removed from staff.")

    remove_staff.short_description = "Remove staff status"

    # Custom filters
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete users
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)


admin.site.register(User, CustomUserAdmin)