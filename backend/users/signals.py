from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging
from .models import User

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    """
    Signal triggered before saving a User
    """
    # Log user creation/update
    if instance.pk:
        # Existing user being updated
        try:
            old_user = User.objects.get(pk=instance.pk)
            changes = []

            # Check for changes in important fields
            for field in ['first_name', 'last_name', 'email', 'role', 'is_active']:
                old_value = getattr(old_user, field, None)
                new_value = getattr(instance, field, None)

                if old_value != new_value:
                    changes.append(f"{field}: {old_value} -> {new_value}")

            if changes:
                logger.info(f"User {instance.registration_number} updated: {', '.join(changes)}")

        except User.DoesNotExist:
            pass

    # Ensure registration number is unique and generated
    if not instance.registration_number:
        # This will be handled by the save() method in the model
        pass

    # Validate role changes (could add more complex logic here)
    if instance.pk and instance.role_changed:
        logger.info(f"User {instance.registration_number} role changed to: {instance.role}")


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Signal triggered after saving a User
    """
    if created:
        # New user created
        logger.info(f"New user created: {instance.registration_number} ({instance.role})")

        # Send welcome email in production
        if settings.EMAIL_HOST_USER and instance.email:
            try:
                subject = f"Welcome to {settings.SCHOOL_NAME or 'Our School'} Management System"
                message = f"""
                Dear {instance.first_name} {instance.last_name},

                Welcome to our School Management System!

                Your registration details:
                - Registration Number: {instance.registration_number}
                - Role: {instance.get_role_display()}
                - Email: {instance.email}

                Please keep your registration number safe as you'll need it to login.

                Best regards,
                School Administration
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.email],
                    fail_silently=True,
                )
                logger.info(f"Welcome email sent to {instance.email}")
            except Exception as e:
                logger.error(f"Failed to send welcome email to {instance.email}: {str(e)}")

    # Log user activation/deactivation
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            if old_user.is_active != instance.is_active:
                action = "activated" if instance.is_active else "deactivated"
                logger.info(f"User {instance.registration_number} {action} by system")
        except User.DoesNotExist:
            pass

    # Log user verification
    if instance.is_verified and instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            if not old_user.is_verified and instance.is_verified:
                logger.info(f"User {instance.registration_number} verified by admin")

                # Send verification email
                if settings.EMAIL_HOST_USER and instance.email:
                    try:
                        subject = f"Account Verified - {settings.SCHOOL_NAME or 'Our School'}"
                        message = f"""
                        Dear {instance.first_name} {instance.last_name},

                        Your account has been verified by the school administration.

                        You can now fully access all features of the School Management System.

                        Your registration number: {instance.registration_number}

                        Best regards,
                        School Administration
                        """

                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [instance.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send verification email to {instance.email}: {str(e)}")
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create related profiles based on user role
    This signal will be connected in the respective apps
    """
    if created:
        # This will be handled by the respective apps (students, staff, parents)
        # Each app will have its own signal receiver
        pass


def setup_user_signals():
    """
    Function to explicitly set up user signals
    Call this in apps.py ready() method
    """
    from django.db.models.signals import post_save, pre_save

    # Connect signals
    pre_save.connect(user_pre_save, sender=User)
    post_save.connect(user_post_save, sender=User)

    logger.info("User signals setup completed")


def disconnect_user_signals():
    """
    Function to disconnect user signals (for testing)
    """
    from django.db.models.signals import post_save, pre_save

    # Disconnect signals
    pre_save.disconnect(user_pre_save, sender=User)
    post_save.disconnect(user_post_save, sender=User)

    logger.info("User signals disconnected")