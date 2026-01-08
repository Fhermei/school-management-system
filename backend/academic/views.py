from rest_framework import generics, permissions, status, filters, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.db import transaction
import logging

from .models import (
    AcademicSession, AcademicTerm, Program, ClassLevel, Subject,
    Class, ClassSubject, Timetable, TimetableEntry, StudentEnrollment
)
from .serializers import (
    AcademicSessionSerializer, AcademicTermSerializer, ProgramSerializer,
    ClassLevelSerializer, SubjectSerializer, ClassSerializer,
    ClassSubjectSerializer, TimetableSerializer, TimetableEntrySerializer,
    StudentEnrollmentSerializer, ClassDashboardSerializer,
    TeacherTimetableSerializer, BulkClassSubjectAssignmentSerializer,
    GenerateTimetableSerializer, AcademicDashboardSerializer,
    ClassStatisticsSerializer
)
from .permissions import (
    IsAcademicAdmin, CanManageAcademicStructure, CanManageClasses,
    CanManageSubjects, CanManageTimetables, CanViewTimetable,
    CanEditTimetable, CanManageStudentEnrollment, CanViewClassInformation,
    CanAssignTeachersToSubjects, CanViewSubjectInformation,
    IsSubjectTeacher, CanCreateClassSubjectAssignment,
    CanEditOwnClassSubjectAssignment, CanViewStudentEnrollment,
    AcademicHierarchyPermission, IsClassTeacher, CanAssignClassTeacher
)

logger = logging.getLogger(__name__)


# ============================================
# Academic Session Views
# ============================================

class AcademicSessionListView(generics.ListCreateAPIView):
    """
    List and create academic sessions
    GET /api/academic/sessions/ - List all sessions
    POST /api/academic/sessions/ - Create new session
    Permissions: Academic administrators only
    """
    serializer_class = AcademicSessionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAcademicStructure]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_current']
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'name']
    ordering = ['-start_date']

    def get_queryset(self):
        return AcademicSession.objects.all()

    def perform_create(self, serializer):
        """Create academic session with logged user"""
        serializer.save()
        logger.info(f"Academic session created: {serializer.instance.name} by {self.request.user.registration_number}")


class AcademicSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete academic session
    GET /api/academic/sessions/{id}/ - Get session details
    PUT/PATCH /api/academic/sessions/{id}/ - Update session
    DELETE /api/academic/sessions/{id}/ - Delete session
    Permissions: Academic administrators only
    """
    serializer_class = AcademicSessionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAcademicStructure]
    queryset = AcademicSession.objects.all()

    def perform_update(self, serializer):
        """Update academic session with logging"""
        instance = serializer.save()
        logger.info(f"Academic session updated: {instance.name} by {self.request.user.registration_number}")

    def perform_destroy(self, instance):
        """Delete academic session with logging"""
        logger.info(f"Academic session deleted: {instance.name} by {self.request.user.registration_number}")
        instance.delete()


# ============================================
# Academic Term Views
# ============================================

class AcademicTermListView(generics.ListCreateAPIView):
    """
    List and create academic terms
    GET /api/academic/terms/ - List all terms
    POST /api/academic/terms/ - Create new term
    Permissions: Academic administrators only
    """
    serializer_class = AcademicTermSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAcademicStructure]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session', 'term', 'status', 'is_current']
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'name']
    ordering = ['session__start_date', 'term']

    def get_queryset(self):
        return AcademicTerm.objects.select_related('session').all()

    def perform_create(self, serializer):
        """Create academic term with logged user"""
        serializer.save()
        logger.info(f"Academic term created: {serializer.instance.name} by {self.request.user.registration_number}")


class AcademicTermDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete academic term
    GET /api/academic/terms/{id}/ - Get term details
    PUT/PATCH /api/academic/terms/{id}/ - Update term
    DELETE /api/academic/terms/{id}/ - Delete term
    Permissions: Academic administrators only
    """
    serializer_class = AcademicTermSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAcademicStructure]
    queryset = AcademicTerm.objects.select_related('session')

    def perform_update(self, serializer):
        """Update academic term with logging"""
        instance = serializer.save()
        logger.info(f"Academic term updated: {instance.name} by {self.request.user.registration_number}")

    def perform_destroy(self, instance):
        """Delete academic term with logging"""
        logger.info(f"Academic term deleted: {instance.name} by {self.request.user.registration_number}")
        instance.delete()


# ============================================
# Program Views
# ============================================

class ProgramListView(generics.ListCreateAPIView):
    """
    List and create academic programs
    GET /api/academic/programs/ - List all programs
    POST /api/academic/programs/ - Create new program
    Permissions: Academic administrators only
    """
    serializer_class = ProgramSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAcademicStructure]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['program_type', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'program_type', 'duration_years']
    ordering = ['program_type', 'name']

    def get_queryset(self):
        return Program.objects.all()

    def perform_create(self, serializer):
        """Create program with logged user"""
        serializer.save()
        logger.info(f"Program created: {serializer.instance.name} by {self.request.user.registration_number}")


class ProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete academic program
    GET /api/academic/programs/{id}/ - Get program details
    PUT/PATCH /api/academic/programs/{id}/ - Update program
    DELETE /api/academic/programs/{id}/ - Delete program
    Permissions: Academic administrators only
    """
    serializer_class = ProgramSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAcademicStructure]
    queryset = Program.objects.all()

    def perform_update(self, serializer):
        """Update program with logging"""
        instance = serializer.save()
        logger.info(f"Program updated: {instance.name} by {self.request.user.registration_number}")

    def perform_destroy(self, instance):
        """Delete program with logging"""
        logger.info(f"Program deleted: {instance.name} by {self.request.user.registration_number}")
        instance.delete()


# ============================================
# Class Level Views
# ============================================

class ClassLevelListView(generics.ListCreateAPIView):
    """
    List and create class levels
    GET /api/academic/class-levels/ - List all class levels
    POST /api/academic/class-levels/ - Create new class level
    Permissions: Academic administrators only
    """
    serializer_class = ClassLevelSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAcademicStructure]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['program', 'level', 'is_promotion_level', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['order', 'name', 'level']
    ordering = ['program__program_type', 'order']

    def get_queryset(self):
        return ClassLevel.objects.select_related('program').all()

    def perform_create(self, serializer):
        """Create class level with logged user"""
        serializer.save()
        logger.info(f"Class level created: {serializer.instance.name} by {self.request.user.registration_number}")


class ClassLevelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete class level
    GET /api/academic/class-levels/{id}/ - Get level details
    PUT/PATCH /api/academic/class-levels/{id}/ - Update level
    DELETE /api/academic/class-levels/{id}/ - Delete level
    Permissions: Academic administrators only
    """
    serializer_class = ClassLevelSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAcademicStructure]
    queryset = ClassLevel.objects.select_related('program')

    def perform_update(self, serializer):
        """Update class level with logging"""
        instance = serializer.save()
        logger.info(f"Class level updated: {instance.name} by {self.request.user.registration_number}")

    def perform_destroy(self, instance):
        """Delete class level with logging"""
        logger.info(f"Class level deleted: {instance.name} by {self.request.user.registration_number}")
        instance.delete()


# ============================================
# Subject Views
# ============================================

class SubjectListView(generics.ListCreateAPIView):
    """
    List and create subjects
    GET /api/academic/subjects/ - List all subjects
    POST /api/academic/subjects/ - Create new subject
    Permissions: Academic administrators only
    """
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageSubjects]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject_type', 'stream', 'is_compulsory', 'is_examinable', 'is_active']
    search_fields = ['name', 'code', 'short_name', 'description']
    ordering_fields = ['name', 'code', 'subject_type']
    ordering = ['code', 'name']

    def get_queryset(self):
        return Subject.objects.prefetch_related('programs', 'class_levels').all()

    def perform_create(self, serializer):
        """Create subject with logged user"""
        serializer.save(created_by=self.request.user)
        logger.info(f"Subject created: {serializer.instance.name} by {self.request.user.registration_number}")


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete subject
    GET /api/academic/subjects/{id}/ - Get subject details
    PUT/PATCH /api/academic/subjects/{id}/ - Update subject
    DELETE /api/academic/subjects/{id}/ - Delete subject
    Permissions: Academic administrators only
    """
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageSubjects]
    queryset = Subject.objects.prefetch_related('programs', 'class_levels')

    def perform_update(self, serializer):
        """Update subject with logging"""
        instance = serializer.save()
        logger.info(f"Subject updated: {instance.name} by {self.request.user.registration_number}")

    def perform_destroy(self, instance):
        """Delete subject with logging"""
        logger.info(f"Subject deleted: {instance.name} by {self.request.user.registration_number}")
        instance.delete()


# ============================================
# Class Views
# ============================================

class ClassListView(generics.ListCreateAPIView):
    """
    List and create classes
    GET /api/academic/classes/ - List all classes
    POST /api/academic/classes/ - Create new class
    Permissions: Class managers only
    """
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageClasses]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session', 'term', 'class_level', 'status', 'is_active', 'stream']
    search_fields = ['name', 'code', 'room_number', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['class_level__order', 'name']

    def get_queryset(self):
        return Class.objects.select_related(
            'session', 'term', 'class_level', 'class_teacher', 'assistant_class_teacher'
        ).all()

    def perform_create(self, serializer):
        """Create class with logged user"""
        serializer.save(created_by=self.request.user)
        logger.info(f"Class created: {serializer.instance.name} by {self.request.user.registration_number}")


class ClassDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete class
    GET /api/academic/classes/{id}/ - Get class details
    PUT/PATCH /api/academic/classes/{id}/ - Update class
    DELETE /api/academic/classes/{id}/ - Delete class
    Permissions: Class managers only
    """
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageClasses]
    queryset = Class.objects.select_related(
        'session', 'term', 'class_level', 'class_teacher', 'assistant_class_teacher'
    )

    def perform_update(self, serializer):
        """Update class with logging"""
        instance = serializer.save()
        logger.info(f"Class updated: {instance.name} by {self.request.user.registration_number}")

    def perform_destroy(self, instance):
        """Delete class with logging"""
        logger.info(f"Class deleted: {instance.name} by {self.request.user.registration_number}")
        instance.delete()


class ClassDashboardView(generics.RetrieveAPIView):
    """
    Get class dashboard with comprehensive information
    GET /api/academic/classes/{id}/dashboard/
    Permissions: Users with view access to the class
    """
    serializer_class = ClassDashboardSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewClassInformation]
    queryset = Class.objects.select_related(
        'session', 'term', 'class_level', 'class_teacher', 'assistant_class_teacher'
    )

    def get_object(self):
        class_obj = super().get_object()
        # Check if user has permission to view this class
        self.check_object_permissions(self.request, class_obj)
        return class_obj


# ============================================
# Class Subject Assignment Views
# ============================================

class ClassSubjectListView(generics.ListCreateAPIView):
    """
    List and create class-subject assignments
    GET /api/academic/class-subjects/ - List all assignments
    POST /api/academic/class-subjects/ - Create new assignment
    Permissions: Academic administrators only
    """
    serializer_class = ClassSubjectSerializer
    permission_classes = [permissions.IsAuthenticated, CanCreateClassSubjectAssignment]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['class_obj', 'subject', 'teacher', 'is_active', 'is_compulsory']
    search_fields = ['class_obj__name', 'subject__name', 'teacher__first_name', 'teacher__last_name', 'notes']
    ordering_fields = ['class_obj__name', 'subject__name']
    ordering = ['class_obj', 'subject']

    def get_queryset(self):
        return ClassSubject.objects.select_related(
            'class_obj', 'subject', 'teacher', 'co_teacher'
        ).all()

    def perform_create(self, serializer):
        """Create class-subject assignment with logged user"""
        serializer.save(created_by=self.request.user)
        logger.info(
            f"Class-subject assignment created: {serializer.instance.class_obj.name} - "
            f"{serializer.instance.subject.name} by {self.request.user.registration_number}"
        )


class ClassSubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete class-subject assignment
    GET /api/academic/class-subjects/{id}/ - Get assignment details
    PUT/PATCH /api/academic/class-subjects/{id}/ - Update assignment
    DELETE /api/academic/class-subjects/{id}/ - Delete assignment
    Permissions: Academic administrators or assigned teacher
    """
    serializer_class = ClassSubjectSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditOwnClassSubjectAssignment]
    queryset = ClassSubject.objects.select_related(
        'class_obj', 'subject', 'teacher', 'co_teacher'
    )

    def perform_update(self, serializer):
        """Update class-subject assignment with logging"""
        instance = serializer.save()
        logger.info(
            f"Class-subject assignment updated: {instance.class_obj.name} - "
            f"{instance.subject.name} by {self.request.user.registration_number}"
        )

    def perform_destroy(self, instance):
        """Delete class-subject assignment with logging"""
        logger.info(
            f"Class-subject assignment deleted: {instance.class_obj.name} - "
            f"{instance.subject.name} by {self.request.user.registration_number}"
        )
        instance.delete()


class BulkClassSubjectAssignmentView(APIView):
    """
    Create multiple class-subject assignments in bulk
    POST /api/academic/class-subjects/bulk-assign/
    Permissions: Academic administrators only
    """
    permission_classes = [permissions.IsAuthenticated, CanAssignTeachersToSubjects]

    def post(self, request):
        """Create bulk assignments"""
        serializer = BulkClassSubjectAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignments = serializer.validated_data['assignments']
        created = []
        errors = []

        with transaction.atomic():
            for i, assignment_data in enumerate(assignments):
                try:
                    # Get related objects
                    class_obj = Class.objects.get(id=assignment_data['class_id'])
                    subject = Subject.objects.get(id=assignment_data['subject_id'])
                    from users.models import User
                    teacher = User.objects.get(id=assignment_data['teacher_id'])

                    # Check if assignment already exists
                    if ClassSubject.objects.filter(class_obj=class_obj, subject=subject).exists():
                        errors.append({
                            'index': i,
                            'error': f'Assignment already exists for {class_obj.name} - {subject.name}'
                        })
                        continue

                    # Create assignment
                    class_subject = ClassSubject.objects.create(
                        class_obj=class_obj,
                        subject=subject,
                        teacher=teacher,
                        created_by=request.user
                    )

                    created.append(class_subject)

                except Exception as e:
                    errors.append({
                        'index': i,
                        'error': str(e)
                    })

        return Response({
            'created_count': len(created),
            'failed_count': len(errors),
            'assignments': ClassSubjectSerializer(created, many=True).data,
            'errors': errors
        }, status=status.HTTP_201_CREATED)


# ============================================
# Timetable Views
# ============================================

class TimetableViewSet(viewsets.ModelViewSet):
    """
    Timetable management
    GET /api/academic/timetables/ - List all timetables
    POST /api/academic/timetables/ - Create new timetable
    GET /api/academic/timetables/{id}/ - Get timetable details
    PUT/PATCH /api/academic/timetables/{id}/ - Update timetable
    DELETE /api/academic/timetables/{id}/ - Delete timetable
    Permissions: Timetable managers for create/update/delete, view for everyone
    """
    serializer_class = TimetableSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session', 'term', 'scope', 'status', 'is_active', 'is_locked']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-session__start_date', '-term__term', 'name']

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, CanViewTimetable]
        elif self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated, CanManageTimetables]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, CanEditTimetable]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter timetables based on user permissions"""
        user = self.request.user

        # Admin users can see all timetables
        if user.role in ['head', 'principal', 'vice_principal', 'secretary']:
            return Timetable.objects.select_related(
                'session', 'term', 'program', 'class_level', 'class_obj', 'teacher'
            ).all()

        # Teachers can see their own timetables or class timetables they teach
        if user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            # Get timetables where teacher is the target
            teacher_timetables = Timetable.objects.filter(teacher=user)

            # Get class timetables where teacher teaches
            teaching_classes = Class.objects.filter(
                class_subjects__teacher=user,
                class_subjects__is_active=True
            )
            class_timetables = Timetable.objects.filter(
                scope='class',
                class_obj__in=teaching_classes
            )

            return (teacher_timetables | class_timetables).distinct().select_related(
                'session', 'term', 'program', 'class_level', 'class_obj', 'teacher'
            )

        return Timetable.objects.none()

    def perform_create(self, serializer):
        """Create timetable with logged user"""
        serializer.save(created_by=self.request.user)
        logger.info(f"Timetable created: {serializer.instance.name} by {self.request.user.registration_number}")

    def perform_update(self, serializer):
        """Update timetable with logging"""
        instance = serializer.save()
        logger.info(f"Timetable updated: {instance.name} by {self.request.user.registration_number}")

    def perform_destroy(self, instance):
        """Delete timetable with logging"""
        logger.info(f"Timetable deleted: {instance.name} by {self.request.user.registration_number}")
        instance.delete()

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a timetable"""
        timetable = self.get_object()

        if timetable.is_locked:
            return Response({
                'error': 'Timetable is locked and cannot be published'
            }, status=status.HTTP_400_BAD_REQUEST)

        timetable.status = 'published'
        timetable.save()

        return Response({
            'message': 'Timetable published successfully',
            'timetable': TimetableSerializer(timetable).data
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a timetable"""
        timetable = self.get_object()

        if timetable.status != 'published':
            return Response({
                'error': 'Only published timetables can be activated'
            }, status=status.HTTP_400_BAD_REQUEST)

        timetable.is_active = True
        timetable.save()

        return Response({
            'message': 'Timetable activated successfully',
            'timetable': TimetableSerializer(timetable).data
        })


# ============================================
# Timetable Entry Views
# ============================================

class TimetableEntryListView(generics.ListCreateAPIView):
    """
    List and create timetable entries
    GET /api/academic/timetable-entries/ - List all entries
    POST /api/academic/timetable-entries/ - Create new entry
    Permissions: Timetable managers only
    """
    serializer_class = TimetableEntrySerializer
    permission_classes = [permissions.IsAuthenticated, CanEditTimetable]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['timetable', 'day', 'teacher', 'subject', 'class_obj', 'entry_type', 'is_active']
    search_fields = ['subject__name', 'teacher__first_name', 'teacher__last_name', 'room', 'notes']
    ordering_fields = ['day', 'period_number']
    ordering = ['timetable', 'day', 'period_number']

    def get_queryset(self):
        return TimetableEntry.objects.select_related(
            'timetable', 'subject', 'teacher', 'class_obj'
        ).all()

    def perform_create(self, serializer):
        """Create timetable entry with logged user"""
        serializer.save(created_by=self.request.user)
        logger.info(
            f"Timetable entry created for {serializer.instance.timetable.name} "
            f"by {self.request.user.registration_number}"
        )


class TimetableEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete timetable entry
    GET /api/academic/timetable-entries/{id}/ - Get entry details
    PUT/PATCH /api/academic/timetable-entries/{id}/ - Update entry
    DELETE /api/academic/timetable-entries/{id}/ - Delete entry
    Permissions: Timetable managers only
    """
    serializer_class = TimetableEntrySerializer
    permission_classes = [permissions.IsAuthenticated, CanEditTimetable]
    queryset = TimetableEntry.objects.select_related(
        'timetable', 'subject', 'teacher', 'class_obj'
    )

    def perform_update(self, serializer):
        """Update timetable entry with logging"""
        instance = serializer.save()
        logger.info(
            f"Timetable entry updated for {instance.timetable.name} "
            f"by {self.request.user.registration_number}"
        )

    def perform_destroy(self, instance):
        """Delete timetable entry with logging"""
        logger.info(
            f"Timetable entry deleted for {instance.timetable.name} "
            f"by {self.request.user.registration_number}"
        )
        instance.delete()


# ============================================
# Student Enrollment Views
# ============================================

class StudentEnrollmentListView(generics.ListCreateAPIView):
    """
    List and create student enrollments
    GET /api/academic/enrollments/ - List all enrollments
    POST /api/academic/enrollments/ - Create new enrollment
    Permissions: Enrollment managers only
    """
    serializer_class = StudentEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageStudentEnrollment]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session', 'term', 'class_obj', 'status', 'is_repeating']
    search_fields = [
        'student__first_name', 'student__last_name',
        'student__registration_number', 'enrollment_number', 'remarks'
    ]
    ordering_fields = ['enrollment_date', 'student__first_name', 'class_obj__name']
    ordering = ['-enrollment_date', 'student__first_name']

    def get_queryset(self):
        return StudentEnrollment.objects.select_related(
            'student', 'class_obj', 'session', 'term', 'enrolled_by', 'approved_by'
        ).all()

    def perform_create(self, serializer):
        """Create enrollment with logged user"""
        serializer.save(enrolled_by=self.request.user)
        logger.info(
            f"Student enrollment created for {serializer.instance.student.get_full_name()} "
            f"in {serializer.instance.class_obj.name} by {self.request.user.registration_number}"
        )


class StudentEnrollmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete student enrollment
    GET /api/academic/enrollments/{id}/ - Get enrollment details
    PUT/PATCH /api/academic/enrollments/{id}/ - Update enrollment
    DELETE /api/academic/enrollments/{id}/ - Delete enrollment
    Permissions: Enrollment managers or related users
    """
    serializer_class = StudentEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewStudentEnrollment]
    queryset = StudentEnrollment.objects.select_related(
        'student', 'class_obj', 'session', 'term', 'enrolled_by', 'approved_by'
    )

    def perform_update(self, serializer):
        """Update enrollment with logging"""
        instance = serializer.save()
        logger.info(
            f"Student enrollment updated for {instance.student.get_full_name()} "
            f"by {self.request.user.registration_number}"
        )

    def perform_destroy(self, instance):
        """Delete enrollment with logging"""
        logger.info(
            f"Student enrollment deleted for {instance.student.get_full_name()} "
            f"by {self.request.user.registration_number}"
        )
        instance.delete()


class ApproveEnrollmentView(APIView):
    """
    Approve student enrollment
    POST /api/academic/enrollments/{id}/approve/
    Permissions: Academic administrators or class teachers
    """
    permission_classes = [permissions.IsAuthenticated, CanManageStudentEnrollment]

    def post(self, request, pk):
        """Approve enrollment"""
        enrollment = get_object_or_404(StudentEnrollment, pk=pk)

        # Check if user can approve this enrollment
        if not self._can_approve_enrollment(request.user, enrollment):
            return Response({
                'error': 'You do not have permission to approve this enrollment'
            }, status=status.HTTP_403_FORBIDDEN)

        if enrollment.status == 'active':
            return Response({
                'error': 'Enrollment is already active'
            }, status=status.HTTP_400_BAD_REQUEST)

        from django.utils import timezone
        enrollment.status = 'active'
        enrollment.approved_by = request.user
        enrollment.approved_date = timezone.now()
        enrollment.save()

        logger.info(
            f"Enrollment approved for {enrollment.student.get_full_name()} "
            f"by {request.user.registration_number}"
        )

        return Response({
            'message': 'Enrollment approved successfully',
            'enrollment': StudentEnrollmentSerializer(enrollment).data
        })

    def _can_approve_enrollment(self, user, enrollment):
        """Check if user can approve enrollment"""
        # Admin users can approve all enrollments
        if user.role in ['head', 'principal', 'vice_principal', 'secretary', 'accountant']:
            return True

        # Class teachers can approve enrollments in their classes
        if user.role in ['teacher', 'form_teacher']:
            if enrollment.class_obj.class_teacher == user:
                return True
            if enrollment.class_obj.assistant_class_teacher == user:
                return True

        return False


# ============================================
# Teacher Views
# ============================================

class TeacherTimetableView(APIView):
    """
    Get teacher's timetable and teaching information
    GET /api/academic/teachers/{id}/timetable/
    Permissions: Teacher can view own, admin can view any
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        """Get teacher timetable"""
        from users.models import User

        # If no pk specified, get current user's timetable
        if pk is None:
            user = request.user
        else:
            user = get_object_or_404(User, pk=pk)

        # Check permissions
        if user != request.user and request.user.role not in ['head', 'principal', 'vice_principal', 'secretary']:
            return Response({
                'error': 'You do not have permission to view this teacher\'s timetable'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if user is a teacher
        if user.role not in ['teacher', 'form_teacher', 'subject_teacher', 'head', 'principal', 'vice_principal']:
            return Response({
                'error': 'User is not a teacher'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get teacher's active timetable
        timetable = Timetable.objects.filter(
            teacher=user,
            is_active=True
        ).first()

        data = {
            'teacher': user,
            'timetable': timetable
        }

        serializer = TeacherTimetableSerializer(data)
        return Response(serializer.data)


class TeacherAssignmentsView(APIView):
    """
    Get teacher's class and subject assignments
    GET /api/academic/teachers/{id}/assignments/
    Permissions: Teacher can view own, admin can view any
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        """Get teacher assignments"""
        from users.models import User

        # If no pk specified, get current user's assignments
        if pk is None:
            user = request.user
        else:
            user = get_object_or_404(User, pk=pk)

        # Check permissions
        if user != request.user and request.user.role not in ['head', 'principal', 'vice_principal', 'secretary']:
            return Response({
                'error': 'You do not have permission to view this teacher\'s assignments'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get class teacher assignments
        class_teacher_classes = Class.objects.filter(
            class_teacher=user,
            is_active=True
        )

        # Get subject teaching assignments
        teaching_assignments = ClassSubject.objects.filter(
            teacher=user,
            is_active=True
        ).select_related('class_obj', 'subject')

        # Get co-teaching assignments
        co_teaching_assignments = ClassSubject.objects.filter(
            co_teacher=user,
            is_active=True
        ).select_related('class_obj', 'subject')

        return Response({
            'teacher': {
                'id': user.id,
                'name': user.get_full_name(),
                'registration_number': user.registration_number,
                'role': user.get_role_display(),
            },
            'class_teacher_classes': ClassSerializer(class_teacher_classes, many=True).data,
            'teaching_assignments': ClassSubjectSerializer(teaching_assignments, many=True).data,
            'co_teaching_assignments': ClassSubjectSerializer(co_teaching_assignments, many=True).data,
            'statistics': {
                'total_classes': class_teacher_classes.count(),
                'total_subjects_taught': teaching_assignments.values('subject').distinct().count(),
                'total_periods_per_week': sum(a.periods_per_week for a in teaching_assignments),
            }
        })


# ============================================
# Dashboard and Reporting Views
# ============================================

class AcademicDashboardView(APIView):
    """
    Academic dashboard with overview statistics
    GET /api/academic/dashboard/
    Permissions: Academic administrators only
    """
    permission_classes = [permissions.IsAuthenticated, IsAcademicAdmin]

    def get(self, request):
        """Get academic dashboard data"""
        # Current academic session and term
        current_session = AcademicSession.objects.filter(is_current=True).first()
        current_term = AcademicTerm.objects.filter(is_current=True).first()

        # Statistics
        total_classes = Class.objects.filter(is_active=True).count()
        total_students_enrolled = StudentEnrollment.objects.filter(status='active').count()
        total_subjects = Subject.objects.filter(is_active=True).count()
        from users.models import User
        total_teachers = User.objects.filter(
            role__in=['teacher', 'form_teacher', 'subject_teacher', 'head', 'principal', 'vice_principal']
        ).count()

        # Recent activities
        recent_classes = Class.objects.filter(is_active=True).order_by('-created_at')[:5]
        recent_enrollments = StudentEnrollment.objects.filter(status='active').order_by('-enrollment_date')[:5]

        # Class capacity statistics
        classes_with_capacity = Class.objects.filter(is_active=True)
        total_capacity = sum(c.max_capacity for c in classes_with_capacity)
        total_enrolled = sum(c.current_enrollment for c in classes_with_capacity)
        capacity_utilization = (total_enrolled / total_capacity * 100) if total_capacity > 0 else 0

        data = {
            'current_session': AcademicSessionSerializer(current_session).data if current_session else None,
            'current_term': AcademicTermSerializer(current_term).data if current_term else None,
            'statistics': {
                'total_classes': total_classes,
                'total_students': total_students_enrolled,
                'total_subjects': total_subjects,
                'total_teachers': total_teachers,
                'total_capacity': total_capacity,
                'total_enrolled': total_enrolled,
                'capacity_utilization': round(capacity_utilization, 2),
                'available_seats': total_capacity - total_enrolled,
            },
            'recent_classes': ClassSerializer(recent_classes, many=True).data,
            'recent_enrollments': StudentEnrollmentSerializer(recent_enrollments, many=True).data,
        }

        serializer = AcademicDashboardSerializer(data)
        return Response(serializer.data)


class ClassStatisticsView(APIView):
    """
    Get class-level statistics
    GET /api/academic/statistics/classes/
    Permissions: Academic administrators only
    """
    permission_classes = [permissions.IsAuthenticated, IsAcademicAdmin]

    def get(self, request):
        """Get class statistics"""
        # Class level statistics
        class_level_stats = []
        for class_level in ClassLevel.objects.filter(is_active=True):
            classes = Class.objects.filter(class_level=class_level, is_active=True)
            total_classes = classes.count()
            total_students = sum(c.current_enrollment for c in classes)
            total_capacity = sum(c.max_capacity for c in classes)

            class_level_stats.append({
                'class_level': ClassLevelSerializer(class_level).data,
                'total_classes': total_classes,
                'total_students': total_students,
                'total_capacity': total_capacity,
                'utilization_rate': (total_students / total_capacity * 100) if total_capacity > 0 else 0,
                'available_seats': total_capacity - total_students,
            })

        # Program statistics
        program_stats = []
        for program in Program.objects.filter(is_active=True):
            classes = Class.objects.filter(class_level__program=program, is_active=True)
            total_classes = classes.count()
            total_students = sum(c.current_enrollment for c in classes)

            program_stats.append({
                'program': ProgramSerializer(program).data,
                'total_classes': total_classes,
                'total_students': total_students,
                'class_levels_count': program.class_levels.filter(is_active=True).count(),
                'subjects_count': program.subjects.filter(is_active=True).count(),
            })

        data = {
            'class_level_statistics': class_level_stats,
            'program_statistics': program_stats,
        }

        serializer = ClassStatisticsSerializer(data)
        return Response(serializer.data)


# ============================================
# Public Views (for students and parents)
# ============================================

class PublicClassTimetableView(APIView):
    """
    Get class timetable for public viewing
    GET /api/academic/public/classes/{id}/timetable/
    Permissions: Authenticated users (students, parents, teachers)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Get class timetable"""
        class_obj = get_object_or_404(Class, pk=pk, is_active=True)

        # Get active timetable for this class
        timetable = Timetable.objects.filter(
            class_obj=class_obj,
            is_active=True
        ).first()

        if not timetable:
            return Response({
                'error': 'No active timetable found for this class'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get timetable entries
        entries = TimetableEntry.objects.filter(
            timetable=timetable,
            is_active=True
        ).order_by('day', 'period_number')

        # Organize by day
        timetable_data = {
            'class': ClassSerializer(class_obj).data,
            'timetable': TimetableSerializer(timetable).data,
            'schedule': {}
        }

        for entry in entries:
            day = entry.day
            if day not in timetable_data['schedule']:
                timetable_data['schedule'][day] = []

            # Get period time from timetable
            schedule = timetable.generate_period_schedule()
            period_time = next((p for p in schedule if p['period'] == entry.period_number), None)

            timetable_data['schedule'][day].append({
                'period': entry.period_number,
                'start_time': period_time['start_time'] if period_time else None,
                'end_time': period_time['end_time'] if period_time else None,
                'subject': entry.subject.name if entry.subject else entry.get_entry_type_display(),
                'teacher': entry.teacher.get_full_name() if entry.teacher else 'N/A',
                'room': entry.room,
                'entry_type': entry.get_entry_type_display(),
            })

        # Sort by period number
        for day in timetable_data['schedule']:
            timetable_data['schedule'][day].sort(key=lambda x: x['period'])

        return Response(timetable_data)


class PublicTeacherTimetableView(APIView):
    """
    Get teacher's public timetable
    GET /api/academic/public/teachers/{id}/timetable/
    Permissions: Authenticated users
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Get teacher timetable"""
        from users.models import User
        teacher = get_object_or_404(User, pk=pk)

        # Check if user is a teacher
        if teacher.role not in ['teacher', 'form_teacher', 'subject_teacher', 'head', 'principal', 'vice_principal']:
            return Response({
                'error': 'User is not a teacher'
            }, status=status.HTTP_400_BAD_REQUEST)

        timetable = Timetable.objects.filter(
            teacher=teacher,
            is_active=True
        ).first()

        if not timetable:
            return Response({
                'error': 'No active timetable found for this teacher'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get timetable entries
        entries = TimetableEntry.objects.filter(
            timetable=timetable,
            is_active=True,
            entry_type='subject'
        ).order_by('day', 'period_number')

        # Organize by day
        timetable_data = {
            'teacher': {
                'id': teacher.id,
                'name': teacher.get_full_name(),
                'registration_number': teacher.registration_number,
            },
            'timetable': TimetableSerializer(timetable).data,
            'schedule': {}
        }

        for entry in entries:
            day = entry.day
            if day not in timetable_data['schedule']:
                timetable_data['schedule'][day] = []

            # Get period time from timetable
            schedule = timetable.generate_period_schedule()
            period_time = next((p for p in schedule if p['period'] == entry.period_number), None)

            timetable_data['schedule'][day].append({
                'period': entry.period_number,
                'start_time': period_time['start_time'] if period_time else None,
                'end_time': period_time['end_time'] if period_time else None,
                'subject': entry.subject.name if entry.subject else 'N/A',
                'class': entry.class_obj.name if entry.class_obj else 'N/A',
                'room': entry.room,
            })

        # Sort by period number
        for day in timetable_data['schedule']:
            timetable_data['schedule'][day].sort(key=lambda x: x['period'])

        return Response(timetable_data)