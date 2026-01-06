from rest_framework import serializers
from django.core.validators import MinValueValidator
from django.utils import timezone

from .models import Student
from users.serializers import UserProfileSerializer


# 🔹 MINI PARENT SERIALIZER (NO IMPORT, NO CIRCLE)
class ParentMiniSerializer(serializers.Serializer):
    """Mini parent serializer to avoid circular imports"""
    id = serializers.IntegerField()
    full_name = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    parent_id = serializers.CharField(source='parent_id', read_only=True)
    
    def get_full_name(self, obj):
        """Get parent's full name"""
        return obj.user.get_full_name()
    
    def get_phone(self, obj):
        """Get parent's phone number"""
        return obj.user.phone_number


# 🔹 FULL STUDENT SERIALIZER
class StudentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    father = ParentMiniSerializer(read_only=True)
    mother = ParentMiniSerializer(read_only=True)

    admission_number = serializers.CharField(read_only=True)
    student_id = serializers.CharField(read_only=True)
    balance_due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'father', 'mother',
            'admission_number', 'student_id',
            'balance_due', 'average_score',
            'overall_grade', 'position_in_class',
            'days_present', 'days_absent', 'days_late',
            'created_at', 'updated_at'
        ]


# 🔹 STUDENT CREATE SERIALIZER (THIS FIXES YOUR ERROR)
class StudentCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Student
        fields = [
            'user_id',
            'class_level',
            'stream',
            'admission_date',
            'house',
            'student_category',
            'total_fee_amount',
            'blood_group',
            'genotype'
        ]

    def validate_user_id(self, value):
        from users.models import User

        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

        if hasattr(user, 'student_profile'):
            raise serializers.ValidationError("User is already a student")

        return value

    def create(self, validated_data):
        from users.models import User

        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)

        user.role = 'student'
        user.save()

        student = Student.objects.create(user=user, **validated_data)
        return student


# 🔹 STUDENT LIST SERIALIZER (SAFE FOR PARENTS)
class StudentListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'email', 'phone',
            'class_level', 'stream',
            'admission_number', 'fee_status',
            'total_fee_amount', 'amount_paid',
            'balance_due', 'is_active', 'created_at'
        ]


# 🔹 FEE PAYMENT SERIALIZER
class FeePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    payment_date = serializers.DateField(
        required=False,
        default=serializers.CreateOnlyDefault(timezone.now)
    )
    payment_method = serializers.CharField(required=False, default='cash')
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    evidence_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        student = self.context.get('student')

        if student and data['amount'] > student.balance_due:
            raise serializers.ValidationError(
                {"amount": "Payment exceeds outstanding balance"}
            )

        return data
