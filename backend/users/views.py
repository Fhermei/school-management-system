from rest_framework import generics, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Q
import logging

from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer,
    AdminResetPasswordSerializer, UserListSerializer, TokenSerializer
)

# Set up logger
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    Register a new user (Student, Teacher, Parent, etc.)

    POST /api/auth/register/
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def get_client_ip(self, request):
        """
        Safely get client IP address
        Works locally and behind proxies
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def create(self, request, *args, **kwargs):
        """Create new user and log the action"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Log registration
        logger.info(
            f"New user registered: {user.registration_number} "
            f"({user.role}) from IP: {self.get_client_ip(request)}"
        )

        # Generate tokens for auto-login
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            },
            status=status.HTTP_201_CREATED
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that accepts registration_number only

    POST /api/auth/login/

    Required: registration_number, password

    Returns: JWT tokens and user profile
    """

    serializer_class = LoginSerializer

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def post(self, request, *args, **kwargs):
        """Handle login and update user stats"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Update login stats
        user.last_login = timezone.now()
        user.last_login_ip = self.get_client_ip(request)
        user.login_count += 1
        user.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        logger.info(f"User logged in: {user.registration_number} from IP: {user.last_login_ip}")

        return Response({
            'message': 'Login successful',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })


class LogoutView(APIView):
    """
    Logout user by blacklisting refresh token

    POST /api/auth/logout/

    Required: refresh_token in body

    Note: Requires authentication
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Blacklist refresh token"""
        try:
            refresh_token = request.data.get("refresh_token")
            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"User logged out: {request.user.registration_number}")

            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile

    GET /api/auth/profile/ - Get user profile
    PUT /api/auth/profile/ - Update user profile
    PATCH /api/auth/profile/ - Partial update

    Note: Users can only view/update their own profile
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get current user"""
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """
    Change user password

    PUT /api/auth/change-password/

    Required: old_password, new_password, confirm_password

    Note: Users can only change their own password
          if they have permission (admin/principal)
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get current user"""
        return self.request.user

    def update(self, request, *args, **kwargs):
        """Change password with validation"""
        user = self.get_object()

        # Check if user can change password
        if not user.can_change_password():
            return Response({
                'error': 'You do not have permission to change password. Contact administrator.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        logger.info(f"Password changed for user: {user.registration_number}")

        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    Request password reset (sends email to admin)

    POST /api/auth/forgot-password/

    Required: email

    Note: This notifies admin, doesn't automatically reset password
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle forgot password request"""
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'No user found with this email address'
            }, status=status.HTTP_404_NOT_FOUND)

        # Log the request (in production, send email to admin)
        logger.warning(f"Password reset requested for: {user.registration_number} ({user.email})")

        # In production, you would:
        # 1. Send email to admin
        # 2. Generate reset token
        # 3. Store request in database

        return Response({
            'message': 'Password reset request sent to administrator.',
            'note': 'Contact your school administrator to reset your password.'
        }, status=status.HTTP_200_OK)


class AdminResetPasswordView(APIView):
    """
    Admin reset user password

    POST /api/auth/admin/reset-password/

    Required: registration_number, new_password

    Note: Only admin/principal can access this
    """

    permission_classes = [permissions.IsAdminUser]  # Only admin users

    def post(self, request):
        """Reset user password as admin"""
        serializer = AdminResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        registration_number = serializer.validated_data['registration_number']
        new_password = serializer.validated_data['new_password']

        # Get user
        try:
            user = User.objects.get(registration_number=registration_number)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Reset password
        user.set_password(new_password)
        user.save()

        logger.info(f"Admin {request.user.registration_number} reset password for: {user.registration_number}")

        return Response({
            'message': f'Password reset successfully for {user.get_full_name()}',
            'user': {
                'registration_number': user.registration_number,
                'email': user.email,
                'role': user.get_role_display()
            }
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    List all users (Admin only)

    GET /api/auth/users/

    Query parameters:
    - role: Filter by role
    - search: Search by name, email, or registration number
    - is_active: Filter by active status

    Note: Only admin/principal can access
    """

    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        """Filter users based on query parameters"""
        queryset = User.objects.all()

        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)

        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=(is_active.lower() == 'true'))

        # Filter by verification status
        is_verified = self.request.query_params.get('is_verified', None)
        if is_verified is not None:
            queryset = queryset.filter(is_verified=(is_verified.lower() == 'true'))

        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(registration_number__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone_number__icontains=search)
            )

        return queryset.order_by('-created_at')


class UserDetailView(generics.RetrieveAPIView):
    """
    Get user details by registration number

    GET /api/auth/users/{registration_number}/

    Note: Admin only or self
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'registration_number'
    lookup_url_kwarg = 'registration_number'

    def get_queryset(self):
        """Filter users based on permissions"""
        user = self.request.user

        # Admin can see all users
        if user.role in ['head', 'principal', 'vice_principal'] or user.is_staff:
            return User.objects.all()

        # Users can only see themselves
        return User.objects.filter(pk=user.pk)


class VerifyUserView(APIView):
    """
    Verify a user (Admin only)

    POST /api/auth/verify/{registration_number}/

    Note: Only admin/principal can verify users
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, registration_number):
        """Verify a user"""
        try:
            user = User.objects.get(registration_number=registration_number)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        user.is_verified = True
        user.save()

        logger.info(f"User verified by admin: {user.registration_number}")

        return Response({
            'message': f'User {user.get_full_name()} verified successfully',
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)


class DeactivateUserView(APIView):
    """
    Deactivate a user (Admin only)

    POST /api/auth/deactivate/{registration_number}/

    Note: Only admin/principal can deactivate users
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, registration_number):
        """Deactivate a user"""
        try:
            user = User.objects.get(registration_number=registration_number)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Cannot deactivate self
        if user == request.user:
            return Response({
                'error': 'You cannot deactivate your own account'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = False
        user.save()

        logger.info(f"User deactivated by admin: {user.registration_number}")

        return Response({
            'message': f'User {user.get_full_name()} deactivated successfully',
            'user': UserProfileSerializer(user).data
        })


class ActivateUserView(APIView):
    """
    Activate a user (Admin only)

    POST /api/auth/activate/{registration_number}/

    Note: Only admin/principal can activate users
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, registration_number):
        """Activate a user"""
        try:
            user = User.objects.get(registration_number=registration_number)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        user.is_active = True
        user.save()

        logger.info(f"User activated by admin: {user.registration_number}")

        return Response({
            'message': f'User {user.get_full_name()} activated successfully',
            'user': UserProfileSerializer(user).data
        })


class UpdateUserRoleView(APIView):
    """
    Update user role (Admin only)

    POST /api/auth/update-role/{registration_number}/

    Required: role (new role)

    Note: Only admin/principal can update roles
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, registration_number):
        """Update user role"""
        try:
            user = User.objects.get(registration_number=registration_number)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        new_role = request.data.get('role')

        if not new_role:
            return Response({
                'error': 'Role is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate role
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if new_role not in valid_roles:
            return Response({
                'error': f'Invalid role. Valid roles are: {", ".join(valid_roles)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cannot change own role if it would remove admin privileges
        if user == request.user and new_role not in ['head', 'principal', 'vice_principal']:
            return Response({
                'error': 'You cannot remove your own administrative privileges'
            }, status=status.HTTP_400_BAD_REQUEST)

        old_role = user.role
        user.role = new_role
        user.save()

        logger.info(f"User role updated from {old_role} to {new_role} by {request.user.registration_number}")

        return Response({
            'message': f'User role updated from {old_role} to {new_role}',
            'user': UserProfileSerializer(user).data
        })