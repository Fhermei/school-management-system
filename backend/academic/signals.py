from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    AcademicSession, AcademicTerm, Class,
    ClassSubject, Timetable, StudentEnrollment
)
import logging

logger = logging.getLogger(__name__)


# ============================================
# Academic Session Signals
# ============================================

@receiver(pre_save, sender=AcademicSession)
def validate_academic_session(sender, instance, **kwargs):
    """Validate academic session before saving"""
    if instance.start_date >= instance.end_date:
        raise ValueError("Academic session end date must be after start date")

    # Ensure only one session is marked as current
    if instance.is_current:
        AcademicSession.objects.filter(is_current=True).exclude(pk=instance.pk).update(is_current=False)


@receiver(post_save, sender=AcademicSession)
def log_academic_session_change(sender, instance, created, **kwargs):
    """Log academic session changes"""
    action = "created" if created else "updated"
    logger.info(f"Academic session {action}: {instance.name} (ID: {instance.id})")


# ============================================
# Academic Term Signals
# ============================================

@receiver(pre_save, sender=AcademicTerm)
def validate_academic_term(sender, instance, **kwargs):
    """Validate academic term before saving"""
    # Validate dates
    if instance.start_date >= instance.end_date:
        raise ValueError("Academic term end date must be after start date")

    # Ensure term dates are within session dates
    if (instance.start_date < instance.session.start_date or
            instance.end_date > instance.session.end_date):
        raise ValueError("Term dates must be within session dates")

    # Ensure only one term is marked as current
    if instance.is_current:
        AcademicTerm.objects.filter(is_current=True).exclude(pk=instance.pk).update(is_current=False)

    # Auto-generate name if not provided
    if not instance.name:
        instance.name = f"{instance.get_term_display()} {instance.session.name}"


@receiver(post_save, sender=AcademicTerm)
def log_academic_term_change(sender, instance, created, **kwargs):
    """Log academic term changes"""
    action = "created" if created else "updated"
    logger.info(f"Academic term {action}: {instance.name} (ID: {instance.id})")


# ============================================
# Class Signals
# ============================================

@receiver(pre_save, sender=Class)
def generate_class_codes(sender, instance, **kwargs):
    """Auto-generate class code and slug before saving"""
    if not instance.code and instance.session and instance.term and instance.class_level:
        # Generate unique class code
        year = instance.session.start_date.year
        term_code = {'first': 'T1', 'second': 'T2', 'third': 'T3'}.get(instance.term.term, 'TX')
        instance.code = f"{instance.class_level.code}-{instance.name}-{year}-{term_code}"

    if not instance.slug and instance.code and instance.session:
        from django.utils.text import slugify
        instance.slug = slugify(f"{instance.code}-{instance.session.name}")

    # Validate term belongs to session
    if instance.term.session != instance.session:
        raise ValueError("Term must belong to the selected session")


@receiver(pre_save, sender=Class)
def validate_class_teacher(sender, instance, **kwargs):
    """Validate class teacher assignment"""
    if instance.class_teacher and instance.class_teacher.role not in [
        'teacher', 'form_teacher', 'subject_teacher',
        'head', 'principal', 'vice_principal'
    ]:
        raise ValueError("Class teacher must have a teaching role")


@receiver(post_save, sender=Class)
def log_class_change(sender, instance, created, **kwargs):
    """Log class changes"""
    action = "created" if created else "updated"
    logger.info(f"Class {action}: {instance.name} (ID: {instance.id})")


# ============================================
# Class Subject Signals
# ============================================

@receiver(pre_save, sender=ClassSubject)
def validate_class_subject(sender, instance, **kwargs):
    """Validate class-subject assignment before saving"""
    # Ensure teacher is a staff member
    if instance.teacher and instance.teacher.role not in [
        'teacher', 'form_teacher', 'subject_teacher',
        'head', 'principal', 'vice_principal'
    ]:
        raise ValueError("Assigned teacher must have a teaching role")

    # Ensure teacher can teach this subject
    if instance.teacher and instance.subject:
        if not instance.subject.can_be_taught_by(instance.teacher):
            raise ValueError(f"Teacher {instance.teacher.get_full_name()} cannot teach {instance.subject.name}")

    # Set default periods if not specified
    if not instance.periods_per_week:
        instance.periods_per_week = instance.subject.periods_per_week


@receiver(post_save, sender=ClassSubject)
def update_teacher_workload(sender, instance, created, **kwargs):
    """Update teacher's workload when assigned to a subject"""
    if instance.teacher and hasattr(instance.teacher, 'staff_profile'):
        try:
            teacher_profile = instance.teacher.staff_profile.teacher_profile
            # Update current periods per week
            teacher_profile.current_periods_per_week += instance.periods_per_week
            teacher_profile.save()
        except:
            pass  # Teacher may not have a teacher profile yet


@receiver(pre_delete, sender=ClassSubject)
def decrease_teacher_workload(sender, instance, **kwargs):
    """Decrease teacher's workload when removed from a subject"""
    if instance.teacher and hasattr(instance.teacher, 'staff_profile'):
        try:
            teacher_profile = instance.teacher.staff_profile.teacher_profile
            # Decrease current periods per week
            teacher_profile.current_periods_per_week -= instance.periods_per_week
            if teacher_profile.current_periods_per_week < 0:
                teacher_profile.current_periods_per_week = 0
            teacher_profile.save()
        except:
            pass  # Teacher may not have a teacher profile


# ============================================
# Timetable Signals
# ============================================

@receiver(pre_save, sender=Timetable)
def generate_timetable_code(sender, instance, **kwargs):
    """Auto-generate timetable code before saving"""
    if not instance.code:
        # Generate unique timetable code
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        scope_code = instance.scope[:3].upper() if instance.scope else 'GEN'
        instance.code = f"TT-{scope_code}-{timestamp}"

    # Ensure only one active timetable per scope
    if instance.is_active:
        # Find other active timetables with same scope and target
        filter_kwargs = {
            'is_active': True,
            'scope': instance.scope,
            'session': instance.session,
            'term': instance.term,
        }

        # Add target filter based on scope
        if instance.scope == 'program' and instance.program:
            filter_kwargs['program'] = instance.program
        elif instance.scope == 'class_level' and instance.class_level:
            filter_kwargs['class_level'] = instance.class_level
        elif instance.scope == 'class' and instance.class_obj:
            filter_kwargs['class_obj'] = instance.class_obj
        elif instance.scope == 'teacher' and instance.teacher:
            filter_kwargs['teacher'] = instance.teacher

        # Exclude self from update
        if instance.pk:
            filter_kwargs['pk__ne'] = instance.pk

        # Deactivate other timetables
        Timetable.objects.filter(**filter_kwargs).update(is_active=False)

    # Validate scope-target consistency
    instance._validate_scope_target()


@receiver(post_save, sender=Timetable)
def log_timetable_change(sender, instance, created, **kwargs):
    """Log timetable changes"""
    action = "created" if created else "updated"
    logger.info(f"Timetable {action}: {instance.name} (ID: {instance.id})")


# ============================================
# Timetable Entry Signals
# ============================================

@receiver(pre_save, sender=TimetableEntry)
def validate_timetable_entry(sender, instance, **kwargs):
    """Validate timetable entry before saving"""
    # Validate period number
    if instance.period_number < 1 or instance.period_number > instance.timetable.periods_per_day:
        raise ValueError(f"Period number must be between 1 and {instance.timetable.periods_per_day}")

    # Validate teacher assignment
    if instance.teacher and instance.subject:
        if not instance.subject.can_be_taught_by(instance.teacher):
            raise ValueError(f"Teacher {instance.teacher.get_full_name()} cannot teach {instance.subject.name}")


# ============================================
# Student Enrollment Signals
# ============================================

@receiver(pre_save, sender=StudentEnrollment)
def generate_enrollment_number(sender, instance, **kwargs):
    """Auto-generate enrollment number before saving"""
    if not instance.enrollment_number:
        # Generate unique enrollment number
        year = instance.session.start_date.year if instance.session else timezone.now().year
        student_id = instance.student.registration_number if instance.student else 'UNKNOWN'
        class_code = instance.class_obj.code if instance.class_obj else 'NOCLASS'
        instance.enrollment_number = f"ENR-{year}-{class_code}-{student_id}"


@receiver(post_save, sender=StudentEnrollment)
def update_class_enrollment_count(sender, instance, created, **kwargs):
    """Update class enrollment count when enrollment status changes"""
    if instance.status == 'active':
        # Update class enrollment count
        active_enrollments = StudentEnrollment.objects.filter(
            class_obj=instance.class_obj,
            status='active'
        ).count()
        instance.class_obj.current_enrollment = active_enrollments
        instance.class_obj.save()


@receiver(post_save, sender=StudentEnrollment)
def log_enrollment_change(sender, instance, created, **kwargs):
    """Log enrollment changes"""
    action = "created" if created else "updated"
    student_name = instance.student.get_full_name() if instance.student else "Unknown"
    logger.info(f"Student enrollment {action} for {student_name} in {instance.class_obj.name}")


# ============================================
# Connect Signals
# ============================================

def connect_signals():
    """Connect all signals"""
    # Signals are automatically connected via @receiver decorators
    pass


def disconnect_signals():
    """Disconnect all signals"""
    from django.db.models import signals

    signals.pre_save.disconnect(validate_academic_session, sender=AcademicSession)
    signals.post_save.disconnect(log_academic_session_change, sender=AcademicSession)

    signals.pre_save.disconnect(validate_academic_term, sender=AcademicTerm)
    signals.post_save.disconnect(log_academic_term_change, sender=AcademicTerm)

    signals.pre_save.disconnect(generate_class_codes, sender=Class)
    signals.pre_save.disconnect(validate_class_teacher, sender=Class)
    signals.post_save.disconnect(log_class_change, sender=Class)

    signals.pre_save.disconnect(validate_class_subject, sender=ClassSubject)
    signals.post_save.disconnect(update_teacher_workload, sender=ClassSubject)
    signals.pre_delete.disconnect(decrease_teacher_workload, sender=ClassSubject)

    signals.pre_save.disconnect(generate_timetable_code, sender=Timetable)
    signals.post_save.disconnect(log_timetable_change, sender=Timetable)

    signals.pre_save.disconnect(validate_timetable_entry, sender=TimetableEntry)

    signals.pre_save.disconnect(generate_enrollment_number, sender=StudentEnrollment)
    signals.post_save.disconnect(update_class_enrollment_count, sender=StudentEnrollment)
    signals.post_save.disconnect(log_enrollment_change, sender=StudentEnrollment)