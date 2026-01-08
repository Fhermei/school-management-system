from rest_framework import generics, permissions, status, filters, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, Avg
from django.db import transaction
from django.utils import timezone
import logging

from .models import Student, StudentEnrollment
from .serializers import (
    StudentSerializer, StudentCreateSerializer, StudentListSerializer,
    StudentDetailSerializer, StudentDashboardSerializer, StudentEnrollmentSerializer,
    StudentFeeUpdateSerializer, StudentPromotionSerializer, StudentAttendanceUpdateSerializer,
    BulkStudentCreateSerializer, StudentAcademicReportSerializer
)
from .permissions import (
    IsAdminOrPrincipal, IsAccountantOrSecretary, IsTeachingStaff,
    CanEditStudent, CanEditFee, CanViewStudentRecords, CanManageAttendance,
    IsStudentOrParent, CanPromoteStudent, CanManageStudentEnrollment
)
from users.models import User

logger = logging.getLogger(__name__)


class StudentListView(generics.ListAPIView):
    """
    List all students with filtering and search

    GET /api/students/

    Filters: class_level, stream, fee_status, student_category, is_active
    Search: name, admission_number, student_id
    Ordering: name, class_level, admission_date

    Permissions: Admin/Principal/Teachers/Accountant/Secretary
    """

    serializer_class = StudentListSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewStudentRecords]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['class_level', 'stream', 'fee_status', 'student_category', 'is_active', 'is_graduated']
    search_fields = [
        'user__first_name', 'user__last_name',
        'admission_number', 'student_id',
        'user__registration_number', 'user__email'
    ]
    ordering_fields = ['user__first_name', 'class_level__order', 'admission_date', 'average_score']
    ordering = ['class_level__order', 'user__first_name']

    def get_queryset(self):
        """Filter students based on user permissions"""
        user = self.request.user

        # Admin/Principal can see all students
        if user.role in ['head', 'principal', 'vice_principal'] or user.is_staff:
            return Student.objects.select_related(
                'user', 'class_level', 'father', 'mother'
            ).all()

        # Accountant/Secretary can see all students
        if user.role in ['accountant', 'secretary']:
            return Student.objects.select_related(
                'user', 'class_level', 'father', 'mother'
            ).all()

        # Teachers can see students in their classes
        if user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            # Get classes where teacher is class teacher
            from academic.models import Class
            teaching_classes = Class.objects.filter(
                Q(class_teacher=user) | Q(assistant_class_teacher=user)
            )

            # Get students in those classes
            return Student.objects.filter(
                class_level__in=teaching_classes.values('class_level')
            ).select_related('user', 'class_level', 'father', 'mother')

        # Parents can only see their own children
        if user.role == 'parent':
            try:
                parent_profile = user.parent_profile
                return Student.objects.filter(
                    Q(father=parent_profile) | Q(mother=parent_profile)
                ).select_related('user', 'class_level', 'father', 'mother')
            except:
                return Student.objects.none()

        # Students can only see themselves
        if user.role == 'student':
            try:
                return Student.objects.filter(user=user).select_related(
                    'user', 'class_level', 'father', 'mother'
                )
            except:
                return Student.objects.none()

        return Student.objects.none()


class StudentCreateView(generics.CreateAPIView):
    """
    Create new student

    POST /api/students/create/

    Required: user_id, class_level_id, admission_date
    Optional: father_id, mother_id, stream, etc.

    Permissions: Admin/Principal/Secretary only
    """

    serializer_class = StudentCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPrincipal]

    def create(self, request, *args, **kwargs):
        """Create student with transaction"""
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            student = serializer.save()

            logger.info(
                f"Student created: {student.admission_number} "
                f"by {request.user.registration_number}"
            )

            return Response({
                'message': 'Student created successfully',
                'student': StudentSerializer(student).data
            }, status=status.HTTP_201_CREATED)


class StudentDetailView(generics.RetrieveAPIView):
    """
    Get student details

    GET /api/students/{id}/

    Permissions: Based on user role and relationship
    """

    serializer_class = StudentDetailSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditStudent]
    queryset = Student.objects.select_related(
        'user', 'class_level', 'father', 'mother'
    ).prefetch_related('enrollments')

    def get_object(self):
        """Get student with permission checks"""
        student = super().get_object()

        # Check object-level permissions
        self.check_object_permissions(self.request, student)

        return student


class StudentUpdateView(generics.UpdateAPIView):
    """
    Update student profile

    PUT/PATCH /api/students/{id}/update/

    Permissions: Based on user role and relationship
    """

    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditStudent]
    queryset = Student.objects.select_related('user', 'class_level')

    def update(self, request, *args, **kwargs):
        """Update student with permission checks"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check object-level permissions
        self.check_object_permissions(request, instance)

        # Parents can only update limited fields
        if request.user.role == 'parent':
            allowed_fields = [
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relationship', 'transportation_mode',
                'bus_route', 'medical_conditions', 'allergies'
            ]

            for field in request.data:
                if field not in allowed_fields:
                    return Response({
                        'error': f'You cannot modify the {field} field'
                    }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        logger.info(f"Student updated: {instance.admission_number} by {request.user.registration_number}")

        return Response({
            'message': 'Student updated successfully',
            'student': serializer.data
        })


class StudentDashboardView(APIView):
    """
    Student dashboard with comprehensive information

    GET /api/students/{id}/dashboard/

    Permissions: Student can view own, admin/teachers can view others
    """

    permission_classes = [permissions.IsAuthenticated, CanViewStudentRecords]

    def get(self, request, pk=None):
        """Get student dashboard"""
        if pk is None and request.user.role == 'student':
            # Student viewing own dashboard
            try:
                student = request.user.student_profile
            except Student.DoesNotExist:
                return Response({
                    'error': 'Student profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Viewing specific student dashboard
            student = get_object_or_404(
                Student.objects.select_related(
                    'user', 'class_level', 'father', 'mother'
                ).prefetch_related('enrollments'),
                pk=pk
            )

            # Check permissions
            if not self._can_view_dashboard(request.user, student):
                return Response({
                    'error': 'You do not have permission to view this dashboard'
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = StudentDashboardSerializer(student)

        return Response({
            'dashboard': serializer.data,
            'quick_stats': self._get_quick_stats(student)
        })

    def _can_view_dashboard(self, user, student):
        """Check if user can view student dashboard"""
        # Admin/Principal can view all
        if user.role in ['head', 'principal', 'vice_principal'] or user.is_staff:
            return True

        # Accountant/Secretary can view all
        if user.role in ['accountant', 'secretary']:
            return True

        # Teachers can view students in their classes
        if user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            # Check if teacher is class teacher for this student
            from staff.models import TeacherProfile
            try:
                teacher_profile = user.staff_profile.teacher_profile
                return teacher_profile.is_class_teacher_of(student)
            except:
                return False

        # Parents can view their children
        if user.role == 'parent':
            try:
                parent = user.parent_profile
                return student.father == parent or student.mother == parent
            except:
                return False

        # Students can view themselves
        if user.role == 'student':
            return student.user == user

        return False

    def _get_quick_stats(self, student):
        """Get quick statistics for dashboard"""
        stats = {
            'attendance_rate': 0,
            'average_score': float(student.average_score),
            'position_in_class': student.position_in_class,
            'fee_status': student.fee_status,
            'balance_due': float(student.balance_due),
            'days_present': student.days_present,
            'days_absent': student.days_absent,
            'days_late': student.days_late,
        }

        # Calculate attendance rate
        total_days = student.days_present + student.days_absent
        if total_days > 0:
            stats['attendance_rate'] = round((student.days_present / total_days) * 100, 2)

        return stats


class UpdateStudentFeeView(APIView):
    """
    Update student fee information

    POST /api/students/{id}/update-fee/

    Required: amount_paid, payment_date (optional), payment_evidence (optional)

    Permissions: Accountant/Admin only
    """

    permission_classes = [permissions.IsAuthenticated, CanEditFee]

    def post(self, request, pk):
        """Update student fee payment"""
        student = get_object_or_404(Student, pk=pk)

        serializer = StudentFeeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update fee information
        amount_paid = serializer.validated_data['amount_paid']
        payment_date = serializer.validated_data.get('payment_date', timezone.now().date())
        payment_evidence = serializer.validated_data.get('fee_payment_evidence', None)

        # Update student fee
        student.amount_paid += amount_paid
        student.last_payment_date = payment_date

        if payment_evidence:
            student.fee_payment_evidence = payment_evidence

        # Recalculate balance and status
        student.balance_due = student.total_fee_amount - student.amount_paid

        if student.amount_paid >= student.total_fee_amount:
            student.fee_status = 'paid_full'
        elif student.amount_paid > 0:
            student.fee_status = 'paid_partial'
        else:
            student.fee_status = 'not_paid'

        student.save()

        logger.info(
            f"Fee updated for student {student.admission_number}: "
            f"Amount paid: {amount_paid}, Balance: {student.balance_due} "
            f"by {request.user.registration_number}"
        )

        return Response({
            'message': 'Fee updated successfully',
            'fee_summary': student.get_fee_summary(),
            'student': StudentSerializer(student).data
        })


class PromoteStudentView(APIView):
    """
    Promote student to next class level

    POST /api/students/{id}/promote/

    Required: new_class_level_id, promotion_date

    Permissions: Admin/Principal only
    """

    permission_classes = [permissions.IsAuthenticated, CanPromoteStudent]

    def post(self, request, pk):
        """Promote student to next class"""
        student = get_object_or_404(Student, pk=pk)

        serializer = StudentPromotionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_class_level = serializer.validated_data['new_class_level']
        promotion_date = serializer.validated_data.get('promotion_date', timezone.now().date())

        # Check if promotion is valid
        if not self._can_promote(student, new_class_level):
            return Response({
                'error': 'Cannot promote student. Check class level progression rules.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update student class level
        old_class_level = student.class_level
        student.class_level = new_class_level
        student.save()

        # Create enrollment record for new class
        from academic.models import AcademicSession, AcademicTerm
        current_session = AcademicSession.objects.filter(is_current=True).first()
        current_term = AcademicTerm.objects.filter(is_current=True).first()

        if current_session and current_term:
            StudentEnrollment.objects.create(
                student=student.user,
                class_obj=None,  # Would need class object in real implementation
                session=current_session,
                term=current_term,
                status='active',
                is_promoted=True,
                promotion_date=promotion_date
            )

        logger.info(
            f"Student {student.admission_number} promoted from "
            f"{old_class_level.name if old_class_level else 'None'} to "
            f"{new_class_level.name} by {request.user.registration_number}"
        )

        return Response({
            'message': f'Student promoted to {new_class_level.name} successfully',
            'old_class': old_class_level.name if old_class_level else 'None',
            'new_class': new_class_level.name,
            'student': StudentSerializer(student).data
        })

    def _can_promote(self, student, new_class_level):
        """Check if student can be promoted to new class level"""
        if not student.class_level:
            return True

        # Check if new class level is in same program
        if student.class_level.program != new_class_level.program:
            return False

        # Check if new class level order is higher (promotion)
        if new_class_level.order <= student.class_level.order:
            return False

        # Check age requirements
        if student.user.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - student.user.date_of_birth.year

            if new_class_level.min_age and age < new_class_level.min_age:
                return False

            if new_class_level.max_age and age > new_class_level.max_age:
                return False

        return True


class BulkStudentCreateView(APIView):
    """
    Create multiple students in bulk (e.g., from CSV upload)

    POST /api/students/bulk-create/

    Permissions: Admin/Principal/Secretary only
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrPrincipal]

    def post(self, request):
        """Create multiple students from bulk data"""
        serializer = BulkStudentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        students_data = serializer.validated_data['students']
        created = []
        errors = []

        with transaction.atomic():
            for i, student_data in enumerate(students_data):
                try:
                    # Create user first
                    user_data = student_data.pop('user')

                    # Check if user already exists
                    if User.objects.filter(email=user_data['email']).exists():
                        errors.append({
                            'index': i,
                            'error': f'User with email {user_data["email"]} already exists'
                        })
                        continue

                    # Create user
                    user = User.objects.create_user(**user_data)

                    # Create student
                    student = Student.objects.create(user=user, **student_data)
                    created.append(student)

                except Exception as e:
                    errors.append({
                        'index': i,
                        'error': str(e)
                    })

        return Response({
            'created_count': len(created),
            'failed_count': len(errors),
            'students': StudentListSerializer(created, many=True).data,
            'errors': errors
        }, status=status.HTTP_201_CREATED)


class StudentEnrollmentListView(generics.ListAPIView):
    """
    List student enrollments

    GET /api/students/enrollments/

    Filters: session, term, class_obj, status
    Search: student name, enrollment_number

    Permissions: Admin/Principal/Teachers
    """

    serializer_class = StudentEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageStudentEnrollment]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['session', 'term', 'class_obj', 'status', 'is_repeating']
    search_fields = [
        'student__first_name', 'student__last_name',
        'student__registration_number', 'enrollment_number'
    ]
    ordering_fields = ['enrollment_date', 'student__first_name']
    ordering = ['-enrollment_date']

    def get_queryset(self):
        """Filter enrollments based on permissions"""
        user = self.request.user

        # Admin/Principal can see all
        if user.role in ['head', 'principal', 'vice_principal'] or user.is_staff:
            return StudentEnrollment.objects.select_related(
                'student', 'class_obj', 'session', 'term'
            ).all()

        # Teachers can see enrollments in their classes
        if user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            # Get classes where teacher is class teacher
            from academic.models import Class
            teaching_classes = Class.objects.filter(
                Q(class_teacher=user) | Q(assistant_class_teacher=user)
            )

            return StudentEnrollment.objects.filter(
                class_obj__in=teaching_classes
            ).select_related('student', 'class_obj', 'session', 'term')

        return StudentEnrollment.objects.none()


class StudentEnrollmentCreateView(generics.CreateAPIView):
    """
    Create student enrollment

    POST /api/students/enrollments/create/

    Required: student_id, class_obj_id, session_id, term_id

    Permissions: Admin/Principal/Secretary only
    """

    serializer_class = StudentEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageStudentEnrollment]

    def create(self, request, *args, **kwargs):
        """Create enrollment with permission checks"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        enrollment = serializer.save(enrolled_by=request.user)

        logger.info(
            f"Enrollment created: {enrollment.enrollment_number} "
            f"for student {enrollment.student.registration_number} "
            f"by {request.user.registration_number}"
        )

        return Response({
            'message': 'Enrollment created successfully',
            'enrollment': StudentEnrollmentSerializer(enrollment).data
        }, status=status.HTTP_201_CREATED)


class StudentAttendanceUpdateView(APIView):
    """
    Update student attendance

    POST /api/students/{id}/attendance/

    Required: date, status (present/absent/late), remarks (optional)

    Permissions: Teachers/Admin
    """

    permission_classes = [permissions.IsAuthenticated, CanManageAttendance]

    def post(self, request, pk):
        """Update student attendance"""
        student = get_object_or_404(Student, pk=pk)

        serializer = StudentAttendanceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        date = serializer.validated_data['date']
        status = serializer.validated_data['status']
        remarks = serializer.validated_data.get('remarks', '')

        # Update student attendance counts
        if status == 'present':
            student.days_present += 1
        elif status == 'absent':
            student.days_absent += 1
        elif status == 'late':
            student.days_late += 1

        student.save()

        # Create attendance record (assuming Attendance app exists)
        try:
            from attendance.models import StudentAttendance
            StudentAttendance.objects.create(
                student=student,
                date=date,
                status=status,
                remarks=remarks,
                recorded_by=request.user
            )
        except ImportError:
            # Attendance app not available
            pass

        logger.info(
            f"Attendance updated for student {student.admission_number}: "
            f"{status} on {date} by {request.user.registration_number}"
        )

        return Response({
            'message': f'Attendance marked as {status} for {date}',
            'attendance_summary': {
                'days_present': student.days_present,
                'days_absent': student.days_absent,
                'days_late': student.days_late
            }
        })


class StudentAcademicReportView(APIView):
    """
    Generate academic report for student

    GET /api/students/{id}/academic-report/

    Query params: session_id, term_id (optional)

    Permissions: Student/Teacher/Admin
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Generate academic report"""
        student = get_object_or_404(Student, pk=pk)

        # Check permissions
        if not self._can_view_report(request.user, student):
            return Response({
                'error': 'You do not have permission to view this report'
            }, status=status.HTTP_403_FORBIDDEN)

        session_id = request.query_params.get('session_id')
        term_id = request.query_params.get('term_id')

        # Get academic data
        report_data = self._generate_report_data(student, session_id, term_id)

        serializer = StudentAcademicReportSerializer(report_data)

        return Response({
            'report': serializer.data,
            'generated_at': timezone.now(),
            'generated_by': request.user.get_full_name()
        })

    def _can_view_report(self, user, student):
        """Check if user can view academic report"""
        # Admin/Principal can view all
        if user.role in ['head', 'principal', 'vice_principal'] or user.is_staff:
            return True

        # Teachers can view reports for their students
        if user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            # Check if teacher teaches this student
            from staff.models import TeacherProfile
            try:
                teacher_profile = user.staff_profile.teacher_profile
                return teacher_profile.is_class_teacher_of(student)
            except:
                return False

        # Parents can view their children's reports
        if user.role == 'parent':
            try:
                parent = user.parent_profile
                return student.father == parent or student.mother == parent
            except:
                return False

        # Students can view their own reports
        if user.role == 'student':
            return student.user == user

        return False

    def _generate_report_data(self, student, session_id=None, term_id=None):
        """Generate academic report data"""
        from academic.models import AcademicSession, AcademicTerm
        from exams.models import Result  # Assuming Exams app exists

        # Get current session/term if not specified
        if not session_id:
            current_session = AcademicSession.objects.filter(is_current=True).first()
            session = current_session
        else:
            session = get_object_or_404(AcademicSession, pk=session_id)

        if not term_id and session:
            current_term = AcademicTerm.objects.filter(is_current=True, session=session).first()
            term = current_term
        elif term_id:
            term = get_object_or_404(AcademicTerm, pk=term_id)
        else:
            term = None

        # Get enrollments
        enrollments = student.enrollments.all()
        if session:
            enrollments = enrollments.filter(session=session)
        if term:
            enrollments = enrollments.filter(term=term)

        # Get results
        results = []
        try:
            results = Result.objects.filter(
                student=student.user,
                session=session,
                term=term
            ).select_related('subject')
        except:
            pass

        return {
            'student': student,
            'session': session,
            'term': term,
            'enrollments': enrollments,
            'results': results,
            'class_level': student.class_level,
            'average_score': student.average_score,
            'position_in_class': student.position_in_class,
            'overall_grade': student.overall_grade
        }


class StudentSearchView(generics.ListAPIView):
    """
    Search students with advanced filtering

    GET /api/students/search/

    Query params: Various filters
    """

    serializer_class = StudentListSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewStudentRecords]

    def get_queryset(self):
        """Advanced student search"""
        queryset = Student.objects.select_related('user', 'class_level')

        # Get query parameters
        name = self.request.query_params.get('name', '')
        admission_number = self.request.query_params.get('admission_number', '')
        class_level_id = self.request.query_params.get('class_level_id', '')
        stream = self.request.query_params.get('stream', '')
        fee_status = self.request.query_params.get('fee_status', '')
        student_category = self.request.query_params.get('student_category', '')
        is_active = self.request.query_params.get('is_active', '')
        is_graduated = self.request.query_params.get('is_graduated', '')

        # Apply filters
        if name:
            queryset = queryset.filter(
                Q(user__first_name__icontains=name) |
                Q(user__last_name__icontains=name)
            )

        if admission_number:
            queryset = queryset.filter(admission_number__icontains=admission_number)

        if class_level_id:
            queryset = queryset.filter(class_level_id=class_level_id)

        if stream and stream != 'all':
            queryset = queryset.filter(stream=stream)

        if fee_status and fee_status != 'all':
            queryset = queryset.filter(fee_status=fee_status)

        if student_category and student_category != 'all':
            queryset = queryset.filter(student_category=student_category)

        if is_active:
            queryset = queryset.filter(is_active=(is_active.lower() == 'true'))

        if is_graduated:
            queryset = queryset.filter(is_graduated=(is_graduated.lower() == 'true'))

        return queryset.order_by('class_level__order', 'user__first_name')


class StudentStatisticsView(APIView):
    """
    Get student statistics for dashboard

    GET /api/students/statistics/

    Permissions: Admin/Principal/Accountant
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrPrincipal]

    def get(self, request):
        """Get comprehensive student statistics"""

        # Overall statistics
        total_students = Student.objects.count()
        active_students = Student.objects.filter(is_active=True).count()
        graduated_students = Student.objects.filter(is_graduated=True).count()

        # Fee statistics
        fee_summary = Student.objects.aggregate(
            total_fee=Sum('total_fee_amount'),
            total_paid=Sum('amount_paid'),
            total_balance=Sum('balance_due')
        )

        # Fee status breakdown
        fee_status_counts = Student.objects.values('fee_status').annotate(
            count=Count('id')
        )

        # Class level distribution
        class_level_distribution = Student.objects.values(
            'class_level__name'
        ).annotate(
            count=Count('id')
        ).order_by('class_level__order')

        # Stream distribution (for secondary)
        stream_distribution = Student.objects.exclude(stream='none').values(
            'stream'
        ).annotate(
            count=Count('id')
        )

        # Student category distribution
        category_distribution = Student.objects.values(
            'student_category'
        ).annotate(
            count=Count('id')
        )

        # Recent enrollments (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_enrollments = Student.objects.filter(
            admission_date__gte=thirty_days_ago
        ).count()

        return Response({
            'overall': {
                'total_students': total_students,
                'active_students': active_students,
                'graduated_students': graduated_students,
                'recent_enrollments': recent_enrollments,
                'inactive_students': total_students - active_students
            },
            'financial': {
                'total_fee': float(fee_summary['total_fee'] or 0),
                'total_paid': float(fee_summary['total_paid'] or 0),
                'total_balance': float(fee_summary['total_balance'] or 0),
                'collection_rate': (float(fee_summary['total_paid'] or 0) /
                                    float(fee_summary['total_fee'] or 1) * 100) if fee_summary['total_fee'] else 0,
                'fee_status_breakdown': list(fee_status_counts)
            },
            'demographics': {
                'class_level_distribution': list(class_level_distribution),
                'stream_distribution': list(stream_distribution),
                'category_distribution': list(category_distribution)
            }
        })