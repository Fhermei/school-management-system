from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging
from .models import Student, StudentEnrollment
from users.models import User

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Student)
def student_pre_save(sender, instance, **kwargs):
    """
    Signal triggered before saving a Student
    """
    # Ensure user has student role
    if instance.user and instance.user.role != 'student':
        instance.user.role = 'student'
        instance.user.save()
        logger.info(f"User {instance.user.registration_number} role updated to student")

    # Log changes for existing students
    if instance.pk:
        try:
            old_student = Student.objects.get(pk=instance.pk)
            changes = []

            # Track important field changes
            for field in ['class_level', 'fee_status', 'is_active', 'is_graduated']:
                old_value = getattr(old_student, field, None)
                new_value = getattr(instance, field, None)

                if old_value != new_value:
                    if field == 'class_level':
                        old_name = old_value.name if old_value else 'None'
                        new_name = new_value.name if new_value else 'None'
                        changes.append(f"{field}: {old_name} -> {new_name}")
                    else:
                        changes.append(f"{field}: {old_value} -> {new_value}")

            if changes:
                logger.info(f"Student {instance.admission_number} updated: {', '.join(changes)}")

        except Student.DoesNotExist:
            pass


@receiver(post_save, sender=Student)
def student_post_save(sender, instance, created, **kwargs):
    """
    Signal triggered after saving a Student
    """
    if created:
        # New student created
        logger.info(f"New student created: {instance.admission_number} ({instance.student_id})")

        # Send notification to parents if email available
        self._notify_parents(instance)

        # Create initial enrollment if class level is set
        if instance.class_level:
            self._create_initial_enrollment(instance)

    # Handle graduation
    if instance.is_graduated and instance.pk:
        try:
            old_student = Student.objects.get(pk=instance.pk)
            if not old_student.is_graduated:
                logger.info(f"Student {instance.admission_number} graduated")
                self._handle_graduation(instance)
        except Student.DoesNotExist:
            pass

    # Handle fee status changes
    if instance.pk:
        try:
            old_student = Student.objects.get(pk=instance.pk)
            if old_student.fee_status != instance.fee_status:
                logger.info(
                    f"Student {instance.admission_number} fee status changed: "
                    f"{old_student.fee_status} -> {instance.fee_status}"
                )
                self._notify_fee_status_change(instance, old_student.fee_status)
        except Student.DoesNotExist:
            pass

    def _notify_parents(self, student):
        """Send notification to parents about student creation"""
        parents = student.get_parents()

        for parent in parents:
            if parent.user.email and settings.EMAIL_HOST_USER:
                try:
                    subject = f"Student Registration - {settings.SCHOOL_NAME or 'Our School'}"
                    message = f"""
                    Dear {parent.user.get_full_name()},

                    Your child {student.user.get_full_name()} has been registered in our school.

                    Student Details:
                    - Admission Number: {student.admission_number}
                    - Student ID: {student.student_id}
                    - Class: {student.class_level.name if student.class_level else 'Not Assigned'}
                    - Registration Number: {student.user.registration_number}

                    Please keep this information safe.

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
                    logger.info(f"Student registration notification sent to {parent.user.email}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {parent.user.email}: {str(e)}")

    def _create_initial_enrollment(self, student):
        """Create initial enrollment record for student"""
        from academic.models import AcademicSession, AcademicTerm

        try:
            current_session = AcademicSession.objects.filter(is_current=True).first()
            current_term = AcademicTerm.objects.filter(is_current=True).first()

            if current_session and current_term:
                enrollment = StudentEnrollment.objects.create(
                    student=student.user,
                    class_obj=None,  # Would need specific class object
                    session=current_session,
                    term=current_term,
                    status='active',
                    enrollment_date=student.admission_date or timezone.now().date(),
                    enrolled_by=student.user  # Or system user
                )
                logger.info(f"Initial enrollment created for student {student.admission_number}")
        except Exception as e:
            logger.error(f"Failed to create initial enrollment: {str(e)}")

    def _handle_graduation(self, student):
        """Handle student graduation"""
        # Update user status
        student.user.is_active = False
        student.user.save()

        # Send graduation notification
        if student.user.email and settings.EMAIL_HOST_USER:
            try:
                subject = f"Congratulations on Graduation - {settings.SCHOOL_NAME or 'Our School'}"
                message = f"""
                Dear {student.user.get_full_name()},

                Congratulations on your graduation from {settings.SCHOOL_NAME or 'Our School'}!

                We are proud of your achievements and wish you success in your future endeavors.

                Graduation Details:
                - Student: {student.user.get_full_name()}
                - Admission Number: {student.admission_number}
                - Graduation Date: {student.graduation_date or 'Not specified'}
                - Final Class: {student.class_level.name if student.class_level else 'Not specified'}

                Best wishes,
                School Administration
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [student.user.email],
                    fail_silently=True,
                )

                # Also notify parents
                parents = student.get_parents()
                for parent in parents:
                    if parent.user.email:
                        parent_subject = f"Your Child's Graduation - {settings.SCHOOL_NAME or 'Our School'}"
                        parent_message = f"""
                        Dear {parent.user.get_full_name()},

                        We are pleased to inform you that your child {student.user.get_full_name()} 
                        has successfully graduated from {settings.SCHOOL_NAME or 'Our School'}.

                        Congratulations to you and your family!

                        Best regards,
                        School Administration
                        """

                        send_mail(
                            parent_subject,
                            parent_message,
                            settings.DEFAULT_FROM_EMAIL,
                            [parent.user.email],
                            fail_silently=True,
                        )

                logger.info(f"Graduation notifications sent for student {student.admission_number}")
            except Exception as e:
                logger.error(f"Failed to send graduation notifications: {str(e)}")

    def _notify_fee_status_change(self, student, old_status):
        """Notify about fee status change"""
        if student.user.email and settings.EMAIL_HOST_USER:
            try:
                subject = f"Fee Status Update - {settings.SCHOOL_NAME or 'Our School'}"
                message = f"""
                Dear {student.user.get_full_name()},

                Your fee status has been updated.

                Old Status: {old_status}
                New Status: {student.fee_status}
                Amount Paid: ₦{student.amount_paid:,.2f}
                Total Fee: ₦{student.total_fee_amount:,.2f}
                Balance Due: ₦{student.balance_due:,.2f}

                Thank you for your prompt payment.

                Best regards,
                School Administration
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [student.user.email],
                    fail_silently=True,
                )
                logger.info(f"Fee status change notification sent to {student.user.email}")
            except Exception as e:
                logger.error(f"Failed to send fee status notification: {str(e)}")


@receiver(pre_save, sender=StudentEnrollment)
def enrollment_pre_save(sender, instance, **kwargs):
    """
    Signal triggered before saving a StudentEnrollment
    """
    # Auto-generate enrollment number if not set
    if not instance.enrollment_number and instance.student and instance.session and instance.class_obj:
        year = instance.session.start_date.year
        student_id = instance.student.registration_number
        class_code = instance.class_obj.code
        instance.enrollment_number = f"ENR-{year}-{class_code}-{student_id}"

    # Log enrollment status changes
    if instance.pk:
        try:
            old_enrollment = StudentEnrollment.objects.get(pk=instance.pk)
            if old_enrollment.status != instance.status:
                logger.info(
                    f"Enrollment {instance.enrollment_number} status changed: "
                    f"{old_enrollment.status} -> {instance.status}"
                )

                # Send notification for important status changes
                if instance.status == 'active' and old_enrollment.status != 'active':
                    self._notify_enrollment_activation(instance)
        except StudentEnrollment.DoesNotExist:
            pass

    def _notify_enrollment_activation(self, enrollment):
        """Notify about enrollment activation"""
        if enrollment.student.email and settings.EMAIL_HOST_USER:
            try:
                subject = f"Enrollment Activated - {settings.SCHOOL_NAME or 'Our School'}"
                message = f"""
                Dear {enrollment.student.get_full_name()},

                Your enrollment has been activated.

                Enrollment Details:
                - Enrollment Number: {enrollment.enrollment_number}
                - Class: {enrollment.class_obj.name if enrollment.class_obj else 'Not specified'}
                - Session: {enrollment.session.name}
                - Term: {enrollment.term.name}
                - Status: {enrollment.get_status_display()}
                - Enrollment Date: {enrollment.enrollment_date}

                You can now access all class materials and participate in activities.

                Best regards,
                School Administration
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [enrollment.student.email],
                    fail_silently=True,
                )
                logger.info(f"Enrollment activation notification sent to {enrollment.student.email}")
            except Exception as e:
                logger.error(f"Failed to send enrollment activation notification: {str(e)}")


@receiver(pre_delete, sender=Student)
def student_pre_delete(sender, instance, **kwargs):
    """
    Signal triggered before deleting a Student
    """
    # Log student deletion
    logger.warning(
        f"Student {instance.admission_number} ({instance.user.get_full_name()}) "
        f"is being deleted from the system"
    )

    # Archive important data before deletion
    # In production, you might want to soft delete instead
    self._archive_student_data(instance)

    def _archive_student_data(self, student):
        """Archive student data before deletion"""
        # This is a placeholder for actual archiving logic
        # In production, you might:
        # 1. Create an archive record
        # 2. Move files to archive storage
        # 3. Update references
        pass


def setup_student_signals():
    """
    Function to explicitly set up student signals
    Call this in apps.py ready() method
    """
    from django.db.models.signals import post_save, pre_save, pre_delete

    # Connect signals
    pre_save.connect(student_pre_save, sender=Student)
    post_save.connect(student_post_save, sender=Student)
    pre_save.connect(enrollment_pre_save, sender=StudentEnrollment)
    pre_delete.connect(student_pre_delete, sender=Student)

    logger.info("Student signals setup completed")


def disconnect_student_signals():
    """
    Function to disconnect student signals (for testing)
    """
    from django.db.models.signals import post_save, pre_save, pre_delete

    # Disconnect signals
    pre_save.disconnect(student_pre_save, sender=Student)
    post_save.disconnect(student_post_save, sender=Student)
    pre_save.disconnect(enrollment_pre_save, sender=StudentEnrollment)
    pre_delete.disconnect(student_pre_delete, sender=Student)

    logger.info("Student signals disconnected")