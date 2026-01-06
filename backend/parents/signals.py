from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from users.models import User
from .models import Parent
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def auto_create_parent_profile(sender, instance, created, **kwargs):
    """
    Auto-create parent profile when user role is 'parent'
    """
    if instance.role != 'parent':
        return
    
    try:
        with transaction.atomic():
            if not hasattr(instance, 'parent_profile'):
                parent = Parent.objects.create(user=instance)
                logger.info(f"Auto-created parent profile for {instance.registration_number}")
                
                # Send welcome email (debug mode only)
                if instance.email and settings.DEBUG:
                    try:
                        send_mail(
                            subject='Welcome to School Parent Portal',
                            message=f"""
                            Dear {instance.get_full_name()},
                            
                            Welcome to the School Parent Portal!
                            
                            Your account has been created:
                            - Registration: {instance.registration_number}
                            - Parent ID: {parent.parent_id}
                            
                            Contact school to link your children.
                            
                            Regards,
                            School Admin
                            """,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[instance.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        logger.error(f"Email error: {str(e)}")
                        
    except Exception as e:
        logger.error(f"Failed to create parent profile: {str(e)}")


@receiver(post_save, sender=Parent)
def update_user_role_to_parent(sender, instance, **kwargs):
    """
    Ensure user role matches parent profile
    """
    if instance.user.role != 'parent':
        instance.user.role = 'parent'
        instance.user.save()
        logger.info(f"Updated role to parent for {instance.user.registration_number}")


@receiver(post_delete, sender=Parent)
def log_parent_deletion(sender, instance, **kwargs):
    """
    Log when parent profile is deleted
    """
    logger.warning(f"Parent deleted: {instance.parent_id} - {instance.user.get_full_name()}")