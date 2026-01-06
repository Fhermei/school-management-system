# parents/urls.py
from django.urls import path
from .views import (
    ParentListView,
    ParentCreateView,
    ParentDetailView,
    ParentUpdateView,
    ParentDashboardView,
    ParentChildrenView,
    LinkChildToParentView
)

app_name = "parents"

urlpatterns = [
    path('', ParentListView.as_view(), name='parent-list'),
    path('create/', ParentCreateView.as_view(), name='parent-create'),
    path('<int:pk>/', ParentDetailView.as_view(), name='parent-detail'),
    path('<int:pk>/update/', ParentUpdateView.as_view(), name='parent-update'),
    path('dashboard/', ParentDashboardView.as_view(), name='parent-dashboard'),
    path('children/', ParentChildrenView.as_view(), name='parent-children'),
    path('link-child/', LinkChildToParentView.as_view(), name='parent-link-child'),
]


api_descriptions = {
    'parent-dashboard': {
        'method': 'GET',
        'description': 'Parent dashboard with children and fee summary',
        'permissions': 'Parents only'
    },
    'parent-children': {
        'method': 'GET',
        'description': 'Get all children of logged-in parent',
        'permissions': 'Parents only'
    },
    'link-child-to-parent': {
        'method': 'POST',
        'description': 'Link existing student to parent',
        'permissions': 'Admin/Principal only',
        'required_fields': ['student_admission_number', 'parent_id', 'relationship_type']
    }
}