from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging
from .models import Parent
from users.models import User

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Parent)
def parent_pre_save(sender, instance, **kwargs):
    """
    Signal triggered before saving a Parent
    """
    # Auto-generate parent ID if not set
    if not instance.parent_id:
        # This will be handled by the save() method in the model
        pass

    # Ensure user has parent role
    if instance.user and instance.user.role != 'parent':
        instance.user.role = 'parent'
        instance.user.save()
        logger.info(f"User {instance.user.registration_number} role updated to parent")

    # Log changes for existing parents
    if instance.pk:
        try:
            old_parent = Parent.objects.get(pk=instance.pk)
            changes = []

            # Track important field changes
            for field in ['parent_type', 'marital_status', 'is_pta_member', 'is_active']:
                old_value = getattr(old_parent, field, None)
                new_value = getattr(instance, field, None)

                if old_value != new_value:
                    changes.append(f"{field}: {old_value} -> {new_value}")

            if changes:
                logger.info(f"Parent {instance.parent_id} updated: {', '.join(changes)}")

        except Parent.DoesNotExist:
            pass


@receiver(post_save, sender=Parent)
def parent_post_save(sender, instance, created, **kwargs):
    """
    Signal triggered after saving a Parent
    """
    if created:
        # New parent created
        logger.info(f"New parent created: {instance.parent_id} ({instance.parent_type})")

        # Send welcome email
        self._send_welcome_email(instance)

        # Update spouse relationship if married
        if instance.marital_status == 'married' and instance.spouse:
            instance.spouse.spouse = instance
            instance.spouse.save()
            logger.info(f"Updated spouse relationship for {instance.parent_id}")

    # Handle verification
    if instance.is_verified and instance.pk:
        try:
            old_parent = Parent.objects.get(pk=instance.pk)
            if not old_parent.is_verified and instance.is_verified:
                logger.info(f"Parent {instance.parent_id} verified")
                self._send_verification_email(instance)
        except Parent.DoesNotExist:
            pass

    # Handle PTA status changes
    if instance.pk:
        try:
            old_parent = Parent.objects.get(pk=instance.pk)
            if old_parent.is_pta_member != instance.is_pta_member:
                status = "added to" if instance.is_pta_member else "removed from"
                logger.info(f"Parent {instance.parent_id} {status} PTA")
                self._send_pta_notification(instance, instance.is_pta_member)
        except Parent.DoesNotExist:
            pass

    def _send_welcome_email(self, parent):
        """Send welcome email to new parent"""
        if parent.user.email and settings.EMAIL_HOST_USER:
            try:
                subject = f"Welcome Parent - {settings.SCHOOL_NAME or 'Our School'}"
                message = f"""
                Dear {parent.user.get_full_name()},

                Welcome to the parent community of {settings.SCHOOL_NAME or 'Our School'}!

                Your parent details:
                - Parent ID: {parent.parent_id}
                - Parent Type: {parent.get_parent_type_display()}
                - Relationship: {parent.get_marital_status_display()}

                As a parent, you can:
                - Monitor your children's academic progress
                - Receive school notifications
                - View and pay school fees online
                - Participate in PTA activities
                - Communicate with teachers

                Please keep your parent ID safe for future reference.

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
                logger.info(f"Welcome email sent to parent {parent.user.email}")
            except Exception as e:
                logger.error(f"Failed to send welcome email to {parent.user.email}: {str(e)}")

    def _send_verification_email(self, parent):
        """Send verification email to parent"""
        if parent.user.email and settings.EMAIL_HOST_USER:
            try:
                subject = f"Parent Account Verified - {settings.SCHOOL_NAME or 'Our School'}"
                message = f"""
                Dear {parent.user.get_full_name()},

                Your parent account has been verified by the school administration.

                You now have full access to all parent features including:
                - Real-time academic updates for your children
                - Fee payment and receipt generation
                - Parent-teacher communication
                - School event notifications

                Parent ID: {parent.parent_id}

                Thank you for being part of our school community.

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

    def _send_pta_notification(self, parent, is_member):
        """Send PTA membership notification"""
        if parent.user.email and settings.EMAIL_HOST_USER:
            try:
                if is_member:
                    subject = f"PTA Membership Confirmation - {settings.SCHOOL_NAME or 'Our School'}"
                    message = f"""
                    Dear {parent.user.get_full_name()},

                    Congratulations! You have been added as a PTA member.

                    PTA Role: {parent.pta_position or 'Member'}
                    Committee: {parent.pta_committee or 'General'}

                    As a PTA member, you play a vital role in our school community.
                    Your participation is highly appreciated.

                    Best regards,
                    School Administration
                    """
                else:
                    subject = f"PTA Membership Update - {settings.SCHOOL_NAME or 'Our School'}"
                    message = f"""
                    Dear {parent.user.get_full_name()},

                    Your PTA membership status has been updated.

                    You are no longer listed as a PTA member.
                    Thank you for your previous service and contributions.

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


@receiver(pre_delete, sender=Parent)
def parent_pre_delete(sender, instance, **kwargs):
    """
    Signal triggered before deleting a Parent
    """
    # Log parent deletion
    logger.warning(
        f"Parent {instance.parent_id} ({instance.user.get_full_name()}) "
        f"is being deleted from the system"
    )

    # Remove parent references from children
    self._unlink_children(instance)

    # Remove spouse reference
    if instance.spouse:
        instance.spouse.spouse = None
        instance.spouse.save()
        logger.info(f"Removed spouse reference from {instance.spouse.parent_id}")

    # Archive important data before deletion
    self._archive_parent_data(instance)

    def _unlink_children(self, parent):
        """Unlink parent from all children"""
        from students.models import Student

        # Unlink as father
        children_as_father = Student.objects.filter(father=parent)
        for child in children_as_father:
            child.father = None
            child.save()
            logger.info(f"Unlinked {child.admission_number} from father {parent.parent_id}")

        # Unlink as mother
        children_as_mother = Student.objects.filter(mother=parent)
        for child in children_as_mother:
            child.mother = None
            child.save()
            logger.info(f"Unlinked {child.admission_number} from mother {parent.parent_id}")

    def _archive_parent_data(self, parent):
        """Archive parent data before deletion"""
        # This is a placeholder for actual archiving logic
        # In production, you might:
        # 1. Create an archive record
        # 2. Move files to archive storage
        # 3. Update references
        pass


def setup_parent_signals():
    """
    Function to explicitly set up parent signals
    Call this in apps.py ready() method
    """
    from django.db.models.signals import post_save, pre_save, pre_delete

    # Connect signals
    pre_save.connect(parent_pre_save, sender=Parent)
    post_save.connect(parent_post_save, sender=Parent)
    pre_delete.connect(parent_pre_delete, sender=Parent)

    logger.info("Parent signals setup completed")


def disconnect_parent_signals():
    """
    Function to disconnect parent signals (for testing)
    """
    from django.db.models.signals import post_save, pre_save, pre_delete

    # Disconnect signals
    pre_save.disconnect(parent_pre_save, sender=Parent)
    post_save.disconnect(parent_post_save, sender=Parent)
    pre_delete.disconnect(parent_pre_delete, sender=Parent)

    logger.info("Parent signals disconnected")