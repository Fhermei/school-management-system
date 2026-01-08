from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .models import Student, StudentEnrollment
from users.serializers import UserProfileSerializer
from parents.serializers import ParentSerializer


class StudentSerializer(serializers.ModelSerializer):
    """Main serializer for Student model"""

    user = UserProfileSerializer(read_only=True)
    class_level_info = serializers.SerializerMethodField(read_only=True)
    father_info = ParentSerializer(source='father', read_only=True)
    mother_info = ParentSerializer(source='mother', read_only=True)
    fee_summary = serializers.SerializerMethodField(read_only=True)
    academic_level = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'admission_number', 'student_id', 'balance_due',
            'average_score', 'overall_grade', 'position_in_class',
            'days_present', 'days_absent', 'days_late', 'created_at', 'updated_at',
            'fee_summary', 'academic_level', 'class_level_info'
        ]

    def get_class_level_info(self, obj):
        if obj.class_level:
            return {
                'id': obj.class_level.id,
                'name': obj.class_level.name,
                'code': obj.class_level.code,
                'program': {
                    'id': obj.class_level.program.id,
                    'name': obj.class_level.program.name,
                }
            }
        return None

    def get_fee_summary(self, obj):
        return obj.get_fee_summary()

    def get_academic_level(self, obj):
        return obj.get_academic_level()


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating students"""

    user_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Student
        fields = [
            'user_id', 'class_level', 'stream', 'admission_date',
            'house', 'student_category', 'father', 'mother',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'total_fee_amount',
            'transportation_mode', 'bus_route', 'blood_group',
            'genotype', 'medical_conditions', 'allergies'
        ]

    def validate_user_id(self, value):
        """Validate user exists and is not already a student"""
        from users.models import User

        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

        # Check if user is already a student
        if hasattr(user, 'student_profile'):
            raise serializers.ValidationError("User is already a student")

        # Check if user role is appropriate
        if user.role != 'student':
            raise serializers.ValidationError("User must have 'student' role")

        return value

    def validate(self, data):
        """Validate student data"""
        # Validate father and mother are parent users
        father = data.get('father')
        mother = data.get('mother')

        if father and father.user.role != 'parent':
            raise serializers.ValidationError({
                'father': 'Father must be a parent user'
            })

        if mother and mother.user.role != 'parent':
            raise serializers.ValidationError({
                'mother': 'Mother must be a parent user'
            })

        # Validate total fee amount
        total_fee = data.get('total_fee_amount', 0)
        if total_fee < 0:
            raise serializers.ValidationError({
                'total_fee_amount': 'Total fee amount cannot be negative'
            })

        return data

    def create(self, validated_data):
        """Create student profile for user"""
        from users.models import User

        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)

        # Ensure user has student role
        if user.role != 'student':
            user.role = 'student'
            user.save()

        # Create student profile
        student = Student.objects.create(user=user, **validated_data)
        return student


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for student lists"""

    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    registration_number = serializers.CharField(source='user.registration_number', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)
    class_level_name = serializers.CharField(source='class_level.name', read_only=True)
    stream_display = serializers.CharField(source='get_stream_display', read_only=True)
    fee_status_display = serializers.CharField(source='get_fee_status_display', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'full_name', 'registration_number', 'email', 'phone',
            'admission_number', 'student_id', 'class_level', 'class_level_name',
            'stream', 'stream_display', 'house', 'student_category',
            'fee_status', 'fee_status_display', 'balance_due',
            'average_score', 'position_in_class', 'is_active', 'is_graduated',
            'admission_date', 'created_at'
        ]


class StudentDetailSerializer(StudentSerializer):
    """Detailed serializer for student view"""

    parents = serializers.SerializerMethodField()
    enrollments = serializers.SerializerMethodField()

    class Meta(StudentSerializer.Meta):
        model = Student
        fields = '__all__'

    def get_parents(self, obj):
        """Get both parents if available"""
        parents = []
        if obj.father:
            parents.append(ParentSerializer(obj.father).data)
        if obj.mother:
            parents.append(ParentSerializer(obj.mother).data)
        return parents

    def get_enrollments(self, obj):
        """Get student enrollments"""
        enrollments = obj.enrollments.all().order_by('-enrollment_date')
        return StudentEnrollmentSerializer(enrollments, many=True).data


class StudentDashboardSerializer(serializers.Serializer):
    """Serializer for student dashboard data"""

    student = StudentSerializer(read_only=True)
    academic_progress = serializers.SerializerMethodField(read_only=True)
    attendance_summary = serializers.SerializerMethodField(read_only=True)
    fee_information = serializers.SerializerMethodField(read_only=True)
    recent_activities = serializers.SerializerMethodField(read_only=True)

    def get_academic_progress(self, obj):
        """Get academic progress data"""
        return {
            'average_score': float(obj.average_score),
            'overall_grade': obj.overall_grade,
            'position_in_class': obj.position_in_class,
            'class_level': obj.class_level.name if obj.class_level else 'Not Assigned',
            'academic_level': obj.get_academic_level(),
            'stream': obj.get_stream_display() if obj.stream != 'none' else 'Not Applicable'
        }

    def get_attendance_summary(self, obj):
        """Get attendance summary"""
        total_days = obj.days_present + obj.days_absent
        attendance_rate = (obj.days_present / total_days * 100) if total_days > 0 else 0

        return {
            'days_present': obj.days_present,
            'days_absent': obj.days_absent,
            'days_late': obj.days_late,
            'total_days': total_days,
            'attendance_rate': round(attendance_rate, 2),
            'attendance_status': 'Good' if attendance_rate >= 80 else 'Needs Improvement'
        }

    def get_fee_information(self, obj):
        """Get fee information"""
        fee_summary = obj.get_fee_summary()

        return {
            **fee_summary,
            'last_payment_date': obj.last_payment_date,
            'payment_evidence_available': bool(obj.fee_payment_evidence)
        }

    def get_recent_activities(self, obj):
        """Get recent activities"""
        # This would fetch from activity logs in a real implementation
        return [
            {
                'date': timezone.now().date(),
                'activity': 'Fee payment updated',
                'details': f'Balance: ₦{obj.balance_due:,.2f}'
            },
            {
                'date': timezone.now().date() - timezone.timedelta(days=1),
                'activity': 'Attendance marked',
                'details': 'Present'
            }
        ]


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for StudentEnrollment model"""

    student_info = serializers.SerializerMethodField(read_only=True)
    class_info = serializers.SerializerMethodField(read_only=True)
    session_info = serializers.SerializerMethodField(read_only=True)
    term_info = serializers.SerializerMethodField(read_only=True)
    enrolled_by_info = serializers.SerializerMethodField(read_only=True)
    approved_by_info = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = '__all__'
        read_only_fields = [
            'id', 'enrollment_number', 'created_at', 'updated_at',
            'status_display', 'student_info', 'class_info', 'session_info',
            'term_info', 'enrolled_by_info', 'approved_by_info'
        ]

    def get_student_info(self, obj):
        return {
            'id': obj.student.id,
            'name': obj.student.get_full_name(),
            'registration_number': obj.student.registration_number,
        }

    def get_class_info(self, obj):
        if obj.class_obj:
            return {
                'id': obj.class_obj.id,
                'name': obj.class_obj.name,
                'code': obj.class_obj.code,
            }
        return None

    def get_session_info(self, obj):
        return {
            'id': obj.session.id,
            'name': obj.session.name,
            'start_date': obj.session.start_date,
            'end_date': obj.session.end_date,
        }

    def get_term_info(self, obj):
        return {
            'id': obj.term.id,
            'name': obj.term.name,
            'term': obj.term.term,
            'start_date': obj.term.start_date,
            'end_date': obj.term.end_date,
        }

    def get_enrolled_by_info(self, obj):
        if obj.enrolled_by:
            return {
                'id': obj.enrolled_by.id,
                'name': obj.enrolled_by.get_full_name(),
                'registration_number': obj.enrolled_by.registration_number,
            }
        return None

    def get_approved_by_info(self, obj):
        if obj.approved_by:
            return {
                'id': obj.approved_by.id,
                'name': obj.approved_by.get_full_name(),
                'registration_number': obj.approved_by.registration_number,
            }
        return None

    def validate(self, data):
        """Validate enrollment data"""
        student = data.get('student')
        class_obj = data.get('class_obj')
        session = data.get('session')
        term = data.get('term')

        # Check if student is already enrolled in this session/term/class
        if student and class_obj and session and term:
            existing = StudentEnrollment.objects.filter(
                student=student,
                class_obj=class_obj,
                session=session,
                term=term
            ).exists()

            if existing:
                raise serializers.ValidationError(
                    "Student is already enrolled in this class for the specified session/term"
                )

        return data


class StudentFeeUpdateSerializer(serializers.Serializer):
    """Serializer for updating student fees"""

    amount_paid = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=0.01,
        help_text="Amount paid by student"
    )
    payment_date = serializers.DateField(
        required=False,
        default=timezone.now().date,
        help_text="Date of payment"
    )
    fee_payment_evidence = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Receipt or evidence of payment"
    )
    payment_method = serializers.CharField(
        required=False,
        max_length=50,
        help_text="Payment method (cash, bank transfer, etc.)"
    )
    transaction_reference = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Transaction reference number"
    )

    def validate_amount_paid(self, value):
        """Validate amount paid"""
        if value <= 0:
            raise serializers.ValidationError("Amount paid must be greater than 0")
        return value


class StudentPromotionSerializer(serializers.Serializer):
    """Serializer for promoting students"""

    new_class_level_id = serializers.IntegerField(
        required=True,
        help_text="ID of the new class level"
    )
    promotion_date = serializers.DateField(
        required=False,
        default=timezone.now().date,
        help_text="Date of promotion"
    )
    remarks = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Promotion remarks"
    )

    def validate_new_class_level_id(self, value):
        """Validate new class level exists"""
        from academic.models import ClassLevel
        try:
            class_level = ClassLevel.objects.get(id=value)
        except ClassLevel.DoesNotExist:
            raise serializers.ValidationError("Class level does not exist")
        return value


class StudentAttendanceUpdateSerializer(serializers.Serializer):
    """Serializer for updating student attendance"""

    date = serializers.DateField(
        required=True,
        help_text="Attendance date"
    )
    status = serializers.ChoiceField(
        choices=['present', 'absent', 'late', 'half_day', 'excused'],
        required=True,
        help_text="Attendance status"
    )
    remarks = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Attendance remarks"
    )
    check_in_time = serializers.TimeField(
        required=False,
        help_text="Check-in time (for late arrivals)"
    )
    check_out_time = serializers.TimeField(
        required=False,
        help_text="Check-out time (for early departures)"
    )

    def validate_date(self, value):
        """Validate date is not in the future"""
        if value > timezone.now().date():
            raise serializers.ValidationError("Attendance date cannot be in the future")
        return value


class BulkStudentCreateSerializer(serializers.Serializer):
    """Serializer for bulk student creation"""

    students = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="List of student objects to create"
    )

    def validate_students(self, value):
        """Validate student list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Students must be a list")

        if len(value) == 0:
            raise serializers.ValidationError("Student list cannot be empty")

        if len(value) > 100:
            raise serializers.ValidationError("Cannot create more than 100 students at once")

        # Validate each student object
        for i, student in enumerate(value):
            if not isinstance(student, dict):
                raise serializers.ValidationError(f"Student at index {i} must be a dictionary")

            # Check required fields
            required_fields = ['user', 'class_level_id', 'admission_date']
            for field in required_fields:
                if field not in student:
                    raise serializers.ValidationError(
                        f"Student at index {i} missing required field: {field}"
                    )

            # Validate user data
            user_data = student.get('user', {})
            user_required = ['first_name', 'last_name', 'email', 'phone_number']
            for field in user_required:
                if field not in user_data:
                    raise serializers.ValidationError(
                        f"Student at index {i} user data missing required field: {field}"
                    )

        return value


class StudentAcademicReportSerializer(serializers.Serializer):
    """Serializer for student academic reports"""

    student = StudentSerializer(read_only=True)
    session = serializers.DictField(read_only=True)
    term = serializers.DictField(read_only=True)
    class_level = serializers.DictField(read_only=True)
    enrollments = StudentEnrollmentSerializer(many=True, read_only=True)
    results = serializers.ListField(read_only=True)
    average_score = serializers.FloatField(read_only=True)
    position_in_class = serializers.IntegerField(read_only=True)
    overall_grade = serializers.CharField(read_only=True)
    recommendations = serializers.SerializerMethodField(read_only=True)

    def get_recommendations(self, obj):
        """Generate recommendations based on performance"""
        recommendations = []

        if obj['average_score'] < 40:
            recommendations.append("Needs academic support and tutoring")
            recommendations.append("Consider parent-teacher conference")

        if obj['average_score'] >= 75:
            recommendations.append("Excellent performance, keep it up!")
            recommendations.append("Consider advanced placement opportunities")

        # Add attendance recommendations if available
        if hasattr(obj['student'], 'attendance_rate'):
            if obj['student'].attendance_rate < 80:
                recommendations.append("Improve attendance rate")

        return recommendations