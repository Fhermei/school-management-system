from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration - Uses registration_number instead of username"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="Password must contain at least 8 characters"
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Enter the same password as above"
    )
    
    class Meta:
        model = User
        fields = (
            'registration_number', 'email', 'password', 'password2',
            'first_name', 'last_name', 'role', 'gender',
            'phone_number', 'date_of_birth'
        )
        extra_kwargs = {
            'registration_number': {'required': False},  # Will be auto-generated
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate registration data"""
        # Check passwords match
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # REMOVED USERNAME VALIDATION
        
        # Validate phone number (Nigerian format)
        phone = attrs.get('phone_number', '')
        if phone and not (phone.startswith('0') or phone.startswith('+234')):
            raise serializers.ValidationError(
                {"phone_number": "Phone number must start with 0 or +234"}
            )
        
        # Check email doesn't already exist
        email = attrs.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password - registration_number will be auto-generated"""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
    
class LoginSerializer(serializers.Serializer):
    """Serializer for user login - Uses registration_number only"""
    
    registration_number = serializers.CharField(
        required=True,
        help_text="Enter your registration number (e.g., femi1234)"
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Enter your password"
    )
    
    def validate(self, attrs):
        """Validate login credentials"""
        registration_number = attrs.get('registration_number')
        password = attrs.get('password')
        
        # Check if user exists with registration number
        try:
            user = User.objects.get(registration_number=registration_number)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"registration_number": "Invalid registration number"}
            )
        
        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError(
                {"registration_number": "Account is deactivated. Contact administrator."}
            )
        
        # Check password
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid password"})
        
        attrs['user'] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile - BASIC FIELDS ONLY"""
    
    class Meta:
        model = User
        fields = (
            'registration_number', 'email', 
            'first_name', 'last_name', 'role', 'gender',
            'date_of_birth', 'phone_number', 'alternative_phone',
            'address', 'city', 'state_of_origin', 'lga', 'nationality',
            'profile_picture', 'is_verified', 'created_at'
        )
        read_only_fields = ('registration_number', 'email', 'role', 'created_at')
        
class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Enter your current password"
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="Enter new password (min 8 characters)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirm new password"
    )
    
    def validate(self, attrs):
        """Validate password change"""
        # Check new passwords match
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"new_password": "New passwords don't match"}
            )
        
        # Check old and new password are different
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {"new_password": "New password cannot be same as old password"}
            )
        
        return attrs

class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request"""
    
    email = serializers.EmailField(
        required=True,
        help_text="Enter your registered email address"
    )
    
    def validate_email(self, value):
        """Validate email exists"""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No account found with this email address"
            )
        return value

class AdminResetPasswordSerializer(serializers.Serializer):
    """Serializer for admin to reset user password"""
    
    registration_number = serializers.CharField(
        required=True,
        help_text="Enter user's registration number"
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="Enter new password for user (min 8 characters)"
    )
    
    def validate_registration_number(self, value):
        """Validate registration number exists"""
        try:
            user = User.objects.get(registration_number=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No user found with this registration number"
            )
        return value

class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (admin only)"""
    
    class Meta:
        model = User
        fields = (
            'id', 'registration_number', 'email',
            'first_name', 'last_name', 'role', 'is_active',
            'is_verified', 'last_login', 'created_at'
        )
        
class TokenSerializer(serializers.Serializer):
    """Serializer for JWT tokens"""
    
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserProfileSerializer()