from django.urls import path
from .views import (
    StudentListView, StudentCreateView, StudentDetailView, StudentUpdateView,
    StudentDashboardView, UpdateStudentFeeView, PromoteStudentView,
    BulkStudentCreateView, StudentEnrollmentListView, StudentEnrollmentCreateView,
    StudentAttendanceUpdateView, StudentAcademicReportView, StudentSearchView,
    StudentStatisticsView
)

app_name = "students"

urlpatterns = [
    # Student Management
    path('', StudentListView.as_view(), name='student-list'),
    path('create/', StudentCreateView.as_view(), name='student-create'),
    path('bulk-create/', BulkStudentCreateView.as_view(), name='student-bulk-create'),
    path('search/', StudentSearchView.as_view(), name='student-search'),

    # Individual Student Operations
    path('<int:pk>/', StudentDetailView.as_view(), name='student-detail'),
    path('<int:pk>/update/', StudentUpdateView.as_view(), name='student-update'),
    path('<int:pk>/dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('<int:pk>/update-fee/', UpdateStudentFeeView.as_view(), name='student-update-fee'),
    path('<int:pk>/promote/', PromoteStudentView.as_view(), name='student-promote'),
    path('<int:pk>/attendance/', StudentAttendanceUpdateView.as_view(), name='student-attendance'),
    path('<int:pk>/academic-report/', StudentAcademicReportView.as_view(), name='student-academic-report'),

    # Student Enrollment
    path('enrollments/', StudentEnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/create/', StudentEnrollmentCreateView.as_view(), name='enrollment-create'),

    # Statistics and Reports
    path('statistics/', StudentStatisticsView.as_view(), name='student-statistics'),
]

# API Documentation descriptions
api_descriptions = {
    'student-list': {
        'method': 'GET',
        'description': 'List all students with filtering and search',
        'permissions': 'Admin/Principal/Teachers/Accountant/Secretary',
        'query_params': [
            'class_level', 'stream', 'fee_status', 'student_category',
            'is_active', 'is_graduated', 'search', 'ordering'
        ]
    },
    'student-create': {
        'method': 'POST',
        'description': 'Create new student',
        'permissions': 'Admin/Principal/Secretary only',
        'required_fields': ['user_id', 'class_level_id', 'admission_date']
    },
    'student-dashboard': {
        'method': 'GET',
        'description': 'Get comprehensive student dashboard',
        'permissions': 'Student can view own, admin/teachers can view others'
    },
    'student-update-fee': {
        'method': 'POST',
        'description': 'Update student fee payment',
        'permissions': 'Accountant/Admin only',
        'required_fields': ['amount_paid']
    },
    'student-promote': {
        'method': 'POST',
        'description': 'Promote student to next class level',
        'permissions': 'Admin/Principal only',
        'required_fields': ['new_class_level_id']
    },
    'student-bulk-create': {
        'method': 'POST',
        'description': 'Create multiple students from bulk data (e.g., CSV)',
        'permissions': 'Admin/Principal/Secretary only'
    },
    'student-academic-report': {
        'method': 'GET',
        'description': 'Generate academic report for student',
        'permissions': 'Student/Teacher/Admin',
        'query_params': ['session_id', 'term_id']
    },
    'student-statistics': {
        'method': 'GET',
        'description': 'Get comprehensive student statistics',
        'permissions': 'Admin/Principal/Accountant'
    }
}