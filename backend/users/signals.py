from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle actions after user is saved
    """
    if created:
        # New user created
        logger.info(f"New user created: {instance.username} ({instance.role})")
        
        # Send welcome email (in production)
        if instance.email and settings.DEBUG:
            try:
                send_mail(
                    subject='Welcome to School Management System',
                    message=f"""
                    Welcome {instance.get_full_name()}!
                    
                    Your account has been created successfully.
                    
                    Registration Number: {instance.registration_number}
                    Username: {instance.username}
                    Role: {instance.get_role_display()}
                    
                    Please contact administrator for your initial password.
                    
                    Best regards,
                    School Administration
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=True,
                )
                logger.info(f"Welcome email sent to: {instance.email}")
            except Exception as e:
                logger.error(f"Failed to send welcome email: {str(e)}")
    
    # Additional logic for user updates
    if not created:
        logger.info(f"User updated: {instance.username}")