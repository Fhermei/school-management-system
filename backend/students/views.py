from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
import logging

from .models import Student
from .serializers import (
    StudentSerializer,
    StudentCreateSerializer,
    StudentListSerializer,
    FeePaymentSerializer
)
from .permissions import (
    IsAdminOrPrincipal,
    CanEditStudent,
    CanEditFee
)

logger = logging.getLogger(__name__)


class StudentListView(generics.ListAPIView):
    serializer_class = StudentListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPrincipal]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['class_level', 'stream', 'fee_status', 'is_active']
    search_fields = [
        'user__first_name', 'user__last_name',
        'admission_number'
    ]

    def get_queryset(self):
        return Student.objects.all()


class StudentCreateView(generics.CreateAPIView):
    serializer_class = StudentCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPrincipal]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        logger.info(f"Student created: {student.admission_number}")

        return Response({
            'message': 'Student created successfully',
            'student': StudentSerializer(student).data
        }, status=status.HTTP_201_CREATED)


class StudentDetailView(generics.RetrieveAPIView):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditStudent]
    queryset = Student.objects.all()


class StudentUpdateView(generics.UpdateAPIView):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, CanEditStudent]
    queryset = Student.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.can_edit_profile(request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Student updated successfully',
            'student': serializer.data
        })


class StudentFeePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanEditFee]

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)

        serializer = FeePaymentSerializer(
            data=request.data,
            context={'student': student}
        )
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        student.amount_paid += amount
        student.save()

        return Response({
            'message': 'Payment recorded successfully',
            'student': StudentSerializer(student).data
        })


class StudentFeeSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)

        return Response({
            'fee_summary': student.get_fee_summary(),
            'student': {
                'name': student.user.get_full_name(),
                'admission_number': student.admission_number
            }
        })

class StudentBulkCreateView(APIView):
    """
    Bulk create students
    POST /api/students/bulk-create/
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrPrincipal]

    def post(self, request):
        students_data = request.data.get('students')

        if not isinstance(students_data, list):
            return Response(
                {'error': 'students must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = []
        errors = []

        from users.models import User

        for index, data in enumerate(students_data):
            try:
                user = User.objects.create_user(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    email=data.get('email'),
                    role='student'
                )

                student = Student.objects.create(
                    user=user,
                    class_level=data.get('class_level'),
                    stream=data.get('stream'),
                    total_fee_amount=data.get('total_fee', 0)
                )

                created.append(student)

            except Exception as e:
                errors.append({
                    'index': index,
                    'error': str(e)
                })

        return Response({
            'created_count': len(created),
            'failed_count': len(errors),
            'students': StudentListSerializer(created, many=True).data,
            'errors': errors
        }, status=status.HTTP_201_CREATED)
