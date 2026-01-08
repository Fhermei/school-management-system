from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    AcademicSession, AcademicTerm, Program, ClassLevel, Subject,
    Class, ClassSubject, Timetable, TimetableEntry, StudentEnrollment
)
from users.serializers import UserProfileSerializer


class AcademicSessionSerializer(serializers.ModelSerializer):
    """Serializer for AcademicSession model"""

    duration_days = serializers.SerializerMethodField(read_only=True)
    is_active_today = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AcademicSession
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_days', 'is_active_today']

    def get_duration_days(self, obj):
        return obj.get_duration_days()

    def get_is_active_today(self, obj):
        return obj.is_active_today()

    def validate(self, data):
        """Validate session dates"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
        return data


class AcademicTermSerializer(serializers.ModelSerializer):
    """Serializer for AcademicTerm model"""

    session_info = serializers.SerializerMethodField(read_only=True)
    duration_days = serializers.SerializerMethodField(read_only=True)
    is_active_today = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AcademicTerm
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_days', 'is_active_today']

    def get_session_info(self, obj):
        return {
            'id': obj.session.id,
            'name': obj.session.name,
            'start_date': obj.session.start_date,
            'end_date': obj.session.end_date,
        }

    def get_duration_days(self, obj):
        return obj.get_duration_days()

    def get_is_active_today(self, obj):
        return obj.is_active_today()

    def validate(self, data):
        """Validate term dates"""
        session = data.get('session') or (self.instance.session if self.instance else None)

        if data.get('start_date') and data.get('end_date') and session:
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })

            # Check if dates are within session
            if data['start_date'] < session.start_date or data['end_date'] > session.end_date:
                raise serializers.ValidationError({
                    'dates': 'Term dates must be within session dates'
                })

        return data


class ProgramSerializer(serializers.ModelSerializer):
    """Serializer for Program model"""

    class_levels_count = serializers.SerializerMethodField(read_only=True)
    subjects_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Program
        fields = '__all__'
        read_only_fields = ['id', 'code', 'created_at', 'updated_at', 'class_levels_count', 'subjects_count']

    def get_class_levels_count(self, obj):
        return obj.class_levels.count()

    def get_subjects_count(self, obj):
        return obj.subjects.count()


class ClassLevelSerializer(serializers.ModelSerializer):
    """Serializer for ClassLevel model"""

    program_info = serializers.SerializerMethodField(read_only=True)
    next_level_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ClassLevel
        fields = '__all__'
        read_only_fields = ['id', 'code', 'name', 'created_at', 'updated_at', 'next_level_info']

    def get_program_info(self, obj):
        return {
            'id': obj.program.id,
            'name': obj.program.name,
            'code': obj.program.code,
        }

    def get_next_level_info(self, obj):
        next_level = obj.get_next_level()
        if next_level:
            return {
                'id': next_level.id,
                'name': next_level.name,
                'code': next_level.code,
            }
        return None


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model"""

    programs_info = serializers.SerializerMethodField(read_only=True)
    class_levels_info = serializers.SerializerMethodField(read_only=True)
    created_by_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subject
        fields = '__all__'
        read_only_fields = [
            'id', 'code', 'total_teaching_hours', 'created_at', 'updated_at',
            'programs_info', 'class_levels_info', 'created_by_info'
        ]

    def get_programs_info(self, obj):
        return [
            {
                'id': program.id,
                'name': program.name,
                'code': program.code,
            }
            for program in obj.programs.all()
        ]

    def get_class_levels_info(self, obj):
        return [
            {
                'id': level.id,
                'name': level.name,
                'code': level.code,
            }
            for level in obj.class_levels.all()
        ]

    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'name': obj.created_by.get_full_name(),
                'registration_number': obj.created_by.registration_number,
            }
        return None


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for Class model"""

    session_info = serializers.SerializerMethodField(read_only=True)
    term_info = serializers.SerializerMethodField(read_only=True)
    class_level_info = serializers.SerializerMethodField(read_only=True)
    class_teacher_info = serializers.SerializerMethodField(read_only=True)
    assistant_class_teacher_info = serializers.SerializerMethodField(read_only=True)
    available_seats = serializers.SerializerMethodField(read_only=True)
    is_full = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = [
            'id', 'code', 'slug', 'created_at', 'updated_at',
            'available_seats', 'is_full', 'current_enrollment'
        ]

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

    def get_class_level_info(self, obj):
        return {
            'id': obj.class_level.id,
            'name': obj.class_level.name,
            'code': obj.class_level.code,
            'program': {
                'id': obj.class_level.program.id,
                'name': obj.class_level.program.name,
            }
        }

    def get_class_teacher_info(self, obj):
        if obj.class_teacher:
            return {
                'id': obj.class_teacher.id,
                'name': obj.class_teacher.get_full_name(),
                'registration_number': obj.class_teacher.registration_number,
                'role': obj.class_teacher.get_role_display(),
            }
        return None

    def get_assistant_class_teacher_info(self, obj):
        if obj.assistant_class_teacher:
            return {
                'id': obj.assistant_class_teacher.id,
                'name': obj.assistant_class_teacher.get_full_name(),
                'registration_number': obj.assistant_class_teacher.registration_number,
                'role': obj.assistant_class_teacher.get_role_display(),
            }
        return None

    def get_available_seats(self, obj):
        return obj.get_available_seats()

    def get_is_full(self, obj):
        return obj.is_full()

    def validate(self, data):
        """Validate class data"""
        # Ensure term belongs to session
        if data.get('term') and data.get('session'):
            if data['term'].session != data['session']:
                raise serializers.ValidationError({
                    'term': 'Selected term does not belong to the selected session'
                })

        return data


class ClassSubjectSerializer(serializers.ModelSerializer):
    """Serializer for ClassSubject model"""

    class_obj_info = serializers.SerializerMethodField(read_only=True)
    subject_info = serializers.SerializerMethodField(read_only=True)
    teacher_info = serializers.SerializerMethodField(read_only=True)
    co_teacher_info = serializers.SerializerMethodField(read_only=True)
    preferred_days_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ClassSubject
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'preferred_days_list'
        ]

    def get_class_obj_info(self, obj):
        return {
            'id': obj.class_obj.id,
            'name': obj.class_obj.name,
            'code': obj.class_obj.code,
        }

    def get_subject_info(self, obj):
        return {
            'id': obj.subject.id,
            'name': obj.subject.name,
            'code': obj.subject.code,
            'subject_type': obj.subject.subject_type,
        }

    def get_teacher_info(self, obj):
        if obj.teacher:
            return {
                'id': obj.teacher.id,
                'name': obj.teacher.get_full_name(),
                'registration_number': obj.teacher.registration_number,
                'role': obj.teacher.get_role_display(),
            }
        return None

    def get_co_teacher_info(self, obj):
        if obj.co_teacher:
            return {
                'id': obj.co_teacher.id,
                'name': obj.co_teacher.get_full_name(),
                'registration_number': obj.co_teacher.registration_number,
                'role': obj.co_teacher.get_role_display(),
            }
        return None

    def get_preferred_days_list(self, obj):
        return obj.get_preferred_days_list()

    def validate(self, data):
        """Validate class-subject assignment"""
        class_obj = data.get('class_obj') or (self.instance.class_obj if self.instance else None)
        subject = data.get('subject') or (self.instance.subject if self.instance else None)
        teacher = data.get('teacher')

        # Check if subject is offered in class level
        if class_obj and subject:
            if not subject.class_levels.filter(id=class_obj.class_level.id).exists():
                raise serializers.ValidationError({
                    'subject': f'Subject {subject.name} is not offered in {class_obj.class_level.name}'
                })

        # Check if teacher can teach this subject
        if teacher and subject:
            if not subject.can_be_taught_by(teacher):
                raise serializers.ValidationError({
                    'teacher': f'Teacher {teacher.get_full_name()} cannot teach {subject.name}'
                })

        return data


class TimetableSerializer(serializers.ModelSerializer):
    """Serializer for Timetable model"""

    session_info = serializers.SerializerMethodField(read_only=True)
    term_info = serializers.SerializerMethodField(read_only=True)
    program_info = serializers.SerializerMethodField(read_only=True)
    class_level_info = serializers.SerializerMethodField(read_only=True)
    class_obj_info = serializers.SerializerMethodField(read_only=True)
    teacher_info = serializers.SerializerMethodField(read_only=True)
    created_by_info = serializers.SerializerMethodField(read_only=True)
    approved_by_info = serializers.SerializerMethodField(read_only=True)
    days_list = serializers.SerializerMethodField(read_only=True)
    break_periods_list = serializers.SerializerMethodField(read_only=True)
    period_schedule = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Timetable
        fields = '__all__'
        read_only_fields = [
            'id', 'code', 'created_at', 'updated_at', 'days_list',
            'break_periods_list', 'period_schedule'
        ]

    def get_session_info(self, obj):
        return {
            'id': obj.session.id,
            'name': obj.session.name,
        }

    def get_term_info(self, obj):
        return {
            'id': obj.term.id,
            'name': obj.term.name,
            'term': obj.term.term,
        }

    def get_program_info(self, obj):
        if obj.program:
            return {
                'id': obj.program.id,
                'name': obj.program.name,
                'code': obj.program.code,
            }
        return None

    def get_class_level_info(self, obj):
        if obj.class_level:
            return {
                'id': obj.class_level.id,
                'name': obj.class_level.name,
                'code': obj.class_level.code,
            }
        return None

    def get_class_obj_info(self, obj):
        if obj.class_obj:
            return {
                'id': obj.class_obj.id,
                'name': obj.class_obj.name,
                'code': obj.class_obj.code,
            }
        return None

    def get_teacher_info(self, obj):
        if obj.teacher:
            return {
                'id': obj.teacher.id,
                'name': obj.teacher.get_full_name(),
                'registration_number': obj.teacher.registration_number,
            }
        return None

    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'name': obj.created_by.get_full_name(),
                'registration_number': obj.created_by.registration_number,
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

    def get_days_list(self, obj):
        return obj.get_days_list()

    def get_break_periods_list(self, obj):
        return obj.get_break_periods_list()

    def get_period_schedule(self, obj):
        return obj.generate_period_schedule()

    def validate(self, data):
        """Validate timetable data"""
        # Validate scope-target consistency
        scope = data.get('scope') or (self.instance.scope if self.instance else None)

        if scope == 'program' and not data.get('program'):
            raise serializers.ValidationError({
                'program': 'Program scope requires a program target'
            })
        elif scope == 'class_level' and not data.get('class_level'):
            raise serializers.ValidationError({
                'class_level': 'Class level scope requires a class level target'
            })
        elif scope == 'class' and not data.get('class_obj'):
            raise serializers.ValidationError({
                'class_obj': 'Class scope requires a class target'
            })
        elif scope == 'teacher' and not data.get('teacher'):
            raise serializers.ValidationError({
                'teacher': 'Teacher scope requires a teacher target'
            })

        return data


class TimetableEntrySerializer(serializers.ModelSerializer):
    """Serializer for TimetableEntry model"""

    timetable_info = serializers.SerializerMethodField(read_only=True)
    subject_info = serializers.SerializerMethodField(read_only=True)
    teacher_info = serializers.SerializerMethodField(read_only=True)
    class_obj_info = serializers.SerializerMethodField(read_only=True)
    period_time = serializers.SerializerMethodField(read_only=True)
    created_by_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TimetableEntry
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'period_time'
        ]

    def get_timetable_info(self, obj):
        return {
            'id': obj.timetable.id,
            'name': obj.timetable.name,
            'code': obj.timetable.code,
        }

    def get_subject_info(self, obj):
        if obj.subject:
            return {
                'id': obj.subject.id,
                'name': obj.subject.name,
                'code': obj.subject.code,
            }
        return None

    def get_teacher_info(self, obj):
        if obj.teacher:
            return {
                'id': obj.teacher.id,
                'name': obj.teacher.get_full_name(),
                'registration_number': obj.teacher.registration_number,
            }
        return None

    def get_class_obj_info(self, obj):
        if obj.class_obj:
            return {
                'id': obj.class_obj.id,
                'name': obj.class_obj.name,
                'code': obj.class_obj.code,
            }
        return None

    def get_period_time(self, obj):
        # Get period time from timetable schedule
        if obj.timetable:
            schedule = obj.timetable.generate_period_schedule()
            for period in schedule:
                if period['period'] == obj.period_number:
                    return {
                        'start_time': period['start_time'],
                        'end_time': period['end_time'],
                        'is_break': period['is_break'],
                        'is_lunch': period['is_lunch'],
                        'is_assembly': period['is_assembly'],
                    }
        return None

    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'name': obj.created_by.get_full_name(),
                'registration_number': obj.created_by.registration_number,
            }
        return None

    def validate(self, data):
        """Validate timetable entry"""
        timetable = data.get('timetable') or (self.instance.timetable if self.instance else None)
        period_number = data.get('period_number')

        if timetable and period_number:
            if period_number < 1 or period_number > timetable.periods_per_day:
                raise serializers.ValidationError({
                    'period_number': f'Period number must be between 1 and {timetable.periods_per_day}'
                })

        # Validate teacher assignment
        if data.get('teacher') and data.get('subject'):
            if not data['subject'].can_be_taught_by(data['teacher']):
                raise serializers.ValidationError({
                    'teacher': f'Teacher {data["teacher"].get_full_name()} cannot teach {data["subject"].name}'
                })

        return data


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for StudentEnrollment model"""

    student_info = serializers.SerializerMethodField(read_only=True)
    class_obj_info = serializers.SerializerMethodField(read_only=True)
    session_info = serializers.SerializerMethodField(read_only=True)
    term_info = serializers.SerializerMethodField(read_only=True)
    enrolled_by_info = serializers.SerializerMethodField(read_only=True)
    approved_by_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = '__all__'
        read_only_fields = [
            'id', 'enrollment_number', 'created_at', 'updated_at'
        ]

    def get_student_info(self, obj):
        return {
            'id': obj.student.id,
            'name': obj.student.get_full_name(),
            'registration_number': obj.student.registration_number,
            'email': obj.student.email,
        }

    def get_class_obj_info(self, obj):
        return {
            'id': obj.class_obj.id,
            'name': obj.class_obj.name,
            'code': obj.class_obj.code,
            'class_level': obj.class_obj.class_level.name,
        }

    def get_session_info(self, obj):
        return {
            'id': obj.session.id,
            'name': obj.session.name,
        }

    def get_term_info(self, obj):
        return {
            'id': obj.term.id,
            'name': obj.term.name,
            'term': obj.term.term,
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
        student = data.get('student') or (self.instance.student if self.instance else None)
        class_obj = data.get('class_obj') or (self.instance.class_obj if self.instance else None)
        session = data.get('session') or (self.instance.session if self.instance else None)
        term = data.get('term') or (self.instance.term if self.instance else None)

        # Check if student can be enrolled in this class
        if student and class_obj:
            # Check if student has student profile
            if hasattr(student, 'student_profile'):
                student_profile = student.student_profile
                # Check age requirements
                if student_profile.user.date_of_birth:
                    from datetime import date
                    today = date.today()
                    age = today.year - student_profile.user.date_of_birth.year

                    if (class_obj.class_level.min_age and age < class_obj.class_level.min_age):
                        raise serializers.ValidationError({
                            'student': f'Student is too young for {class_obj.class_level.name}. Minimum age: {class_obj.class_level.min_age}'
                        })

                    if (class_obj.class_level.max_age and age > class_obj.class_level.max_age):
                        raise serializers.ValidationError({
                            'student': f'Student is too old for {class_obj.class_level.name}. Maximum age: {class_obj.class_level.max_age}'
                        })

            # Check if class is full
            if class_obj.is_full():
                raise serializers.ValidationError({
                    'class_obj': f'Class {class_obj.name} is full'
                })

        # Check if term belongs to session
        if term and session and term.session != session:
            raise serializers.ValidationError({
                'term': 'Selected term does not belong to the selected session'
            })

        return data


class ClassDashboardSerializer(serializers.Serializer):
    """Serializer for class dashboard data"""

    class_info = ClassSerializer(read_only=True)
    class_teacher = UserProfileSerializer(read_only=True)
    subjects = serializers.SerializerMethodField(read_only=True)
    enrolled_students = serializers.SerializerMethodField(read_only=True)
    timetable = serializers.SerializerMethodField(read_only=True)
    statistics = serializers.SerializerMethodField(read_only=True)

    def get_subjects(self, obj):
        """Get subjects offered in this class"""
        class_subjects = obj.class_subjects.filter(is_active=True)
        return ClassSubjectSerializer(class_subjects, many=True).data

    def get_enrolled_students(self, obj):
        """Get enrolled students"""
        from students.models import StudentEnrollment
        enrollments = StudentEnrollment.objects.filter(
            class_obj=obj,
            status='active'
        ).select_related('student')
        return StudentEnrollmentSerializer(enrollments, many=True).data

    def get_timetable(self, obj):
        """Get class timetable"""
        timetable = obj.timetables.filter(is_active=True).first()
        if timetable:
            return TimetableSerializer(timetable).data
        return None

    def get_statistics(self, obj):
        """Get class statistics"""
        return {
            'total_students': obj.current_enrollment,
            'available_seats': obj.get_available_seats(),
            'is_full': obj.is_full(),
            'subjects_count': obj.class_subjects.filter(is_active=True).count(),
            'attendance_rate': 0,  # Would calculate from attendance records
            'average_score': 0,  # Would calculate from exam records
        }


class TeacherTimetableSerializer(serializers.Serializer):
    """Serializer for teacher's timetable view"""

    teacher = UserProfileSerializer(read_only=True)
    timetable = TimetableSerializer(read_only=True)
    weekly_schedule = serializers.SerializerMethodField(read_only=True)
    teaching_load = serializers.SerializerMethodField(read_only=True)
    assigned_classes = serializers.SerializerMethodField(read_only=True)
    assigned_subjects = serializers.SerializerMethodField(read_only=True)

    def get_weekly_schedule(self, obj):
        """Get weekly teaching schedule"""
        teacher = obj.get('teacher')
        timetable = obj.get('timetable')

        if not teacher or not timetable:
            return {}

        entries = TimetableEntry.objects.filter(
            teacher=teacher,
            timetable__is_active=True,
            is_active=True
        ).select_related('subject', 'class_obj', 'timetable')

        # Organize by day
        schedule = {}
        for entry in entries:
            day = entry.day
            if day not in schedule:
                schedule[day] = []

            period_time = entry.get_period_time()
            schedule[day].append({
                'period': entry.period_number,
                'start_time': period_time['start_time'] if period_time else None,
                'end_time': period_time['end_time'] if period_time else None,
                'subject': entry.subject.name if entry.subject else entry.get_entry_type_display(),
                'class': entry.class_obj.name if entry.class_obj else 'N/A',
                'room': entry.room,
            })

        # Sort by period number
        for day in schedule:
            schedule[day].sort(key=lambda x: x['period'])

        return schedule

    def get_teaching_load(self, obj):
        """Calculate teaching load"""
        teacher = obj.get('teacher')

        if not teacher:
            return {}

        entries = TimetableEntry.objects.filter(
            teacher=teacher,
            timetable__is_active=True,
            is_active=True,
            entry_type='subject'
        )

        total_periods = entries.count()
        total_subjects = entries.values('subject').distinct().count()
        total_classes = entries.values('class_obj').distinct().count()

        return {
            'total_periods': total_periods,
            'total_subjects': total_subjects,
            'total_classes': total_classes,
            'periods_per_week': total_periods,
        }

    def get_assigned_classes(self, obj):
        """Get assigned classes"""
        teacher = obj.get('teacher')

        if not teacher:
            return []

        # Get classes where teacher is class teacher
        class_teacher_classes = Class.objects.filter(
            class_teacher=teacher,
            is_active=True
        )

        # Get classes where teacher teaches subjects
        teaching_classes = Class.objects.filter(
            class_subjects__teacher=teacher,
            class_subjects__is_active=True,
            is_active=True
        ).distinct()

        all_classes = (class_teacher_classes | teaching_classes).distinct()

        return ClassSerializer(all_classes, many=True).data

    def get_assigned_subjects(self, obj):
        """Get assigned subjects"""
        teacher = obj.get('teacher')

        if not teacher:
            return []

        class_subjects = ClassSubject.objects.filter(
            teacher=teacher,
            is_active=True
        ).select_related('subject').distinct('subject')

        subjects = [cs.subject for cs in class_subjects]
        return SubjectSerializer(subjects, many=True).data


class BulkClassSubjectAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk class-subject assignments"""

    assignments = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of assignment objects"
    )

    def validate_assignments(self, value):
        """Validate assignment list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Assignments must be a list")

        for i, assignment in enumerate(value):
            if not isinstance(assignment, dict):
                raise serializers.ValidationError(f"Assignment at index {i} must be a dictionary")

            required_fields = ['class_id', 'subject_id', 'teacher_id']
            for field in required_fields:
                if field not in assignment:
                    raise serializers.ValidationError(f"Assignment at index {i} missing required field: {field}")

        return value


class GenerateTimetableSerializer(serializers.Serializer):
    """Serializer for timetable generation request"""

    timetable_id = serializers.IntegerField(required=False)
    class_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of class IDs to include in timetable"
    )

    # Generation options
    optimize_teacher_load = serializers.BooleanField(default=True)
    avoid_teacher_conflicts = serializers.BooleanField(default=True)
    avoid_class_conflicts = serializers.BooleanField(default=True)
    respect_preferred_times = serializers.BooleanField(default=True)
    max_periods_per_day = serializers.IntegerField(default=8, min_value=4, max_value=10)

    def validate(self, data):
        """Validate generation request"""
        if not data.get('timetable_id') and not data.get('class_ids'):
            raise serializers.ValidationError(
                "Either timetable_id or class_ids must be provided"
            )

        return data


class AcademicDashboardSerializer(serializers.Serializer):
    """Serializer for academic dashboard data"""

    current_session = AcademicSessionSerializer(read_only=True)
    current_term = AcademicTermSerializer(read_only=True)
    statistics = serializers.DictField(read_only=True)
    recent_classes = ClassSerializer(many=True, read_only=True)
    recent_enrollments = StudentEnrollmentSerializer(many=True, read_only=True)


class ClassStatisticsSerializer(serializers.Serializer):
    """Serializer for class statistics"""

    class_level_statistics = serializers.ListField(read_only=True)
    program_statistics = serializers.ListField(read_only=True)