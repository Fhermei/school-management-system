from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
import logging

from .models import Parent
from .serializers import (
    ParentSerializer,
    ParentCreateSerializer,
    ParentListSerializer,
    ParentDashboardSerializer
)
from .permissions import IsParent, CanEditParent

logger = logging.getLogger(__name__)


class ParentListView(generics.ListAPIView):
    """
    List all parents
    
    GET /api/parents/
    
    Filters: parent_type, marital_status, is_pta_member, is_active
    Search: name, email, parent_id, occupation
    
    Note: Admin/Principal only
    """
    serializer_class = ParentListSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    
    filterset_fields = ['parent_type', 'marital_status', 'is_pta_member', 'is_active']
    search_fields = [
        'user__first_name', 'user__last_name',
        'user__email', 'parent_id', 'occupation'
    ]
    ordering = ['user__first_name']
    
    def get_queryset(self):
        return Parent.objects.all()


class ParentCreateView(generics.CreateAPIView):
    """
    Create new parent profile
    
    POST /api/parents/create/
    
    Required: user_id, parent_type
    """
    serializer_class = ParentCreateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        parent = serializer.save()
        
        logger.info(f"Parent created: {parent.parent_id} by {request.user.registration_number}")
        
        return Response({
            'message': 'Parent created successfully',
            'parent': ParentSerializer(parent).data
        }, status=status.HTTP_201_CREATED)


class ParentDetailView(generics.RetrieveAPIView):
    """
    Get parent details
    
    GET /api/parents/{id}/
    
    Permissions:
    - Parent can view own profile
    - Admin can view any profile
    """
    serializer_class = ParentSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditParent]
    queryset = Parent.objects.all()
    
    def get_object(self):
        # If user is parent, return their own profile
        if self.request.user.role == 'parent':
            try:
                return self.request.user.parent_profile
            except Parent.DoesNotExist:
                pass
        
        # Otherwise use the normal lookup
        return super().get_object()


class ParentUpdateView(generics.UpdateAPIView):
    """
    Update parent profile
    
    PUT/PATCH /api/parents/{id}/update/
    
    Permissions:
    - Parent can update own profile (limited fields)
    - Admin can update any profile
    """
    serializer_class = ParentSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditParent]
    queryset = Parent.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check permissions
        if not instance.can_edit_profile(request.user):
            return Response({
                'error': 'You do not have permission to edit this parent'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Parents cannot edit restricted fields
        if request.user.role == 'parent' and instance.user == request.user:
            restricted_fields = ['parent_id', 'is_verified', 'user', 'parent_type']
            for field in restricted_fields:
                if field in request.data:
                    return Response({
                        'error': f'You cannot modify the {field} field'
                    }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        logger.info(f"Parent updated: {instance.parent_id} by {request.user.registration_number}")
        
        return Response({
            'message': 'Parent updated successfully',
            'parent': serializer.data
        })


class ParentDashboardView(APIView):
    """
    Parent dashboard with children and fee summary
    
    GET /api/parents/dashboard/
    
    Note: Parents only
    """
    permission_classes = [permissions.IsAuthenticated, IsParent]
    
    def get(self, request):
        try:
            parent = request.user.parent_profile
            serializer = ParentDashboardSerializer(parent)
            
            return Response({
                'dashboard': serializer.data,
                'quick_stats': {
                    'total_children': parent.get_children_count(),
                    'active_children': parent.get_children().filter(is_active=True).count(),
                    'total_fee_due': parent.get_fee_summary()['total_balance'],
                    'pta_member': parent.is_pta_member
                }
            })
            
        except Parent.DoesNotExist:
            return Response({
                'error': 'Parent profile not found. Please contact administrator.'
            }, status=status.HTTP_404_NOT_FOUND)


class ParentChildrenView(generics.ListAPIView):
    """
    Get all children of logged-in parent
    
    GET /api/parents/children/
    
    Note: Parents only
    """
    permission_classes = [permissions.IsAuthenticated, IsParent]
    
    def get_serializer_class(self):
        """Dynamically get serializer to avoid circular import"""
        from students.serializers import StudentListSerializer
        return StudentListSerializer
    
    def get_queryset(self):
        """Get parent's children"""
        try:
            parent = self.request.user.parent_profile
            return parent.get_children().order_by('class_level')
        except Parent.DoesNotExist:
            return Parent.objects.none()


class LinkChildToParentView(APIView):
    """
    Link existing student to parent
    
    POST /api/parents/link-child/
    
    Required: student_admission_number, parent_id, relationship_type
    
    Note: Admin/Principal only
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def post(self, request):
        student_admission = request.data.get('student_admission_number')
        parent_id = request.data.get('parent_id')
        relationship = request.data.get('relationship_type')
        
        # Validate required fields
        if not all([student_admission, parent_id, relationship]):
            return Response({
                'error': 'Missing required fields: student_admission_number, parent_id, relationship_type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate relationship
        if relationship not in ['father', 'mother']:
            return Response({
                'error': 'relationship_type must be "father" or "mother"'
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
        
        # Link student to parent
        if relationship == 'father':
            student.father = parent
        else:
            student.mother = parent
        
        student.save()
        
        logger.info(f"Linked student {student.admission_number} to parent {parent.parent_id} as {relationship}")
        
        # Get serializer dynamically to avoid circular import
        from students.serializers import StudentListSerializer
        
        return Response({
            'message': f'Successfully linked student to parent as {relationship}',
            'student': StudentListSerializer(student).data,
            'parent': ParentSerializer(parent).data
        })