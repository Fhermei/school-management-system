from django.urls import path
from .views import (
    StudentListView,
    StudentCreateView,
    StudentDetailView,
    StudentUpdateView,
    StudentFeePaymentView,
    StudentFeeSummaryView,
    StudentBulkCreateView,
)

urlpatterns = [
    # -------------------------
    # Students Core Endpoints
    # -------------------------

    # GET  → List students (with filters, search, ordering)
    path('', StudentListView.as_view(), name='student-list'),

    # POST → Create a single student
    path('create/', StudentCreateView.as_view(), name='student-create'),

    # POST → Bulk create students
    path('bulk-create/', StudentBulkCreateView.as_view(), name='student-bulk-create'),

    # -------------------------
    # Student Profile
    # -------------------------

    # GET → Retrieve student details
    path('<int:pk>/', StudentDetailView.as_view(), name='student-detail'),

    # PATCH / PUT → Update student profile
    path('<int:pk>/update/', StudentUpdateView.as_view(), name='student-update'),

    # -------------------------
    # Fees Management
    # -------------------------

    # POST → Record fee payment
    path('<int:pk>/pay-fee/', StudentFeePaymentView.as_view(), name='student-pay-fee'),

    # GET → Fee summary
    path('<int:pk>/fee-summary/', StudentFeeSummaryView.as_view(), name='student-fee-summary'),
]
