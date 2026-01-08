# create_test.py - COMPLETELY ERROR-FREE VERSION
import os
import sys
import django
import random
from datetime import datetime, timedelta
from faker import Faker

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from users.models import User
from academic.models import (
    AcademicSession, AcademicTerm, Program, ClassLevel,
    Subject, Class, ClassSubject, Timetable, TimetableEntry
)
from students.models import Student, StudentEnrollment
from staff.models import Staff, TeacherProfile, StaffAttendance, StaffPermission
from parents.models import Parent

fake = Faker()


def create_test_data():
    """
    Create comprehensive test data for the School Management System
    """
    print("=" * 60)
    print("CREATING TEST DATA FOR SCHOOL MANAGEMENT SYSTEM")
    print("=" * 60)

    try:
        # Clear existing data first to avoid conflicts
        print("\n[1/15] Clearing existing data...")
        clear_existing_data()

        # Use transaction to rollback if any error occurs
        with transaction.atomic():
            # 1. First create users (required for all other models)
            print("\n[2/15] Creating users...")
            users = create_users()

            # 2. Create academic structure
            print("\n[3/15] Creating academic structure...")
            academic_session = create_academic_session()
            academic_term = create_academic_term(academic_session)
            programs = create_programs()
            class_levels = create_class_levels(programs)
            subjects = create_subjects(programs, class_levels)

            # 3. Create staff with their profiles
            print("\n[4/15] Creating staff...")
            staff_members = create_staff(users['staff_users'])
            teacher_profiles = create_teacher_profiles(staff_members)

            # 4. Create classes
            print("\n[5/15] Creating classes...")
            classes = create_classes(academic_session, academic_term, class_levels)

            # 5. Create students
            print("\n[6/15] Creating students...")
            students = create_students(users['student_users'], class_levels)

            # 6. Create parents
            print("\n[7/15] Creating parents...")
            parents = create_parents(users['parent_users'])

            # 7. Link students with parents
            print("\n[8/15] Linking students with parents...")
            link_students_with_parents(students, parents)

            # 8. Update teacher assignments BEFORE creating class subjects
            print("\n[9/15] Updating teacher assignments...")
            update_teacher_assignments_for_subjects(teacher_profiles, subjects)

            # 9. Assign class teachers
            print("\n[10/15] Assigning class teachers...")
            assign_class_teachers(classes, staff_members)

            # 10. Create class-subject assignments
            print("\n[11/15] Creating class-subject assignments...")
            class_subjects = create_class_subjects(classes, subjects, teacher_profiles)

            # 11. Create student enrollments
            print("\n[12/15] Creating student enrollments...")
            student_enrollments = create_student_enrollments(students, classes, academic_session, academic_term)

            # 12. Create timetables
            print("\n[13/15] Creating timetables...")
            if classes:
                timetable = create_timetable(academic_session, academic_term, classes[0])
                timetable_entries = create_timetable_entries(timetable, class_subjects)

            # 13. Create staff attendance (optional)
            print("\n[14/15] Creating staff attendance...")
            staff_attendance = create_staff_attendance(staff_members)

            # 14. Create staff permissions
            print("\n[15/15] Creating staff permissions...")
            staff_permissions = create_staff_permissions(staff_members)

        print("\n" + "=" * 60)
        print("✅ TEST DATA CREATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📊 SUMMARY:")
        print(f"   👥 Users: {len(users['all_users'])}")
        print(f"   👩‍🏫 Staff: {len(staff_members)}")
        print(f"   👨‍🏫 Teacher Profiles: {len(teacher_profiles)}")
        print(f"   🧑‍🎓 Students: {len(students)}")
        print(f"   👨‍👩‍👧‍👦 Parents: {len(parents)}")
        print(f"   🏫 Classes: {len(classes)}")
        print(f"   📚 Subjects: {len(subjects)}")
        print(f"   📝 Class-Subject Assignments: {len(class_subjects)}")
        print(f"   📅 Student Enrollments: {len(student_enrollments)}")
        print("=" * 60)
        print("\n🔑 DEFAULT LOGIN CREDENTIALS:")
        print("   Superuser: head@school.edu.ng / password123")
        print("   All users: Use registration number as username, password: password123")
        print("\n💡 TIP: You can now run 'python manage.py runserver' to start the application.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR OCCURRED: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Run migrations: python manage.py migrate")
        print("   2. Install Faker: pip install Faker")
        print("   3. Check database connection")
        print("   4. Clear existing data manually if needed")


def clear_existing_data():
    """Clear all existing data to avoid conflicts"""
    # Delete in reverse order to avoid foreign key constraints
    try:
        TimetableEntry.objects.all().delete()
    except:
        pass

    try:
        Timetable.objects.all().delete()
    except:
        pass

    try:
        ClassSubject.objects.all().delete()
    except:
        pass

    try:
        StudentEnrollment.objects.all().delete()
    except:
        pass

    try:
        Class.objects.all().delete()
    except:
        pass

    try:
        Student.objects.all().delete()
    except:
        pass

    try:
        Parent.objects.all().delete()
    except:
        pass

    try:
        StaffPermission.objects.all().delete()
    except:
        pass

    try:
        StaffAttendance.objects.all().delete()
    except:
        pass

    try:
        TeacherProfile.objects.all().delete()
    except:
        pass

    try:
        Staff.objects.all().delete()
    except:
        pass

    try:
        Subject.objects.all().delete()
    except:
        pass

    try:
        ClassLevel.objects.all().delete()
    except:
        pass

    try:
        Program.objects.all().delete()
    except:
        pass

    try:
        AcademicTerm.objects.all().delete()
    except:
        pass

    try:
        AcademicSession.objects.all().delete()
    except:
        pass

    # Delete all users except superusers
    try:
        User = get_user_model()
        User.objects.filter(is_superuser=False).delete()
    except:
        pass


def create_users():
    """Create test users with different roles"""
    User = get_user_model()

    # Define user roles with counts
    roles_distribution = {
        'head': 1,
        'principal': 1,
        'vice_principal': 2,
        'teacher': 3,
        'form_teacher': 2,
        'subject_teacher': 3,
        'student': 10,  # Reduced for stability
        'parent': 8,  # Reduced for stability
        'accountant': 1,
        'secretary': 1,
        'librarian': 1,
        'laboratory': 1,
        'security': 1,
        'cleaner': 1
    }

    all_users = []
    staff_users = []
    student_users = []
    parent_users = []

    # Nigerian names
    nigerian_first_names = ['Chinonso', 'Adeola', 'Chiamaka', 'Oluwatobi', 'Ifeanyi',
                            'Ngozi', 'Chinedu', 'Adebayo', 'Folake', 'Emeka']

    nigerian_last_names = ['Adeyemi', 'Okafor', 'Chukwu', 'Mohammed', 'Okoro',
                           'Aliyu', 'Eze', 'Bello', 'Adebisi', 'Ogunleye']

    # Create superuser (Head of School)
    try:
        superuser = User.objects.create_superuser(
            email='head@school.edu.ng',
            first_name='Admin',
            last_name='School',
            password='password123',
            role='head',
            gender='male',
            date_of_birth=datetime(1975, 5, 15).date(),
            phone_number='08012345678',
            address='123 School Road, Lagos',
            city='Lagos',
            state_of_origin='lagos',
            lga='Lagos Island',
            is_verified=True
        )
        all_users.append(superuser)
        staff_users.append(superuser)
        print("   ✓ Created superuser: head@school.edu.ng")
    except:
        superuser = User.objects.get(email='head@school.edu.ng')
        all_users.append(superuser)
        staff_users.append(superuser)
        print("   ✓ Using existing superuser")

    # Track used emails
    used_emails = {'head@school.edu.ng'}

    # Create users for each role
    for role, count in roles_distribution.items():
        if role == 'head':  # Skip as we already created it
            continue

        for i in range(count):
            first_name = random.choice(nigerian_first_names)
            last_name = random.choice(nigerian_last_names)

            # Create unique email
            email_suffix = 1
            email = f"{first_name.lower()}.{last_name.lower()}{email_suffix}@school.edu.ng"

            while email in used_emails:
                email_suffix += 1
                email = f"{first_name.lower()}.{last_name.lower()}{email_suffix}@school.edu.ng"

            used_emails.add(email)

            # Create user based on role
            user_data = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'password': 'password123',
                'role': role,
                'gender': random.choice(['male', 'female']),
                'date_of_birth': fake.date_of_birth(minimum_age=22,
                                                    maximum_age=65) if role != 'student' else fake.date_of_birth(
                    minimum_age=5, maximum_age=18),
                'phone_number': f'080{random.randint(10000000, 99999999)}',
                'address': fake.address(),
                'city': fake.city(),
                'state_of_origin': random.choice(['lagos', 'abuja', 'oyo', 'rivers']),
                'lga': fake.city(),
                'is_verified': True
            }

            try:
                if role in ['student', 'parent']:
                    user = User.objects.create_user(**user_data)
                else:
                    user = User.objects.create_user(**user_data)

                all_users.append(user)

                if role in ['student']:
                    student_users.append(user)
                elif role in ['parent']:
                    parent_users.append(user)
                else:
                    staff_users.append(user)

                print(f"   ✓ Created {role}: {email}")

            except Exception as e:
                print(f"   ⚠️ Warning creating user {email}: {str(e)}")
                continue

    return {
        'all_users': all_users,
        'staff_users': staff_users,
        'student_users': student_users,
        'parent_users': parent_users
    }


def create_academic_session():
    """Create academic session"""
    current_year = datetime.now().year
    session = AcademicSession.objects.create(
        name=f"{current_year - 1}/{current_year} Academic Session",
        start_date=datetime(current_year - 1, 9, 1).date(),
        end_date=datetime(current_year, 8, 31).date(),
        is_current=True,
        status='active',
        description="Current academic session for testing"
    )
    return session


def create_academic_term(academic_session):
    """Create academic term"""
    term = AcademicTerm.objects.create(
        session=academic_session,
        term='first',
        name=f"First Term {academic_session.name}",
        start_date=datetime(academic_session.start_date.year, 9, 1).date(),
        end_date=datetime(academic_session.start_date.year, 12, 20).date(),
        is_current=True,
        status='active',
        total_school_days=90,
        total_teaching_weeks=13,
        holiday_weeks=2,
        examination_weeks=2,
        description="First term of the academic session"
    )
    return term


def create_programs():
    """Create academic programs"""
    programs = []
    program_data = [
        ('pre_school', 'Pre-School Program', 'PRE'),
        ('primary', 'Primary School Program', 'PRI'),
        ('junior_secondary', 'Junior Secondary Program', 'JSS'),
        ('senior_secondary', 'Senior Secondary Program', 'SSS')
    ]

    for program_type, name, code in program_data:
        program = Program.objects.create(
            name=name,
            program_type=program_type,
            code=code,
            description=f"{name} following Nigerian curriculum",
            duration_years=3 if 'secondary' in program_type else 6,
            curriculum="Nigerian Curriculum",
            is_active=True
        )
        programs.append(program)
        print(f"   ✓ Created program: {name}")

    return programs


def create_class_levels(programs):
    """Create class levels for each program"""
    class_levels = []

    # Define levels for each program
    program_levels = {
        'pre_school': [
            ('nursery_1', 'Nursery 1', 3, 4),
            ('nursery_2', 'Nursery 2', 4, 5),
        ],
        'primary': [
            ('primary_1', 'Primary 1', 6, 7),
            ('primary_2', 'Primary 2', 7, 8),
            ('primary_3', 'Primary 3', 8, 9),
        ],
        'junior_secondary': [
            ('jss_1', 'JSS 1', 12, 13),
            ('jss_2', 'JSS 2', 13, 14),
        ],
        'senior_secondary': [
            ('sss_1', 'SSS 1', 15, 16),
            ('sss_2', 'SSS 2', 16, 17),
        ]
    }

    for program in programs:
        levels = program_levels.get(program.program_type, [])
        for order, (level_code, level_name, min_age, max_age) in enumerate(levels, 1):
            class_level = ClassLevel.objects.create(
                program=program,
                level=level_code,
                name=level_name,
                code=f"{program.code}{order}",
                order=order,
                min_age=min_age,
                max_age=max_age,
                is_promotion_level=level_code in ['nursery_2', 'primary_3', 'jss_2', 'sss_2'],
                is_active=True,
                description=f"{level_name} level"
            )
            class_levels.append(class_level)
            print(f"   ✓ Created class level: {level_name} in {program.name}")

    return class_levels


def create_subjects(programs, class_levels):
    """Create subjects for the school"""
    subjects = []

    # Core subjects that every teacher can teach
    core_subjects_data = [
        ('English Language', 'ENG001', 'ENG', 'core'),
        ('Mathematics', 'MAT001', 'MATH', 'core'),
        ('Basic Science', 'SCI001', 'BSCI', 'science'),
        ('Social Studies', 'SOC001', 'SSTU', 'arts'),
        ('Religious Studies', 'REL001', 'RELG', 'religious'),
    ]

    # Additional subjects
    additional_subjects_data = [
        ('Physics', 'PHY001', 'PHY', 'science'),
        ('Chemistry', 'CHE001', 'CHEM', 'science'),
        ('Biology', 'BIO001', 'BIO', 'science'),
        ('Economics', 'ECO001', 'ECON', 'commercial'),
        ('Commerce', 'CMR001', 'COMM', 'commercial'),
        ('Accounting', 'ACC001', 'ACC', 'commercial'),
        ('Literature in English', 'LIT001', 'LIT', 'arts'),
        ('Government', 'GOV001', 'GOV', 'arts'),
        ('Geography', 'GEO001', 'GEO', 'arts'),
        ('French', 'FRE001', 'FRE', 'language'),
    ]

    all_subjects_data = core_subjects_data + additional_subjects_data

    for name, code, short_name, subject_type in all_subjects_data:
        # Check if subject already exists
        if Subject.objects.filter(code=code).exists():
            subject = Subject.objects.get(code=code)
        else:
            subject = Subject.objects.create(
                name=name,
                code=code,
                short_name=short_name,
                subject_type=subject_type,
                stream='general',
                curriculum="WAEC/NECO",
                periods_per_week=random.randint(3, 6),
                minutes_per_period=40,
                has_continuous_assessment=True,
                ca_weight=30,
                exam_weight=70,
                is_compulsory=subject_type == 'core',
                is_examinable=True,
                is_practical=subject_type in ['science', 'technical'],
                is_active=True,
                description=f"{name} subject"
            )
            print(f"   ✓ Created subject: {name}")

        # Assign to ALL programs and class levels (simplified for testing)
        for program in programs:
            subject.programs.add(program)

        for class_level in class_levels:
            subject.class_levels.add(class_level)

        subjects.append(subject)

    return subjects


def create_classes(academic_session, academic_term, class_levels):
    """Create classes for each class level"""
    classes = []

    for class_level in class_levels:
        class_obj = Class.objects.create(
            session=academic_session,
            term=academic_term,
            class_level=class_level,
            name=f"{class_level.name} A",
            code=f"{class_level.code}A",
            max_capacity=30,
            current_enrollment=0,
            room_number=f"RM{random.randint(101, 199)}",
            building='Main Building',
            floor='Ground Floor',
            stream='general',
            status='active',
            is_active=True,
            start_date=academic_term.start_date,
            end_date=academic_term.end_date,
            description=f"{class_level.name} class"
        )
        classes.append(class_obj)
        print(f"   ✓ Created class: {class_obj.name}")

    return classes


def create_staff(users):
    """Create staff profiles for staff users"""
    staff_members = []

    for user in users:
        # Skip if user is already linked to a staff profile
        if hasattr(user, 'staff_profile'):
            staff_members.append(user.staff_profile)
            continue

        # Determine department based on role
        department_map = {
            'head': 'administration',
            'principal': 'administration',
            'vice_principal': 'administration',
            'teacher': 'academic',
            'form_teacher': 'academic',
            'subject_teacher': 'academic',
            'accountant': 'finance',
            'secretary': 'administration',
            'librarian': 'library',
            'laboratory': 'laboratory',
            'security': 'security',
            'cleaner': 'maintenance'
        }

        # Generate staff ID
        staff_id = f"STF{random.randint(100000, 999999)}"

        staff = Staff.objects.create(
            user=user,
            staff_id=staff_id,
            employment_date=fake.date_between(start_date='-5y', end_date='today'),
            employment_type='full_time',
            department=department_map.get(user.role, 'none'),
            highest_qualification=random.choice(['B.Sc', 'B.Ed', 'M.Ed']),
            qualification_institution=random.choice(['University of Lagos', 'University of Ibadan']),
            year_of_graduation=random.randint(2010, 2020),
            professional_certifications="TRCN Certified" if user.role in ['teacher', 'form_teacher',
                                                                          'subject_teacher'] else "",
            trcn_number=f"TRCN/{random.randint(10000, 99999)}" if user.role in ['teacher', 'form_teacher',
                                                                                'subject_teacher'] else "",
            specialization=random.choice(['Mathematics', 'English', 'Science']),
            bank_name=random.choice(['First Bank', 'GTBank', 'Zenith Bank']),
            account_name=f"{user.first_name} {user.last_name}",
            account_number=str(random.randint(1000000000, 9999999999)),
            basic_salary=random.randint(150000, 400000),
            salary_scale=random.choice(['CONPASS 10', 'CONPASS 12']),
            annual_leave_days=21,
            leave_days_taken=random.randint(0, 5),
            next_of_kin_name=fake.name(),
            next_of_kin_relationship=random.choice(['Spouse', 'Sibling']),
            next_of_kin_phone=f'080{random.randint(10000000, 99999999)}',
            next_of_kin_address=fake.address(),
            blood_group=random.choice(['A+', 'B+', 'O+']),
            genotype=random.choice(['AA', 'AS']),
            medical_conditions="None",
            is_active=True,
            is_retired=False,
            performance_rating=round(random.uniform(3.5, 5.0), 1),
            last_appraisal_date=fake.date_between(start_date='-1y', end_date='today')
        )
        staff_members.append(staff)
        print(f"   ✓ Created staff: {user.get_full_name()} ({user.role})")

    return staff_members


def create_teacher_profiles(staff_members):
    """Create teacher profiles for teaching staff"""
    teacher_profiles = []

    for staff in staff_members:
        if staff.user.role in ['teacher', 'form_teacher', 'subject_teacher',
                               'head', 'principal', 'vice_principal']:
            teacher_type_map = {
                'head': 'head',
                'principal': 'principal',
                'vice_principal': 'vice_principal_academic',
                'form_teacher': 'class_teacher',
                'teacher': 'subject_teacher',
                'subject_teacher': 'subject_teacher'
            }

            teacher_profile = TeacherProfile.objects.create(
                staff=staff,
                teacher_type=teacher_type_map.get(staff.user.role, 'subject_teacher'),
                stream_specialization=random.choice(['science', 'commercial', 'arts', 'general']),
                max_periods_per_week=40,
                current_periods_per_week=random.randint(20, 35),
                years_of_experience=random.randint(1, 15),
                previous_schools='Previous teaching experience',
                workshops_attended='Professional development workshops',
                has_teaching_materials=True,
                teaching_materials_description="Standard teaching materials"
            )
            teacher_profiles.append(teacher_profile)
            print(f"   ✓ Created teacher profile: {staff.user.get_full_name()}")

    return teacher_profiles


def create_students(users, class_levels):
    """Create student profiles"""
    students = []

    # Get primary and secondary class levels
    primary_levels = [cl for cl in class_levels if cl.program.program_type == 'primary']
    secondary_levels = [cl for cl in class_levels if 'secondary' in cl.program.program_type]

    for user in users:
        # Determine appropriate class level based on age
        if user.date_of_birth:
            age = timezone.now().year - user.date_of_birth.year
            if age < 10:
                class_level = random.choice(primary_levels) if primary_levels else random.choice(class_levels)
            else:
                class_level = random.choice(secondary_levels) if secondary_levels else random.choice(class_levels)
        else:
            class_level = random.choice(class_levels)

        # Generate fee amount
        total_fee = random.randint(50000, 250000)
        amount_paid = random.randint(0, total_fee)

        student = Student.objects.create(
            user=user,
            class_level=class_level,
            stream='none',
            admission_date=fake.date_between(start_date='-2y', end_date='today'),
            house=random.choice(['red', 'blue', 'green', 'none']),
            previous_class='Previous class',
            previous_school='Previous School',
            is_prefect=random.choice([True, False]),
            prefect_role='Class Prefect' if random.choice([True, False]) else '',
            student_category=random.choice(['day', 'boarding']),
            emergency_contact_name=fake.name(),
            emergency_contact_phone=f'080{random.randint(10000000, 99999999)}',
            emergency_contact_relationship='Parent',
            fee_status='paid_full' if amount_paid >= total_fee else 'paid_partial' if amount_paid > 0 else 'not_paid',
            total_fee_amount=total_fee,
            amount_paid=amount_paid,
            balance_due=total_fee - amount_paid,
            last_payment_date=fake.date_between(start_date='-30d', end_date='today') if amount_paid > 0 else None,
            average_score=round(random.uniform(50.0, 95.0), 2),
            overall_grade=random.choice(['A', 'B', 'C']),
            position_in_class=random.randint(1, 30),
            blood_group=random.choice(['A+', 'B+', 'O+']),
            genotype=random.choice(['AA', 'AS']),
            medical_conditions="None",
            allergies="None",
            transportation_mode=random.choice(['school_bus', 'parent_drop']),
            is_active=True,
            is_graduated=False,
            days_present=random.randint(60, 90),
            days_absent=random.randint(0, 10),
            days_late=random.randint(0, 5)
        )
        students.append(student)
        print(f"   ✓ Created student: {user.get_full_name()} in {class_level.name}")

    return students


def create_parents(users):
    """Create parent profiles"""
    parents = []

    for user in users:
        parent = Parent.objects.create(
            user=user,
            parent_type=random.choice(['father', 'mother']),
            occupation=random.choice(['Teacher', 'Engineer', 'Doctor', 'Business Owner']),
            employer=random.choice(['Company Ltd', 'Self-employed', 'Government']),
            marital_status=random.choice(['married', 'single']),
            emergency_contact_name=fake.name(),
            emergency_contact_phone=f'080{random.randint(10000000, 99999999)}',
            emergency_contact_relationship='Friend',
            preferred_communication='whatsapp',
            receive_sms_alerts=True,
            receive_email_alerts=True,
            annual_income_range=random.choice(['500k_1m', '1m_3m']),
            bank_name=random.choice(['First Bank', 'GTBank']),
            account_name=f"{user.first_name} {user.last_name}",
            account_number=str(random.randint(1000000000, 9999999999)),
            is_pta_member=random.choice([True, False]),
            is_active=True,
            is_verified=True
        )
        parents.append(parent)
        print(f"   ✓ Created parent: {user.get_full_name()}")

    return parents


def link_students_with_parents(students, parents):
    """Link students with parents (each student gets 1-2 parents)"""
    print(f"   Linking {len(students)} students with {len(parents)} parents...")

    # Make sure we have enough parents
    if len(parents) < len(students):
        print(f"   ⚠️ Warning: Not enough parents ({len(parents)}) for students ({len(students)})")

    for i, student in enumerate(students):
        # Assign father (if available)
        if i < len(parents):
            father_candidate = parents[i]
            if father_candidate.parent_type in ['father', 'guardian']:
                student.father = father_candidate
            elif father_candidate.parent_type == 'mother':
                # Find a father candidate
                for parent in parents:
                    if parent.parent_type in ['father', 'guardian']:
                        student.father = parent
                        break

        # Assign mother (if available)
        if i + 1 < len(parents):
            mother_candidate = parents[i + 1]
            if mother_candidate.parent_type == 'mother':
                student.mother = mother_candidate
            else:
                # Find a mother candidate
                for parent in parents:
                    if parent.parent_type == 'mother':
                        student.mother = parent
                        break

        student.save()
        print(f"   ✓ Linked student {student.user.get_full_name()} with parents")


def update_teacher_assignments_for_subjects(teacher_profiles, subjects):
    """Update teacher assignments with subjects they can teach"""
    # Core subjects that every teacher can teach
    core_subjects = [s for s in subjects if s.subject_type == 'core']

    for teacher_profile in teacher_profiles:
        # Assign ALL core subjects to every teacher (simplified for testing)
        teacher_profile.subjects.set(core_subjects)

        # Assign 2-3 additional subjects
        additional_subjects = [s for s in subjects if s.subject_type != 'core']
        if additional_subjects:
            num_additional = min(random.randint(2, 3), len(additional_subjects))
            selected_additional = random.sample(additional_subjects, num_additional)
            teacher_profile.subjects.add(*selected_additional)

        print(f"   ✓ Assigned subjects to teacher: {teacher_profile.staff.user.get_full_name()}")


def assign_class_teachers(classes, staff_members):
    """Assign class teachers to classes"""
    teachers = [s for s in staff_members if
                s.user.role in ['teacher', 'form_teacher', 'head', 'principal', 'vice_principal']]

    for class_obj in classes:
        if teachers:
            class_teacher = random.choice(teachers)
            class_obj.class_teacher = class_teacher.user
            class_obj.save()
            print(f"   ✓ Assigned class teacher to {class_obj.name}: {class_teacher.user.get_full_name()}")


def create_class_subjects(classes, subjects, teacher_profiles):
    """Create class-subject assignments"""
    class_subjects = []

    for class_obj in classes:
        # Get subjects appropriate for this class level
        class_level = class_obj.class_level
        suitable_subjects = [s for s in subjects if class_level in s.class_levels.all()]

        if not suitable_subjects:
            print(f"   ⚠️ No suitable subjects found for {class_obj.name}")
            continue

        # Assign 4-6 subjects to each class
        num_subjects = min(random.randint(4, 6), len(suitable_subjects))
        selected_subjects = random.sample(suitable_subjects, num_subjects)

        for subject in selected_subjects:
            # Find a teacher who can teach this subject
            qualified_teachers = []
            for teacher_profile in teacher_profiles:
                if subject in teacher_profile.subjects.all():
                    qualified_teachers.append(teacher_profile.staff.user)

            teacher = random.choice(qualified_teachers) if qualified_teachers else None

            try:
                class_subject = ClassSubject.objects.create(
                    class_obj=class_obj,
                    subject=subject,
                    teacher=teacher,
                    start_date=class_obj.start_date,
                    end_date=class_obj.end_date,
                    periods_per_week=subject.periods_per_week,
                    preferred_days='Monday, Wednesday, Friday',
                    is_active=True,
                    is_compulsory=subject.is_compulsory,
                    ca_required=subject.has_continuous_assessment,
                    exam_required=subject.is_examinable
                )
                class_subjects.append(class_subject)
                print(f"   ✓ Created class-subject: {class_obj.name} - {subject.name}")

            except ValidationError as e:
                print(f"   ⚠️ Skipping {subject.name} for {class_obj.name}: {str(e)}")
                continue

    return class_subjects


def create_student_enrollments(students, classes, academic_session, academic_term):
    """Create student enrollment records"""
    enrollments = []
    User = get_user_model()

    for student in students:
        # Find appropriate class for student
        class_level = student.class_level
        suitable_classes = [c for c in classes if c.class_level == class_level]

        if not suitable_classes:
            print(f"   ⚠️ No suitable class found for student {student.user.get_full_name()}")
            continue

        class_obj = random.choice(suitable_classes)

        # Generate enrollment number
        enrollment_number = f"ENR-{academic_session.start_date.year}-{class_obj.code}-{student.user.registration_number}"

        # Get staff users for enrolled_by and approved_by
        enrolled_by_user = User.objects.filter(role__in=['head', 'principal', 'secretary']).first()
        approved_by_user = User.objects.filter(role__in=['head', 'principal']).first()

        enrollment = StudentEnrollment.objects.create(
            student=student,
            class_obj=class_obj,
            session=academic_session,
            term=academic_term,
            enrollment_date=fake.date_between(start_date=academic_term.start_date, end_date='today'),
            enrollment_number=enrollment_number,
            status='active',
            is_repeating=False,
            is_promoted=False,
            days_present=random.randint(30, 60),
            days_absent=random.randint(0, 10),
            average_score=student.average_score,
            position=student.position_in_class,
            remarks='Good student',
            enrolled_by=enrolled_by_user,
            approved_by=approved_by_user
        )
        enrollments.append(enrollment)

        # Update class enrollment count
        class_obj.current_enrollment += 1
        class_obj.save()

        print(f"   ✓ Enrolled student: {student.user.get_full_name()} in {class_obj.name}")

    return enrollments


def create_timetable(academic_session, academic_term, class_obj):
    """Create a sample timetable"""
    timetable = Timetable.objects.create(
        name=f"{class_obj.name} Timetable",
        code=f"TT-{class_obj.code}",
        session=academic_session,
        term=academic_term,
        scope='class',
        class_obj=class_obj,
        days='monday,tuesday,wednesday,thursday,friday',
        periods_per_day=8,
        period_duration=40,
        break_periods='3,6',
        lunch_period=5,
        assembly_period=1,
        start_time=datetime.strptime('08:00', '%H:%M').time(),
        end_time=datetime.strptime('15:20', '%H:%M').time(),
        status='active',
        is_active=True,
        description=f"Timetable for {class_obj.name}"
    )
    print(f"   ✓ Created timetable for {class_obj.name}")
    return timetable


def create_timetable_entries(timetable, class_subjects):
    """Create timetable entries"""
    entries = []
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']

    # Get subjects for this class
    class_subjects_for_class = [cs for cs in class_subjects if cs.class_obj == timetable.class_obj]

    if not class_subjects_for_class:
        print(f"   ⚠️ No class subjects found for timetable")
        return entries

    for day in days:
        for period in range(1, timetable.periods_per_day + 1):
            entry_type = 'subject'
            subject = None
            teacher = None

            # Assembly in period 1
            if period == timetable.assembly_period:
                entry_type = 'assembly'
            # Break periods
            elif period in [3, 6]:
                entry_type = 'break'
            # Lunch period
            elif period == timetable.lunch_period:
                entry_type = 'lunch'
            else:
                # Assign subject for academic periods
                subject_index = (days.index(day) + period) % len(class_subjects_for_class)
                cs = class_subjects_for_class[subject_index]
                subject = cs.subject
                teacher = cs.teacher
                entry_type = 'subject'

            entry = TimetableEntry.objects.create(
                timetable=timetable,
                day=day,
                period_number=period,
                subject=subject,
                teacher=teacher,
                class_obj=timetable.class_obj,
                room=timetable.class_obj.room_number,
                entry_type=entry_type,
                is_active=True
            )
            entries.append(entry)

    print(f"   ✓ Created {len(entries)} timetable entries")
    return entries


def create_staff_attendance(staff_members):
    """Create staff attendance records"""
    attendance_records = []

    # Create attendance for 3 days
    for i in range(3):
        date = timezone.now().date() - timedelta(days=3 - i)

        for staff in staff_members[:3]:  # Only for first 3 staff
            status = 'present'
            check_in = datetime.combine(date, datetime.strptime(f"08:{random.randint(0, 30):02d}", "%H:%M").time())
            check_out = datetime.combine(date, datetime.strptime(f"16:{random.randint(0, 30):02d}", "%H:%M").time())
            hours = 8.0

            # Get a staff member to record the attendance
            recorded_by = random.choice([s for s in staff_members if s != staff])

            attendance = StaffAttendance.objects.create(
                staff=staff,
                date=date,
                status=status,
                check_in_time=check_in.time(),
                check_out_time=check_out.time(),
                hours_worked=hours,
                remarks='On time',
                recorded_by=recorded_by,
                is_verified=True
            )
            attendance_records.append(attendance)

    print(f"   ✓ Created {len(attendance_records)} staff attendance records")
    return attendance_records


def create_staff_permissions(staff_members):
    """Create staff permission profiles"""
    permissions_list = []

    for staff in staff_members:
        # Base permissions based on role
        is_admin = staff.user.role in ['head', 'principal', 'vice_principal']

        permissions = StaffPermission.objects.create(
            staff=staff,
            can_view_all_results=is_admin,
            can_edit_results=is_admin,
            can_approve_results=is_admin,
            can_generate_reports=is_admin,
            can_add_students=is_admin,
            can_edit_students=is_admin,
            can_view_all_students=True,
            can_add_parents=is_admin,
            can_edit_parents=is_admin,
            can_add_staff=is_admin,
            can_edit_staff=is_admin,
            can_view_all_staff=True,
            can_view_finances=is_admin,
            can_edit_finances=is_admin,
            can_generate_financial_reports=is_admin,
            can_manage_system_settings=is_admin,
            can_view_audit_logs=is_admin,
            can_manage_backups=is_admin,
            can_send_broadcast_messages=is_admin,
            can_send_individual_messages=True
        )
        permissions_list.append(permissions)

    print(f"   ✓ Created {len(permissions_list)} staff permission profiles")
    return permissions_list


if __name__ == '__main__':
    # Check for Faker
    try:
        from faker import Faker
    except ImportError:
        print("Installing required package: Faker")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "Faker"])
        from faker import Faker

    # Run migrations check
    print("Checking migrations...")
    try:
        os.system("python manage.py migrate --check")
    except:
        print("⚠️ Run migrations with: python manage.py migrate")

    create_test_data()