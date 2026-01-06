from django.contrib import admin
from django.utils.html import format_html
from .models import Parent


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    """Admin interface for Parent model"""

    list_display = (
        'get_full_name', 'parent_id', 'get_parent_type',
        'occupation', 'children_count', 'is_pta_member',
        'is_active', 'created_at'
    )
    list_filter = (
        'parent_type', 'marital_status', 'is_pta_member',
        'is_active', 'is_verified'
    )
    search_fields = (
        'user__first_name', 'user__last_name',
        'parent_id', 'occupation', 'employer'
    )
    readonly_fields = ('parent_id', 'created_at', 'updated_at')
    list_per_page = 50

    fieldsets = (
        ('Parent Information', {
            'fields': ('user', 'parent_id', 'parent_type')
        }),
        ('Personal Details', {
            'fields': ('occupation', 'employer', 'employer_address', 'office_phone')
        }),
        ('Family Information', {
            'fields': ('marital_status', 'spouse')
        }),
        ('Communication', {
            'fields': (
                'preferred_communication', 'receive_sms_alerts',
                'receive_email_alerts', 'emergency_contact_name',
                'emergency_contact_phone', 'emergency_contact_relationship'
            )
        }),
        ('Financial Information', {
            'fields': ('annual_income_range', 'bank_name', 'account_name', 'account_number'),
            'classes': ('collapse',)
        }),
        ('PTA Information', {
            'fields': ('is_pta_member', 'pta_position', 'pta_committee'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
    )

    # ===============================
    # CUSTOM METHODS
    # ===============================
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Parent Name'
    get_full_name.admin_order_field = 'user__first_name'

    def get_parent_type(self, obj):
        return obj.get_parent_type_display()
    get_parent_type.short_description = 'Parent Type'

    def children_count(self, obj):
        count = obj.get_children_count()
        color = 'green' if count > 0 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color,
            count
        )
    children_count.short_description = 'Children'

    # ===============================
    # ACTIONS
    # ===============================
    actions = ['verify_parents', 'activate_parents', 'deactivate_parents']

    def verify_parents(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} parent(s) verified.')
    verify_parents.short_description = "Verify selected parents"

    def activate_parents(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} parent(s) activated.')
    activate_parents.short_description = "Activate selected parents"

    def deactivate_parents(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} parent(s) deactivated.')
    deactivate_parents.short_description = "Deactivate selected parents"
