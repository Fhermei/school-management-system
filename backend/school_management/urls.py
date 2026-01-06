from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="School Management System API",
      default_version='v1',
      description="""
      # School Management System API Documentation
      
      This API powers a complete school management system for Nigerian schools.
      
      ## Authentication
      - Register: `/api/auth/register/`
      - Login: `/api/auth/login/`
      - Refresh Token: `/api/auth/token/refresh/`
      
      ## User Roles
      - Head of School/Proprietor
      - Principal
      - Vice Principal
      - Teacher/Form Teacher
      - Student
      - Parent/Guardian
      - Accountant/Bursar
      - Secretary
      - Other Staff
      
      ## Security Features
      - JWT Token Authentication
      - Role-based permissions
      - Login tracking
      - Admin-only password reset
      
      ## Test Credentials
      - Admin: admin / Admin123!
      - Teacher: teacher01 / Password123
      - Student: student01 / Password123
      """,
      terms_of_service="https://www.school.edu/terms/",
      contact=openapi.Contact(email="support@school.edu"),
      license=openapi.License(name="School License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
    
    # API Endpoints
    path('api/auth/', include('users.urls')),  # Authentication URLs
    path('api/students/', include('students.urls')),
    path('api/parents/', include('parents.urls')),
    
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    