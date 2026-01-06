from rest_framework import serializers
from .models import Parent
from users.serializers import UserProfileSerializer


# 🔹 MINI STUDENT SERIALIZER (NO IMPORT CIRCLE)
class StudentMiniSerializer(serializers.Serializer):
    """Mini student serializer to avoid circular imports"""
    id = serializers.IntegerField()
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    admission_number = serializers.CharField(read_only=True)
    class_level = serializers.CharField(read_only=True)
    fee_status = serializers.CharField(read_only=True)


# 🔹 PARENT SERIALIZER
class ParentSerializer(serializers.ModelSerializer):
    """Main parent serializer"""
    user = UserProfileSerializer(read_only=True)
    children = serializers.SerializerMethodField(read_only=True)
    
    parent_id = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = Parent
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'parent_id', 'is_verified',
            'created_at', 'updated_at'
        ]

    def get_children(self, obj):
        """Get children without circular import"""
        from students.serializers import StudentListSerializer
        return StudentListSerializer(obj.get_children(), many=True).data


# 🔹 PARENT CREATE SERIALIZER
class ParentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating parent profiles"""
    user_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Parent
        fields = [
            'user_id',
            'parent_type',
            'occupation',
            'employer',
            'marital_status',
            'preferred_communication'
        ]

    def validate_user_id(self, value):
        """Validate user exists and is not already a parent"""
        from users.models import User
        
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        
        if hasattr(user, 'parent_profile'):
            raise serializers.ValidationError("User is already a parent")
        
        return value

    def create(self, validated_data):
        """Create parent profile for user"""
        from users.models import User
        
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        
        # Update user role to parent
        user.role = 'parent'
        user.save()
        
        # Create parent profile
        parent = Parent.objects.create(user=user, **validated_data)
        return parent


# 🔹 PARENT LIST SERIALIZER
class ParentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for parent lists"""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)
    children_count = serializers.IntegerField(source='get_children_count', read_only=True)

    class Meta:
        model = Parent
        fields = [
            'id', 'full_name', 'email', 'phone', 'parent_id',
            'parent_type', 'occupation', 'marital_status',
            'children_count', 'is_pta_member', 'is_active',
            'created_at'
        ]


# 🔹 PARENT DASHBOARD SERIALIZER
class ParentDashboardSerializer(serializers.Serializer):
    """Serializer for parent dashboard data"""
    parent = ParentSerializer(read_only=True)
    children_count = serializers.IntegerField(read_only=True)
    fee_summary = serializers.DictField(read_only=True)
    
    def to_representation(self, instance):
        """Custom representation for dashboard"""
        from students.serializers import StudentListSerializer
        
        return {
            'parent': ParentSerializer(instance).data,
            'children_count': instance.get_children_count(),
            'fee_summary': instance.get_fee_summary(),
            'children': StudentListSerializer(instance.get_children(), many=True).data
        }