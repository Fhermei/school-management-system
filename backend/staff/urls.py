from django.urls import path
from .views import (
    ParentListView, ParentCreateView, ParentDetailView, ParentUpdateView,
    ParentDashboardView, ParentChildrenView, LinkChildToParentView,
    UnlinkChildFromParentView, UpdatePTAStatusView, ParentFeeSummaryView,
    BulkParentCreateView, SendParentNotificationView, ParentStatisticsView,
    VerifyParentView, ParentSearchView
)

app_name = "parents"

urlpatterns = [
    # Parent Management
    path('', ParentListView.as_view(), name='parent-list'),
    path('create/', ParentCreateView.as_view(), name='parent-create'),
    path('bulk-create/', BulkParentCreateView.as_view(), name='parent-bulk-create'),
    path('search/', ParentSearchView.as_view(), name='parent-search'),

    # Individual Parent Operations
    path('<int:pk>/', ParentDetailView.as_view(), name='parent-detail'),
    path('<int:pk>/update/', ParentUpdateView.as_view(), name='parent-update'),
    path('<int:pk>/dashboard/', ParentDashboardView.as_view(), name='parent-dashboard'),
    path('<int:pk>/update-pta/', UpdatePTAStatusView.as_view(), name='parent-update-pta'),
    path('<int:pk>/fee-summary/', ParentFeeSummaryView.as_view(), name='parent-fee-summary'),
    path('<int:pk>/verify/', VerifyParentView.as_view(), name='parent-verify'),

    # Parent-Child Relationships
    path('children/', ParentChildrenView.as_view(), name='parent-children'),
    path('link-child/', LinkChildToParentView.as_view(), name='parent-link-child'),
    path('unlink-child/', UnlinkChildFromParentView.as_view(), name='parent-unlink-child'),

    # Communication
    path('send-notification/', SendParentNotificationView.as_view(), name='parent-send-notification'),

    # Statistics and Reports
    path('statistics/', ParentStatisticsView.as_view(), name='parent-statistics'),
]

# API Documentation descriptions
api_descriptions = {
    'parent-list': {
        'method': 'GET',
        'description': 'List all parents with filtering and search',
        'permissions': 'Admin/Principal/Teachers/Accountant/Secretary',
        'query_params': [
            'parent_type', 'marital_status', 'is_pta_member',
            'is_active', 'is_verified', 'search', 'ordering'
        ]
    },
    'parent-create': {
        'method': 'POST',
        'description': 'Create new parent profile',
        'permissions': 'Admin/Principal/Secretary/Teachers',
        'required_fields': ['user_id', 'parent_type']
    },
    'parent-dashboard': {
        'method': 'GET',
        'description': 'Get parent dashboard with children and fee summary',
        'permissions': 'Parents only'
    },
    'parent-children': {
        'method': 'GET',
        'description': 'Get all children of logged-in parent',
        'permissions': 'Parents only',
        'query_params': ['class_level', 'is_active', 'is_graduated']
    },
    'parent-link-child': {
        'method': 'POST',
        'description': 'Link existing student to parent',
        'permissions': 'Admin/Principal/Secretary/Teachers',
        'required_fields': ['student_admission_number', 'parent_id', 'relationship_type']
    },
    'parent-update-pta': {
        'method': 'POST',
        'description': 'Update parent\'s PTA membership status',
        'permissions': 'Admin/Principal only',
        'required_fields': ['is_pta_member']
    },
    'parent-fee-summary': {
        'method': 'GET',
        'description': 'Get fee summary for parent\'s children',
        'permissions': 'Parent can view own, admin/accountant can view any'
    },
    'parent-send-notification': {
        'method': 'POST',
        'description': 'Send notification to parent(s)',
        'permissions': 'Admin/Principal/Teachers/Secretary',
        'required_fields': ['message', 'notification_type']
    },
    'parent-statistics': {
        'method': 'GET',
        'description': 'Get parent statistics for dashboard',
        'permissions': 'Admin/Principal/Accountant'
    },
    'parent-verify': {
        'method': 'POST',
        'description': 'Verify a parent (Admin only)',
        'permissions': 'Admin/Principal only'
    }
}