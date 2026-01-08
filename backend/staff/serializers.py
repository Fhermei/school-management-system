from rest_framework import serializers
from django.utils import timezone
from .models import Parent
from users.serializers import UserProfileSerializer
from students.serializers import StudentListSerializer


class ParentSerializer(serializers.ModelSerializer):
    """Main serializer for Parent model"""

    user = UserProfileSerializer(read_only=True)
    spouse_info = serializers.SerializerMethodField(read_only=True)
    children_count = serializers.SerializerMethodField(read_only=True)
    fee_summary = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Parent
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'parent_id', 'is_verified',
            'created_at', 'updated_at', 'children_count',
            'fee_summary', 'spouse_info'
        ]

    def get_spouse_info(self, obj):
        """Get spouse information"""
        if obj.spouse:
            return {
                'id': obj.spouse.id,
                'name': obj.spouse.user.get_full_name(),
                'parent_id': obj.spouse.parent_id,
                'parent_type': obj.spouse.parent_type
            }
        return None

    def get_children_count(self, obj):
        """Get number of children"""
        return obj.get_children_count()

    def get_fee_summary(self, obj):
        """Get fee summary for all children"""
        return obj.get_fee_summary()


class ParentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating parent profiles"""

    user_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Parent
        fields = [
            'user_id', 'parent_type', 'occupation', 'employer',
            'employer_address', 'office_phone', 'marital_status',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'preferred_communication',
            'receive_sms_alerts', 'receive_email_alerts',
            'annual_income_range', 'bank_name', 'account_name',
            'account_number', 'is_pta_member', 'pta_position',
            'pta_committee', 'spouse'
        ]

    def validate_user_id(self, value):
        """Validate user exists and is not already a parent"""
        from users.models import User

        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

        # Check if user is already a parent
        if hasattr(user, 'parent_profile'):
            raise serializers.ValidationError("User is already a parent")

        # Check if user role is appropriate
        if user.role in ['head', 'principal', 'vice_principal', 'teacher']:
            raise serializers.ValidationError("Staff cannot be converted to parent")

        return value

    def validate_spouse(self, value):
        """Validate spouse is a parent"""
        if value and not isinstance(value, Parent):
            raise serializers.ValidationError("Spouse must be a parent")
        return value

    def validate(self, data):
        """Validate parent data"""
        # Validate bank details if provided
        bank_fields = ['bank_name', 'account_name', 'account_number']
        bank_provided = any(data.get(field) for field in bank_fields)

        if bank_provided:
            for field in bank_fields:
                if not data.get(field):
                    raise serializers.ValidationError(
                        f"All bank details must be provided if any is provided. Missing: {field}"
                    )

        # Validate marital status and spouse consistency
        marital_status = data.get('marital_status')
        spouse = data.get('spouse')

        if marital_status == 'married' and not spouse:
            raise serializers.ValidationError({
                'spouse': 'Spouse is required for married parents'
            })

        if marital_status != 'married' and spouse:
            raise serializers.ValidationError({
                'spouse': 'Spouse can only be specified for married parents'
            })

        return data

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

        # Update spouse's spouse field if married
        if parent.marital_status == 'married' and parent.spouse:
            parent.spouse.spouse = parent
            parent.spouse.save()

        return parent


class ParentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for parent lists"""

    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)
    parent_type_display = serializers.CharField(source='get_parent_type_display', read_only=True)
    marital_status_display = serializers.CharField(source='get_marital_status_display', read_only=True)
    children_count = serializers.IntegerField(source='get_children_count', read_only=True)

    class Meta:
        model = Parent
        fields = [
            'id', 'full_name', 'email', 'phone', 'parent_id',
            'parent_type', 'parent_type_display', 'occupation',
            'marital_status', 'marital_status_display', 'children_count',
            'is_pta_member', 'is_active', 'is_verified',
            'preferred_communication', 'created_at'
        ]


class ParentDetailSerializer(ParentSerializer):
    """Detailed serializer for parent view"""

    children = serializers.SerializerMethodField(read_only=True)

    class Meta(ParentSerializer.Meta):
        fields = ParentSerializer.Meta.fields + ['children']

    def get_children(self, obj):
        """Get all children of this parent"""
        children = obj.get_children()
        return StudentListSerializer(children, many=True).data


class ParentDashboardSerializer(serializers.Serializer):
    """Serializer for parent dashboard data"""

    parent = ParentSerializer(read_only=True)
    children = serializers.SerializerMethodField(read_only=True)
    fee_summary = serializers.DictField(read_only=True)
    pta_info = serializers.SerializerMethodField(read_only=True)

    def get_children(self, obj):
        """Get children with academic details"""
        children = obj.get_children().select_related(
            'user', 'class_level'
        )
        return StudentListSerializer(children, many=True).data

    def get_pta_info(self, obj):
        """Get PTA information"""
        if obj.is_pta_member:
            return {
                'is_member': True,
                'position': obj.pta_position,
                'committee': obj.pta_committee
            }
        return {'is_member': False}


class ParentChildrenSerializer(StudentListSerializer):
    """Serializer for parent's children view"""

    class Meta(StudentListSerializer.Meta):
        pass


class LinkChildToParentSerializer(serializers.Serializer):
    """Serializer for linking child to parent"""

    student_admission_number = serializers.CharField(required=True, max_length=20)
    parent_id = serializers.CharField(required=True, max_length=20)
    relationship_type = serializers.ChoiceField(
        choices=[('father', 'Father'), ('mother', 'Mother')],
        required=True
    )

    def validate_student_admission_number(self, value):
        """Validate student exists"""
        from students.models import Student
        try:
            student = Student.objects.get(admission_number=value)
        except Student.DoesNotExist:
            raise serializers.ValidationError("Student not found")
        return value

    def validate_parent_id(self, value):
        """Validate parent exists"""
        try:
            parent = Parent.objects.get(parent_id=value)
        except Parent.DoesNotExist:
            raise serializers.ValidationError("Parent not found")
        return value

    def validate(self, data):
        """Validate linking data"""
        from students.models import Student

        student = Student.objects.get(admission_number=data['student_admission_number'])
        parent = Parent.objects.get(parent_id=data['parent_id'])
        relationship = data['relationship_type']

        # Check if parent is appropriate gender for relationship
        if relationship == 'father' and parent.parent_type not in ['father', 'guardian', 'other']:
            raise serializers.ValidationError({
                'parent_id': 'Parent must be male or guardian for father relationship'
            })

        if relationship == 'mother' and parent.parent_type not in ['mother', 'guardian', 'other']:
            raise serializers.ValidationError({
                'parent_id': 'Parent must be female or guardian for mother relationship'
            })

        data['student'] = student
        data['parent'] = parent

        return data


class UpdateParentSerializer(serializers.ModelSerializer):
    """Serializer for updating parent profiles"""

    class Meta:
        model = Parent
        fields = [
            'occupation', 'employer', 'employer_address', 'office_phone',
            'marital_status', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'preferred_communication',
            'receive_sms_alerts', 'receive_email_alerts', 'annual_income_range',
            'bank_name', 'account_name', 'account_number', 'next_of_kin_name',
            'next_of_kin_relationship', 'next_of_kin_phone', 'next_of_kin_address',
            'is_pta_member', 'pta_position', 'pta_committee', 'spouse'
        ]

    def validate(self, data):
        """Validate update data"""
        # Parents cannot change PTA status themselves
        if 'is_pta_member' in data and self.context['request'].user.role == 'parent':
            raise serializers.ValidationError({
                'is_pta_member': 'You cannot change your PTA membership status'
            })

        return data


class ParentPTASerializer(serializers.Serializer):
    """Serializer for updating PTA status"""

    is_pta_member = serializers.BooleanField(required=True)
    pta_position = serializers.CharField(required=False, max_length=100, allow_blank=True)
    pta_committee = serializers.CharField(required=False, max_length=100, allow_blank=True)

    def validate(self, data):
        """Validate PTA data"""
        if data.get('is_pta_member'):
            # If becoming PTA member, position should be provided
            if not data.get('pta_position'):
                raise serializers.ValidationError({
                    'pta_position': 'PTA position is required when becoming a member'
                })
        return data


class BulkParentCreateSerializer(serializers.Serializer):
    """Serializer for bulk parent creation"""

    parents = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="List of parent objects to create"
    )

    def validate_parents(self, value):
        """Validate parent list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Parents must be a list")

        if len(value) == 0:
            raise serializers.ValidationError("Parent list cannot be empty")

        if len(value) > 100:
            raise serializers.ValidationError("Cannot create more than 100 parents at once")

        # Validate each parent object
        for i, parent in enumerate(value):
            if not isinstance(parent, dict):
                raise serializers.ValidationError(f"Parent at index {i} must be a dictionary")

            # Check required fields
            required_fields = ['user', 'parent_type']
            for field in required_fields:
                if field not in parent:
                    raise serializers.ValidationError(
                        f"Parent at index {i} missing required field: {field}"
                    )

            # Validate user data
            user_data = parent.get('user', {})
            user_required = ['first_name', 'last_name', 'email', 'phone_number']
            for field in user_required:
                if field not in user_data:
                    raise serializers.ValidationError(
                        f"Parent at index {i} user data missing required field: {field}"
                    )

        return value


class ParentFeeSummarySerializer(serializers.Serializer):
    """Serializer for parent fee summary"""

    total_children = serializers.IntegerField(read_only=True)
    total_fee = serializers.FloatField(read_only=True)
    total_paid = serializers.FloatField(read_only=True)
    total_balance = serializers.FloatField(read_only=True)
    percentage_paid = serializers.FloatField(read_only=True)

    def to_representation(self, instance):
        """Convert to representation"""
        fee_summary = instance.get_fee_summary()
        return {
            'total_children': fee_summary['total_children'],
            'total_fee': fee_summary['total_fee'],
            'total_paid': fee_summary['total_paid'],
            'total_balance': fee_summary['total_balance'],
            'percentage_paid': fee_summary['percentage_paid']
        }


class ParentNotificationSerializer(serializers.Serializer):
    """Serializer for parent notifications"""

    message = serializers.CharField(required=True, max_length=1000)
    notification_type = serializers.ChoiceField(
        choices=[
            ('academic', 'Academic Update'),
            ('financial', 'Financial Update'),
            ('attendance', 'Attendance Update'),
            ('event', 'School Event'),
            ('pta', 'PTA Meeting'),
            ('general', 'General Announcement'),
            ('emergency', 'Emergency Alert')
        ],
        required=True
    )
    parent_ids = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        help_text="List of parent IDs to notify (empty for all parents)"
    )
    student_ids = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        help_text="List of student admission numbers (notify their parents)"
    )

    def validate(self, data):
        """Validate notification data"""
        parent_ids = data.get('parent_ids', [])
        student_ids = data.get('student_ids', [])

        if not parent_ids and not student_ids:
            # Send to all parents
            pass

        return data


class ParentSearchSerializer(serializers.Serializer):
    """Serializer for parent search parameters"""

    name = serializers.CharField(required=False, max_length=100)
    parent_id = serializers.CharField(required=False, max_length=20)
    occupation = serializers.CharField(required=False, max_length=100)
    parent_type = serializers.CharField(required=False, max_length=20)
    marital_status = serializers.CharField(required=False, max_length=20)
    is_pta_member = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    is_verified = serializers.BooleanField(required=False)

    def validate(self, data):
        """Validate search parameters"""
        # Ensure at least one search parameter is provided
        if not any(data.values()):
            raise serializers.ValidationError("At least one search parameter is required")
        return data