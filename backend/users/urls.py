from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, CustomTokenObtainPairView, LogoutView,
    UserProfileView, ChangePasswordView, ForgotPasswordView,
    AdminResetPasswordView, UserListView, VerifyUserView
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Profile management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Password recovery
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    
    # Admin endpoints (protected)
    path('admin/reset-password/', AdminResetPasswordView.as_view(), name='admin_reset_password'),
    path('admin/users/', UserListView.as_view(), name='user_list'),
    path('admin/verify/<str:registration_number>/', VerifyUserView.as_view(), name='verify_user'),
]

# API Documentation descriptions
api_descriptions = {
    'register': {
        'method': 'POST',
        'description': 'Register a new user (Student, Teacher, Parent, etc.)',
        'required_fields': ['username', 'email', 'password', 'password2', 
                           'first_name', 'last_name', 'phone_number', 'role'],
        'example': {
            'username': 'john_doe',
            'email': 'john@school.com',
            'password': 'Password123',
            'password2': 'Password123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'role': 'student',
            'gender': 'male',
            'date_of_birth': '2005-05-15'
        }
    },
    'login': {
        'method': 'POST',
        'description': 'Login with username OR registration number',
        'required_fields': ['username', 'password'],
        'example': {
            'username': 'john_doe',  # or registration number
            'password': 'Password123'
        }
    },
    'profile': {
        'method': 'GET/PUT/PATCH',
        'description': 'Get or update user profile',
        'authentication': 'Required (Bearer token)'
    },
    'change_password': {
        'method': 'PUT',
        'description': 'Change password (Admin/Principal only)',
        'required_fields': ['old_password', 'new_password', 'confirm_password'],
        'authentication': 'Required (Bearer token)'
    },
    'forgot_password': {
        'method': 'POST',
        'description': 'Request password reset (notifies admin)',
        'required_fields': ['email']
    },
    'admin_reset_password': {
        'method': 'POST',
        'description': 'Admin reset user password',
        'required_fields': ['registration_number', 'new_password'],
        'authentication': 'Required (Admin only)'
    }
}