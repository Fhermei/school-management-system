from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for viewset
router = DefaultRouter()
router.register(r'timetables', views.TimetableViewSet, basename='timetable')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # ============================================
    # Academic Structure
    # ============================================

    # Academic Sessions
    path('sessions/', views.AcademicSessionListView.as_view(), name='academic-session-list'),
    path('sessions/<int:pk>/', views.AcademicSessionDetailView.as_view(), name='academic-session-detail'),

    # Academic Terms
    path('terms/', views.AcademicTermListView.as_view(), name='academic-term-list'),
    path('terms/<int:pk>/', views.AcademicTermDetailView.as_view(), name='academic-term-detail'),

    # Programs
    path('programs/', views.ProgramListView.as_view(), name='program-list'),
    path('programs/<int:pk>/', views.ProgramDetailView.as_view(), name='program-detail'),

    # Class Levels
    path('class-levels/', views.ClassLevelListView.as_view(), name='class-level-list'),
    path('class-levels/<int:pk>/', views.ClassLevelDetailView.as_view(), name='class-level-detail'),

    # Subjects
    path('subjects/', views.SubjectListView.as_view(), name='subject-list'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject-detail'),

    # ============================================
    # Class Management
    # ============================================

    # Classes
    path('classes/', views.ClassListView.as_view(), name='class-list'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='class-detail'),
    path('classes/<int:pk>/dashboard/', views.ClassDashboardView.as_view(), name='class-dashboard'),

    # Class-Subject Assignments
    path('class-subjects/', views.ClassSubjectListView.as_view(), name='class-subject-list'),
    path('class-subjects/<int:pk>/', views.ClassSubjectDetailView.as_view(), name='class-subject-detail'),
    path('class-subjects/bulk-assign/', views.BulkClassSubjectAssignmentView.as_view(),
         name='class-subject-bulk-assign'),

    # ============================================
    # Timetable Management
    # ============================================

    # Timetable Entries
    path('timetable-entries/', views.TimetableEntryListView.as_view(), name='timetable-entry-list'),
    path('timetable-entries/<int:pk>/', views.TimetableEntryDetailView.as_view(), name='timetable-entry-detail'),

    # ============================================
    # Student Enrollment
    # ============================================

    path('enrollments/', views.StudentEnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/<int:pk>/', views.StudentEnrollmentDetailView.as_view(), name='enrollment-detail'),
    path('enrollments/<int:pk>/approve/', views.ApproveEnrollmentView.as_view(), name='enrollment-approve'),

    # ============================================
    # Teacher Management
    # ============================================

    path('teachers/timetable/', views.TeacherTimetableView.as_view(), name='teacher-timetable-current'),
    path('teachers/<int:pk>/timetable/', views.TeacherTimetableView.as_view(), name='teacher-timetable'),
    path('teachers/<int:pk>/assignments/', views.TeacherAssignmentsView.as_view(), name='teacher-assignments'),

    # ============================================
    # Dashboard and Reporting
    # ============================================

    path('dashboard/', views.AcademicDashboardView.as_view(), name='academic-dashboard'),
    path('statistics/classes/', views.ClassStatisticsView.as_view(), name='class-statistics'),

    # ============================================
    # Public Views (for students and parents)
    # ============================================

    path('public/classes/<int:pk>/timetable/', views.PublicClassTimetableView.as_view(), name='public-class-timetable'),
    path('public/teachers/<int:pk>/timetable/', views.PublicTeacherTimetableView.as_view(),
         name='public-teacher-timetable'),
]

# API Documentation descriptions
api_descriptions = {
    'academic-session-list': {
        'method': 'GET/POST',
        'description': 'List or create academic sessions',
        'permissions': 'Academic administrators only',
    },
    'class-list': {
        'method': 'GET/POST',
        'description': 'List or create classes',
        'permissions': 'Head, Principal, Vice Principal, Secretary',
    },
    'class-dashboard': {
        'method': 'GET',
        'description': 'Get comprehensive class dashboard with subjects, students, and timetable',
        'permissions': 'Users with view access to the class',
    },
    'class-subject-list': {
        'method': 'GET/POST',
        'description': 'List or create class-subject assignments',
        'permissions': 'Head, Principal, Vice Principal',
    },
    'timetable-list': {
        'method': 'GET',
        'description': 'List timetables based on user role and permissions',
        'permissions': 'Authenticated users (filtered by role)',
    },
    'teacher-timetable': {
        'method': 'GET',
        'description': 'Get teacher\'s timetable and teaching information',
        'permissions': 'Teacher can view own, admin can view any',
    },
    'enrollment-approve': {
        'method': 'POST',
        'description': 'Approve student enrollment',
        'permissions': 'Academic administrators or class teachers',
    },
    'public-class-timetable': {
        'method': 'GET',
        'description': 'Get class timetable for public viewing',
        'permissions': 'Authenticated users',
    },
}