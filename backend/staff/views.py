from rest_framework import generics, permissions, status, filters, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.utils import timezone
import logging

from .models import Parent
from .serializers import (
    ParentSerializer, ParentCreateSerializer, ParentListSerializer,
    ParentDetailSerializer, ParentDashboardSerializer, ParentChildrenSerializer,
    LinkChildToParentSerializer, UpdateParentSerializer, ParentPTASerializer,
    BulkParentCreateSerializer, ParentFeeSummarySerializer, ParentNotificationSerializer
)
from .permissions import (
    IsParent, CanEditParent, CanViewParentInfo, CanAddParent,
    CanViewChildrenInfo, CanManagePTA, CanViewFeeInformation,
    CanCommunicateWithParents, IsParentOfStudent
)
from users.models import User

logger = logging.getLogger(__name__)


class ParentListView(generics.ListAPIView):
    """
    List all parents with filtering and search

    GET /api/parents/

    Filters: parent_type, marital_status, is_pta_member, is_active
    Search: name, email, parent_id, occupation
    Ordering: name, parent_type, created_at

    Permissions: Admin/Principal/Teachers/Accountant/Secretary
    """

    serializer_class = ParentListSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewParentInfo]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['parent_type', 'marital_status', 'is_pta_member', 'is_active', 'is_verified']
    search_fields = [
        'user__first_name', 'user__last_name',
        'user__email', 'parent_id', 'occupation',
        'user__phone_number', 'user__registration_number'
    ]
    ordering_fields = ['user__first_name', 'parent_type', 'created_at', 'marital_status']
    ordering = ['user__first_name']

    def get_queryset(self):
        """Filter parents based on user permissions"""
        user = self.request.user

        # Admin/Principal can see all parents
        if user.role in ['head', 'principal', 'vice_principal'] or user.is_staff:
            return Parent.objects.select_related('user', 'spouse').all()

        # Accountant/Secretary can see all parents
        if user.role in ['accountant', 'secretary']:
            return Parent.objects.select_related('user', 'spouse').all()

        # Teachers can see parents of students in their classes
        if user.role in ['teacher', 'form_teacher', 'subject_teacher']:
            # Get students in teacher's classes
            from staff.models import TeacherProfile
            from students.models import Student

            try:
                teacher_profile = user.staff_profile.teacher_profile
                # Get classes where teacher is class teacher
                assigned_classes = teacher_profile.assigned_classes.all()

                # Get students in those classes
                student_ids = []
                for class_obj in assigned_classes:
                    # This would need enrollment model in real implementation
                    # For now, we'll use a simplified approach
                    pass

                # Get parents of those students
                parents = Parent.objects.filter(
                    Q(father_of_students__class_level__in=assigned_classes.values('class_level')) |
                    Q(mother_of_students__class_level__in=assigned_classes.values('class_level'))
                ).distinct()

                return parents.select_related('user', 'spouse')

            except (TeacherProfile.DoesNotExist, AttributeError):
                return Parent.objects.none()

        # Parents can only see themselves
        if user.role == 'parent':
            try:
                return Parent.objects.filter(user=user).select_related('user', 'spouse')
            except Parent.DoesNotExist:
                return Parent.objects.none()

        return Parent.objects.none()


class ParentCreateView(generics.CreateAPIView):
    """
    Create new parent profile

    POST /api/parents/create/

    Required: user_id, parent_type
    Optional: occupation, marital_status, preferred_communication

    Permissions: Admin/Principal/Secretary/Teachers
    """

    serializer_class = ParentCreateSerializer
    permission_classes = [permissions.IsAuthenticated, CanAddParent]

    def create(self, request, *args, **kwargs):
        """Create parent with transaction"""
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            parent = serializer.save()

            logger.info(
                f"Parent created: {parent.parent_id} ({parent.parent_type}) "
                f"by {request.user.registration_number}"
            )

            return Response({
                'message': 'Parent created successfully',
                'parent': ParentSerializer(parent).data
            }, status=status.HTTP_201_CREATED)


class ParentDetailView(generics.RetrieveAPIView):
    """
    Get parent details

    GET /api/parents/{id}/

    Permissions: Parent can view own, admin can view any
    """

    serializer_class = ParentDetailSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditParent]
    queryset = Parent.objects.select_related('user', 'spouse')

    def get_object(self):
        """Get parent with permission checks"""
        # If user is parent, return their own profile
        if self.request.user.role == 'parent':
            try:
                return self.request.user.parent_profile
            except Parent.DoesNotExist:
                pass

        # Otherwise use the normal lookup
        parent = super().get_object()

        # Check object-level permissions
        self.check_object_permissions(self.request, parent)

        return parent


class ParentUpdateView(generics.UpdateAPIView):
    """
    Update parent profile

    PUT/PATCH /api/parents/{id}/update/

    Permissions: Parent can update own (limited), admin can update any
    """

    serializer_class = UpdateParentSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditParent]
    queryset = Parent.objects.select_related('user')

    def update(self, request, *args, **kwargs):
        """Update parent with permission checks"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check object-level permissions
        self.check_object_permissions(request, instance)

        # Parents cannot edit restricted fields on their own profile
        if request.user.role == 'parent' and instance.user == request.user:
            restricted_fields = ['parent_id', 'is_verified', 'user', 'parent_type',
                                 'annual_income_range', 'is_pta_member', 'pta_position',
                                 'spouse', 'marital_status']

            for field in request.data:
                if field in restricted_fields:
                    return Response({
                        'error': f'You cannot modify the {field} field'
                    }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        logger.info(f"Parent updated: {instance.parent_id} by {request.user.registration_number}")

        return Response({
            'message': 'Parent updated successfully',
            'parent': ParentSerializer(instance).data
        })


class ParentDashboardView(APIView):
    """
    Parent dashboard with children and fee summary

    GET /api/parents/dashboard/

    Permissions: Parents only
    """

    permission_classes = [permissions.IsAuthenticated, IsParent]

    def get(self, request):
        """Get parent dashboard data"""
        try:
            parent = request.user.parent_profile
        except Parent.DoesNotExist:
            return Response({
                'error': 'Parent profile not found. Please contact administrator.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ParentDashboardSerializer(parent)

        # Get additional dashboard data
        dashboard_data = serializer.data
        dashboard_data.update({
            'quick_stats': self._get_quick_stats(parent),
            'recent_notifications': self._get_recent_notifications(parent),
            'upcoming_events': self._get_upcoming_events(parent)
        })

        return Response({
            'dashboard': dashboard_data
        })

    def _get_quick_stats(self, parent):
        """Get quick statistics for dashboard"""
        children = parent.get_children()
        active_children = children.filter(is_active=True)

        return {
            'total_children': children.count(),
            'active_children': active_children.count(),
            'graduated_children': children.filter(is_graduated=True).count(),
            'pta_member': parent.is_pta_member,
            'fee_summary': parent.get_fee_summary(),
            'children_by_level': self._get_children_by_level(children)
        }

    def _get_children_by_level(self, children):
        """Get children distribution by class level"""
        from collections import defaultdict

        levels = defaultdict(int)
        for child in children:
            if child.class_level:
                levels[child.class_level.name] += 1

        return dict(levels)

    def _get_recent_notifications(self, parent):
        """Get recent notifications for parent"""
        # This would fetch from notifications app in real implementation
        return [
            {
                'date': timezone.now().date(),
                'title': 'Fee Payment Reminder',
                'message': 'Please complete fee payment for current term',
                'type': 'financial'
            },
            {
                'date': timezone.now().date() - timezone.timedelta(days=1),
                'title': 'PTA Meeting',
                'message': 'Monthly PTA meeting scheduled for next week',
                'type': 'pta'
            }
        ]

    def _get_upcoming_events(self, parent):
        """Get upcoming events for parent's children"""
        # This would fetch from academic calendar in real implementation
        return [
            {
                'date': timezone.now().date() + timezone.timedelta(days=7),
                'title': 'Mid-term Break',
                'description': 'School resumes on following Monday',
                'type': 'holiday'
            },
            {
                'date': timezone.now().date() + timezone.timedelta(days=14),
                'title': 'Examination Week',
                'description': 'End of term examinations',
                'type': 'academic'
            }
        ]


class ParentChildrenView(generics.ListAPIView):
    """
    Get all children of logged-in parent

    GET /api/parents/children/

    Permissions: Parents only
    """

    serializer_class = ParentChildrenSerializer
    permission_classes = [permissions.IsAuthenticated, IsParent]

    def get_queryset(self):
        """Get parent's children"""
        try:
            parent = self.request.user.parent_profile
            children = parent.get_children().select_related(
                'user', 'class_level', 'father', 'mother'
            )

            # Apply filters if provided
            class_level = self.request.query_params.get('class_level')
            is_active = self.request.query_params.get('is_active')
            is_graduated = self.request.query_params.get('is_graduated')

            if class_level:
                children = children.filter(class_level_id=class_level)

            if is_active:
                children = children.filter(is_active=(is_active.lower() == 'true'))

            if is_graduated:
                children = children.filter(is_graduated=(is_graduated.lower() == 'true'))

            return children.order_by('class_level__order', 'user__first_name')

        except Parent.DoesNotExist:
            return Parent.objects.none()


class LinkChildToParentView(APIView):
    """
    Link existing student to parent

    POST /api/parents/link-child/

    Required: student_admission_number, parent_id, relationship_type

    Permissions: Admin/Principal/Secretary/Teachers
    """

    permission_classes = [permissions.IsAuthenticated, CanAddParent]

    def post(self, request):
        """Link student to parent"""
        serializer = LinkChildToParentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = serializer.validated_data['student']
        parent = serializer.validated_data['parent']
        relationship = serializer.validated_data['relationship_type']

        # Check if student is already linked to this parent
        existing_link = False
        if relationship == 'father' and student.father == parent:
            existing_link = True
        elif relationship == 'mother' and student.mother == parent:
            existing_link = True

        if existing_link:
            return Response({
                'error': f'Student is already linked as {relationship} to this parent'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Link student to parent
        if relationship == 'father':
            student.father = parent
        else:
            student.mother = parent

        student.save()

        logger.info(
            f"Linked student {student.admission_number} to parent {parent.parent_id} as {relationship} "
            f"by {request.user.registration_number}"
        )

        return Response({
            'message': f'Successfully linked student to parent as {relationship}',
            'student': {
                'id': student.id,
                'name': student.user.get_full_name(),
                'admission_number': student.admission_number,
                'class_level': student.class_level.name if student.class_level else None
            },
            'parent': ParentSerializer(parent).data,
            'relationship': relationship
        })


class UnlinkChildFromParentView(APIView):
    """
    Unlink student from parent

    POST /api/parents/unlink-child/

    Required: student_admission_number, parent_id

    Permissions: Admin/Principal only
    """

    permission_classes = [permissions.IsAuthenticated, CanAddParent]

    def post(self, request):
        """Unlink student from parent"""
        student_admission = request.data.get('student_admission_number')
        parent_id = request.data.get('parent_id')

        if not all([student_admission, parent_id]):
            return Response({
                'error': 'Missing required fields: student_admission_number, parent_id'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get student and parent
        from students.models import Student
        try:
            student = Student.objects.get(admission_number=student_admission)
        except Student.DoesNotExist:
            return Response({
                'error': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            parent = Parent.objects.get(parent_id=parent_id)
        except Parent.DoesNotExist:
            return Response({
                'error': 'Parent not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Unlink student from parent
        unlinked = False
        if student.father == parent:
            student.father = None
            unlinked = True
            relationship = 'father'
        elif student.mother == parent:
            student.mother = None
            unlinked = True
            relationship = 'mother'

        if not unlinked:
            return Response({
                'error': 'Student is not linked to this parent'
            }, status=status.HTTP_400_BAD_REQUEST)

        student.save()

        logger.info(
            f"Unlinked student {student.admission_number} from parent {parent.parent_id} "
            f"by {request.user.registration_number}"
        )

        return Response({
            'message': f'Successfully unlinked student from {relationship}',
            'student': {
                'id': student.id,
                'name': student.user.get_full_name(),
                'admission_number': student.admission_number
            },
            'parent': ParentSerializer(parent).data
        })


class UpdatePTAStatusView(APIView):
    """
    Update parent's PTA membership status

    POST /api/parents/{id}/update-pta/

    Required: is_pta_member
    Optional: pta_position, pta_committee

    Permissions: Admin/Principal only
    """

    permission_classes = [permissions.IsAuthenticated, CanManagePTA]

    def post(self, request, pk):
        """Update PTA status"""
        parent = get_object_or_404(Parent, pk=pk)

        serializer = ParentPTASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_pta_status = parent.is_pta_member
        parent.is_pta_member = serializer.validated_data['is_pta_member']
        parent.pta_position = serializer.validated_data.get('pta_position', '')
        parent.pta_committee = serializer.validated_data.get('pta_committee', '')
        parent.save()

        # Send notification if PTA status changed
        if old_pta_status != parent.is_pta_member:
            status = "added to" if parent.is_pta_member else "removed from"
            logger.info(
                f"Parent {parent.parent_id} {status} PTA "
                f"by {request.user.registration_number}"
            )

            # Send email notification
            self._send_pta_notification(parent, parent.is_pta_member)

        return Response({
            'message': f'PTA status updated successfully',
            'pta_status': {
                'is_pta_member': parent.is_pta_member,
                'pta_position': parent.pta_position,
                'pta_committee': parent.pta_committee
            },
            'parent': ParentSerializer(parent).data
        })

    def _send_pta_notification(self, parent, is_member):
        """Send PTA membership notification"""
        if parent.user.email:
            try:
                from django.core.mail import send_mail
                from django.conf import settings

                if is_member:
                    subject = f"PTA Membership - {settings.SCHOOL_NAME or 'Our School'}"
                    message = f"""
                    Dear {parent.user.get_full_name()},

                    You have been added as a PTA member of {settings.SCHOOL_NAME or 'Our School'}.

                    PTA Details:
                    - Position: {parent.pta_position or 'Member'}
                    - Committee: {parent.pta_committee or 'General'}

                    Thank you for your commitment to supporting our school community.

                    Best regards,
                    School Administration
                    """
                else:
                    subject = f"PTA Membership Update - {settings.SCHOOL_NAME or 'Our School'}"
                    message = f"""
                    Dear {parent.user.get_full_name()},

                    Your PTA membership status has been updated.

                    You are no longer listed as a PTA member. Thank you for your previous service.

                    Best regards,
                    School Administration
                    """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [parent.user.email],
                    fail_silently=True,
                )
                logger.info(f"PTA notification sent to {parent.user.email}")

            except Exception as e:
                logger.error(f"Failed to send PTA notification: {str(e)}")


class ParentFeeSummaryView(APIView):
    """
    Get fee summary for parent's children

    GET /api/parents/fee-summary/

    Permissions: Parent can view own, admin/accountant can view any
    """

    permission_classes = [permissions.IsAuthenticated, CanViewFeeInformation]

    def get(self, request, pk=None):
        """Get parent fee summary"""
        if pk is None and request.user.role == 'parent':
            # Parent viewing own fee summary
            try:
                parent = request.user.parent_profile
            except Parent.DoesNotExist:
                return Response({
                    'error': 'Parent profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Viewing specific parent fee summary
            parent = get_object_or_404(Parent, pk=pk)

            # Check permissions
            if not self._can_view_fee_info(request.user, parent):
                return Response({
                    'error': 'You do not have permission to view fee information for this parent'
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = ParentFeeSummarySerializer(parent)

        return Response({
            'fee_summary': serializer.data,
            'detailed_breakdown': self._get_detailed_breakdown(parent)
        })

    def _can_view_fee_info(self, user, parent):
        """Check if user can view fee information for parent"""
        # Admin/Accountant can view all
        if user.role in ['head', 'principal', 'vice_principal', 'accountant'] or user.is_staff:
            return True

        # Parent can view own
        if user.role == 'parent' and user.parent_profile == parent:
            return True

        return False

    def _get_detailed_breakdown(self, parent):
        """Get detailed fee breakdown by child"""
        children = parent.get_children()
        breakdown = []

        for child in children:
            breakdown.append({
                'student': {
                    'id': child.id,
                    'name': child.user.get_full_name(),
                    'admission_number': child.admission_number,
                    'class_level': child.class_level.name if child.class_level else None
                },
                'fee_details': child.get_fee_summary(),
                'last_payment_date': child.last_payment_date,
                'payment_evidence': bool(child.fee_payment_evidence)
            })

        return breakdown


class BulkParentCreateView(APIView):
    """
    Create multiple parents in bulk

    POST /api/parents/bulk-create/

    Permissions: Admin/Principal/Secretary only
    """

    permission_classes = [permissions.IsAuthenticated, CanAddParent]

    def post(self, request):
        """Create multiple parents from bulk data"""
        serializer = BulkParentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parents_data = serializer.validated_data['parents']
        created = []
        errors = []

        with transaction.atomic():
            for i, parent_data in enumerate(parents_data):
                try:
                    # Create user first
                    user_data = parent_data.pop('user')

                    # Check if user already exists
                    if User.objects.filter(email=user_data['email']).exists():
                        errors.append({
                            'index': i,
                            'error': f'User with email {user_data["email"]} already exists'
                        })
                        continue

                    # Create user
                    user = User.objects.create_user(**user_data)

                    # Create parent
                    parent = Parent.objects.create(user=user, **parent_data)
                    created.append(parent)

                except Exception as e:
                    errors.append({
                        'index': i,
                        'error': str(e)
                    })

        return Response({
            'created_count': len(created),
            'failed_count': len(errors),
            'parents': ParentListSerializer(created, many=True).data,
            'errors': errors
        }, status=status.HTTP_201_CREATED)


class SendParentNotificationView(APIView):
    """
    Send notification to parent(s)

    POST /api/parents/send-notification/

    Required: message, notification_type
    Optional: parent_ids (if empty, sends to all parents), student_ids

    Permissions: Admin/Principal/Teachers/Secretary
    """

    permission_classes = [permissions.IsAuthenticated, CanCommunicateWithParents]

    def post(self, request):
        """Send notification to parents"""
        serializer = ParentNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data['message']
        notification_type = serializer.validated_data['notification_type']
        parent_ids = serializer.validated_data.get('parent_ids', [])
        student_ids = serializer.validated_data.get('student_ids', [])

        # Determine which parents to notify
        parents_to_notify = self._get_parents_to_notify(parent_ids, student_ids)

        if not parents_to_notify:
            return Response({
                'error': 'No parents found to notify'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Send notifications
        sent_count = 0
        failed_count = 0

        for parent in parents_to_notify:
            try:
                self._send_notification(parent, message, notification_type)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send notification to parent {parent.parent_id}: {str(e)}")
                failed_count += 1

        logger.info(
            f"Notification sent to {sent_count} parents by {request.user.registration_number}"
        )

        return Response({
            'message': f'Notification sent to {sent_count} parents',
            'summary': {
                'total_parents': len(parents_to_notify),
                'sent_count': sent_count,
                'failed_count': failed_count,
                'notification_type': notification_type
            }
        })

    def _get_parents_to_notify(self, parent_ids, student_ids):
        """Get list of parents to notify"""
        if parent_ids:
            # Notify specific parents
            return Parent.objects.filter(parent_id__in=parent_ids)
        elif student_ids:
            # Notify parents of specific students
            from students.models import Student
            students = Student.objects.filter(admission_number__in=student_ids)

            parent_ids = set()
            for student in students:
                if student.father:
                    parent_ids.add(student.father.parent_id)
                if student.mother:
                    parent_ids.add(student.mother.parent_id)

            return Parent.objects.filter(parent_id__in=parent_ids)
        else:
            # Notify all parents
            return Parent.objects.filter(is_active=True)

    def _send_notification(self, parent, message, notification_type):
        """Send notification to parent"""
        # In production, this would:
        # 1. Send email
        # 2. Send SMS (if enabled)
        # 3. Send push notification
        # 4. Store in database

        # For now, just log it
        logger.info(
            f"Notification [{notification_type}] sent to parent {parent.parent_id}: {message[:50]}..."
        )

        # Send email if parent has email
        if parent.user.email:
            try:
                from django.core.mail import send_mail
                from django.conf import settings

                subject = f"School Notification: {notification_type.title()}"
                full_message = f"""
                Dear {parent.user.get_full_name()},

                {message}

                Best regards,
                {settings.SCHOOL_NAME or 'School'} Administration
                """

                send_mail(
                    subject,
                    full_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [parent.user.email],
                    fail_silently=True,
                )

            except Exception as e:
                logger.error(f"Failed to send email to {parent.user.email}: {str(e)}")


class ParentStatisticsView(APIView):
    """
    Get parent statistics for dashboard

    GET /api/parents/statistics/

    Permissions: Admin/Principal/Accountant
    """

    permission_classes = [permissions.IsAuthenticated, CanViewParentInfo]

    def get(self, request):
        """Get comprehensive parent statistics"""

        # Overall statistics
        total_parents = Parent.objects.count()
        active_parents = Parent.objects.filter(is_active=True).count()
        verified_parents = Parent.objects.filter(is_verified=True).count()
        pta_members = Parent.objects.filter(is_pta_member=True).count()

        # Parent type distribution
        parent_type_distribution = Parent.objects.values(
            'parent_type'
        ).annotate(
            count=Count('id')
        ).order_by('parent_type')

        # Marital status distribution
        marital_status_distribution = Parent.objects.values(
            'marital_status'
        ).annotate(
            count=Count('id')
        ).order_by('marital_status')

        # Communication preference distribution
        communication_distribution = Parent.objects.values(
            'preferred_communication'
        ).annotate(
            count=Count('id')
        ).order_by('preferred_communication')

        # Children per parent distribution
        from django.db.models import Count
        children_distribution = Parent.objects.annotate(
            child_count=Count('father_of_students') + Count('mother_of_students')
        ).values('child_count').annotate(
            parent_count=Count('id')
        ).order_by('child_count')

        # Recent registrations (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_registrations = Parent.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()

        # Fee collection summary from parents
        from students.models import Student
        fee_summary = Parent.objects.aggregate(
            total_children=Count('father_of_students') + Count('mother_of_students'),
        )

        # Get actual fee data from children
        children = Student.objects.filter(
            Q(father__isnull=False) | Q(mother__isnull=False)
        )
        total_fee = children.aggregate(
            total=Sum('total_fee_amount'),
            paid=Sum('amount_paid'),
            balance=Sum('balance_due')
        )

        return Response({
            'overall': {
                'total_parents': total_parents,
                'active_parents': active_parents,
                'verified_parents': verified_parents,
                'pta_members': pta_members,
                'recent_registrations': recent_registrations,
                'inactive_parents': total_parents - active_parents
            },
            'demographics': {
                'parent_type_distribution': list(parent_type_distribution),
                'marital_status_distribution': list(marital_status_distribution),
                'communication_distribution': list(communication_distribution),
                'children_distribution': list(children_distribution)
            },
            'financial': {
                'total_children': fee_summary['total_children'] or 0,
                'total_fee': float(total_fee['total'] or 0),
                'total_paid': float(total_fee['paid'] or 0),
                'total_balance': float(total_fee['balance'] or 0),
                'collection_rate': (float(total_fee['paid'] or 0) /
                                    float(total_fee['total'] or 1) * 100) if total_fee['total'] else 0
            },
            'pta_analysis': {
                'pta_member_percentage': (pta_members / total_parents * 100) if total_parents > 0 else 0,
                'pta_positions': Parent.objects.exclude(pta_position='').values('pta_position').annotate(
                    count=Count('id')
                ).order_by('-count')
            }
        })


class VerifyParentView(APIView):
    """
    Verify a parent (Admin only)

    POST /api/parents/{id}/verify/

    Permissions: Admin/Principal only
    """

    permission_classes = [permissions.IsAuthenticated, CanAddParent]

    def post(self, request, pk):
        """Verify parent"""
        parent = get_object_or_404(Parent, pk=pk)

        if parent.is_verified:
            return Response({
                'error': 'Parent is already verified'
            }, status=status.HTTP_400_BAD_REQUEST)

        parent.is_verified = True
        parent.save()

        logger.info(
            f"Parent {parent.parent_id} verified by {request.user.registration_number}"
        )

        # Send verification email
        self._send_verification_email(parent)

        return Response({
            'message': 'Parent verified successfully',
            'parent': ParentSerializer(parent).data
        })

    def _send_verification_email(self, parent):
        """Send verification email to parent"""
        if parent.user.email:
            try:
                from django.core.mail import send_mail
                from django.conf import settings

                subject = f"Parent Account Verified - {settings.SCHOOL_NAME or 'Our School'}"
                message = f"""
                Dear {parent.user.get_full_name()},

                Your parent account has been verified by the school administration.

                You can now access all parent features including:
                - Viewing your children's academic progress
                - Receiving school notifications
                - Making fee payments online
                - Participating in PTA activities

                Parent ID: {parent.parent_id}

                Best regards,
                School Administration
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [parent.user.email],
                    fail_silently=True,
                )
                logger.info(f"Verification email sent to {parent.user.email}")

            except Exception as e:
                logger.error(f"Failed to send verification email: {str(e)}")


class ParentSearchView(generics.ListAPIView):
    """
    Search parents with advanced filtering

    GET /api/parents/search/

    Permissions: Admin/Principal/Teachers/Accountant/Secretary
    """

    serializer_class = ParentListSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewParentInfo]

    def get_queryset(self):
        """Advanced parent search"""
        queryset = Parent.objects.select_related('user')

        # Get query parameters
        name = self.request.query_params.get('name', '')
        parent_id = self.request.query_params.get('parent_id', '')
        occupation = self.request.query_params.get('occupation', '')
        parent_type = self.request.query_params.get('parent_type', '')
        marital_status = self.request.query_params.get('marital_status', '')
        is_pta_member = self.request.query_params.get('is_pta_member', '')
        is_active = self.request.query_params.get('is_active', '')
        is_verified = self.request.query_params.get('is_verified', '')

        # Apply filters
        if name:
            queryset = queryset.filter(
                Q(user__first_name__icontains=name) |
                Q(user__last_name__icontains=name)
            )

        if parent_id:
            queryset = queryset.filter(parent_id__icontains=parent_id)

        if occupation:
            queryset = queryset.filter(occupation__icontains=occupation)

        if parent_type and parent_type != 'all':
            queryset = queryset.filter(parent_type=parent_type)

        if marital_status and marital_status != 'all':
            queryset = queryset.filter(marital_status=marital_status)

        if is_pta_member:
            queryset = queryset.filter(is_pta_member=(is_pta_member.lower() == 'true'))

        if is_active:
            queryset = queryset.filter(is_active=(is_active.lower() == 'true'))

        if is_verified:
            queryset = queryset.filter(is_verified=(is_verified.lower() == 'true'))

        # Apply permission-based filtering
        user = self.request.user

        # Non-admin users should only see parents they have access to
        if user.role not in ['head', 'principal', 'vice_principal', 'accountant', 'secretary']:
            if user.role in ['teacher', 'form_teacher', 'subject_teacher']:
                # Teachers can see parents of students in their classes
                # This would require more complex filtering in real implementation
                pass
            elif user.role == 'parent':
                # Parents can only see themselves
                queryset = queryset.filter(user=user)

        return queryset.order_by('user__first_name')