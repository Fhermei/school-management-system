from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from users.models import User
from .models import Student
from parents.models import Parent
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def auto_create_student_profile(sender, instance, created, **kwargs):
    """
    Automatically create student profile when user role is 'student'
    """
    # Only process if role is student
    if instance.role != 'student':
        return
    
    try:
        with transaction.atomic():
            # Check if student profile already exists
            if not hasattr(instance, 'student_profile'):
                # Create student profile with auto-generated fields
                student = Student.objects.create(user=instance)
                logger.info(f"Auto-created student profile for {instance.registration_number}")
                
                # Send welcome email to student
                if instance.email and settings.DEBUG:
                    try:
                        send_mail(
                            subject='Welcome to School Student Portal',
                            message=f"""
                            Dear {instance.get_full_name()},
                            
                            Welcome to the School Student Portal!
                            
                            Your student account has been created successfully:
                            - Registration Number: {instance.registration_number}
                            - Admission Number: {student.admission_number}
                            - Student ID: {student.student_id}
                            
                            You can now:
                            1. View your timetable
                            2. Check your results
                            3. Track attendance
                            4. Access learning materials
                            
                            Please contact your class teacher if you have any questions.
                            
                            Best regards,
                            School Administration
                            """,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[instance.email],
                            fail_silently=True,
                        )
                        logger.info(f"Welcome email sent to student: {instance.email}")
                    except Exception as e:
                        logger.error(f"Failed to send student welcome email: {str(e)}")
                        
    except Exception as e:
        logger.error(f"Failed to auto-create student profile for {instance.registration_number}: {str(e)}")


@receiver(pre_save, sender=User)
def handle_role_change_to_student(sender, instance, **kwargs):
    """
    Handle user role change to student
    """
    try:
        # Get the old user instance if it exists
        if instance.pk:
            old_user = User.objects.get(pk=instance.pk)
            
            # If role changed TO student
            if old_user.role != 'student' and instance.role == 'student':
                logger.info(f"User role changed to student: {instance.registration_number}")
                
                # Check if already has student profile
                if not hasattr(instance, 'student_profile'):
                    # Student profile will be created in post_save
                    pass
                
            # If role changed FROM student
            elif old_user.role == 'student' and instance.role != 'student':
                logger.info(f"User role changed from student to {instance.role}: {instance.registration_number}")
                
                # Student profile will be automatically handled by cascade delete or can be kept
                # We'll keep it but mark as inactive
                if hasattr(instance, 'student_profile'):
                    instance.student_profile.is_active = False
                    instance.student_profile.save()
                    
    except User.DoesNotExist:
        # New user, no old instance
        pass
    except Exception as e:
        logger.error(f"Error handling role change for {instance.registration_number}: {str(e)}")


@receiver(post_save, sender=Student)
def student_profile_post_save(sender, instance, created, **kwargs):
    """
    Actions after student profile is saved
    """
    if created:
        logger.info(f"New student profile created: {instance.admission_number} - {instance.user.get_full_name()}")
        
        # Send notification to admin about new student
        try:
            admin_users = User.objects.filter(role__in=['head', 'principal', 'vice_principal'])
            for admin in admin_users:
                if admin.email:
                    send_mail(
                        subject='New Student Registration Notification',
                        message=f"""
                        New student registered in the system:
                        
                        Student Information:
                        - Name: {instance.user.get_full_name()}
                        - Admission Number: {instance.admission_number}
                        - Class: {instance.get_class_level_display()}
                        - Stream: {instance.get_stream_display()}
                        - Email: {instance.user.email}
                        - Phone: {instance.user.phone_number}
                        - Registration Date: {instance.created_at}
                        
                        Please assign the student to a class and link parents if available.
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin.email],
                        fail_silently=True,
                    )
        except Exception as e:
            logger.error(f"Failed to send student notification: {str(e)}")
        
        # Notify parents if linked
        if instance.father or instance.mother:
            parent_emails = []
            if instance.father and instance.father.user.email:
                parent_emails.append(instance.father.user.email)
            if instance.mother and instance.mother.user.email:
                parent_emails.append(instance.mother.user.email)
            
            for email in parent_emails:
                try:
                    send_mail(
                        subject=f'Your Child {instance.user.get_full_name()} Registered',
                        message=f"""
                        Dear Parent,
                        
                        Your child {instance.user.get_full_name()} has been registered in the school system.
                        
                        Student Details:
                        - Name: {instance.user.get_full_name()}
                        - Admission Number: {instance.admission_number}
                        - Class: {instance.get_class_level_display()}
                        - Student ID: {instance.student_id}
                        
                        You can now access their academic progress through the parent portal.
                        
                        Best regards,
                        School Administration
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send parent notification: {str(e)}")
    
    else:
        # Student profile updated
        logger.info(f"Student profile updated: {instance.admission_number}")
        
        # Log important changes
        update_fields = kwargs.get('update_fields', [])
        if update_fields:
            logger.info(f"Student {instance.admission_number} updated fields: {update_fields}")
            
            # Notify if fee status changed
            if 'fee_status' in update_fields:
                logger.info(f"Fee status changed for {instance.admission_number}: {instance.get_fee_status_display()}")
                
                # Notify parents about fee status change
                if instance.father or instance.mother:
                    parent_emails = []
                    if instance.father and instance.father.user.email:
                        parent_emails.append(instance.father.user.email)
                    if instance.mother and instance.mother.user.email:
                        parent_emails.append(instance.mother.user.email)
                    
                    for email in parent_emails:
                        try:
                            send_mail(
                                subject=f'Fee Status Update for {instance.user.get_full_name()}',
                                message=f"""
                                Dear Parent,
                                
                                The fee status for your child {instance.user.get_full_name()} has been updated.
                                
                                New Fee Status: {instance.get_fee_status_display()}
                                Total Fee: ₦{instance.total_fee_amount}
                                Amount Paid: ₦{instance.amount_paid}
                                Balance: ₦{instance.balance_due}
                                
                                Please contact the school accountant for any queries.
                                
                                Best regards,
                                School Administration
                                """,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[email],
                                fail_silently=True,
                            )
                        except Exception as e:
                            logger.error(f"Failed to send fee status notification: {str(e)}")


@receiver(post_delete, sender=Student)
def student_profile_post_delete(sender, instance, **kwargs):
    """
    Actions after student profile is deleted
    """
    logger.warning(f"Student profile deleted: {instance.admission_number} - {instance.user.get_full_name()}")
    
    # Send notification to admin
    try:
        admin_users = User.objects.filter(role__in=['head', 'principal', 'vice_principal'])
        for admin in admin_users:
            if admin.email:
                send_mail(
                    subject='Student Profile Deleted',
                    message=f"""
                    Student profile has been deleted from the system:
                    
                    Deleted Student:
                    - Name: {instance.user.get_full_name()}
                    - Admission Number: {instance.admission_number}
                    - Class: {instance.get_class_level_display()}
                    - Deletion Date: {timezone.now()}
                    
                    Please update any related records.
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    fail_silently=True,
                )
    except Exception as e:
        logger.error(f"Failed to send student deletion notification: {str(e)}")


@receiver(post_save, sender=Student)
def update_student_user_role(sender, instance, **kwargs):
    """
    Ensure user role matches student profile
    """
    # If user role is not student, update it
    if instance.user.role != 'student':
        instance.user.role = 'student'
        instance.user.save()
        logger.info(f"Updated user role to student for {instance.user.registration_number}")


@receiver(post_save, sender=Student)
def link_student_to_parent_by_name(sender, instance, created, **kwargs):
    """
    Attempt to auto-link student to parent by matching names
    This is a simple heuristic - in production, you'd have a better matching system
    """
    if created and (not instance.father or not instance.mother):
        try:
            from users.models import User
            
            # Try to find father by matching student's last name
            if not instance.father and instance.user.last_name:
                father_users = User.objects.filter(
                    last_name__iexact=instance.user.last_name,
                    role='parent'
                )
                
                for father_user in father_users:
                    try:
                        father_parent = father_user.parent_profile
                        if father_parent.parent_type in ['father', 'guardian']:
                            instance.father = father_parent
                            instance.save()
                            logger.info(f"Auto-linked student {instance.admission_number} to father {father_user.registration_number}")
                            break
                    except:
                        pass
            
            # Try to find mother by matching first name (simplistic)
            if not instance.mother and instance.user.first_name:
                # In Nigerian context, sometimes mother's maiden name is used
                # This is just a placeholder logic
                mother_users = User.objects.filter(
                    role='parent',
                    parent_profile__parent_type__in=['mother', 'guardian']
                )[:5]  # Limit search
                
                # More sophisticated matching would be needed in production
                
        except Exception as e:
            logger.error(f"Error in parent auto-linking: {str(e)}")