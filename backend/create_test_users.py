#!/usr/bin/env python
"""
Script to create test users for the school management system.
Run with: python create_test_users.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from users.models import User

def create_test_users():
    """Create test users for different roles"""
    
    test_users = [
        # Head of School/Admin
        {
            'registration_number': 'admi1234',
            'email': 'admin@school.edu',
            'password': 'Admin123!',
            'first_name': 'School',
            'last_name': 'Admin',
            'role': 'head',
            'phone_number': '08011111111',
            'is_staff': True,
            'is_superuser': True,
        },
        # Principal
        {
            'registration_number': 'prin5678',
            'email': 'principal@school.edu',
            'password': 'Principal123',
            'first_name': 'John',
            'last_name': 'Principal',
            'role': 'principal',
            'phone_number': '08022222222',
            'is_staff': True,
        },
        # Teacher
        {
            'registration_number': 'teac9012',
            'email': 'teacher@school.edu',
            'password': 'Teacher123',
            'first_name': 'Sarah',
            'last_name': 'Teacher',
            'role': 'teacher',
            'phone_number': '08033333333',
            'subject_specialization': 'Mathematics',
            'qualification': 'B.Sc Education',
        },
        # Student
        {
            'registration_number': 'stud3456',
            'email': 'student@school.edu',
            'password': 'Student123',
            'first_name': 'Michael',
            'last_name': 'Student',
            'role': 'student',
            'phone_number': '08044444444',
            'gender': 'male',
            'date_of_birth': '2008-05-15',
            'current_class': 'JSS 2A',
        },
        # Parent
        {
            'registration_number': 'pare7890',
            'email': 'parent@school.edu',
            'password': 'Parent123',
            'first_name': 'David',
            'last_name': 'Parent',
            'role': 'parent',
            'phone_number': '08055555555',
        },
        # Accountant
        {
            'registration_number': 'acco1234',
            'email': 'accountant@school.edu',
            'password': 'Accountant123',
            'first_name': 'Grace',
            'last_name': 'Accountant',
            'role': 'accountant',
            'phone_number': '08066666666',
        },
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            # Check if user exists by registration number
            if User.objects.filter(registration_number=user_data['registration_number']).exists():
                print(f"User with registration {user_data['registration_number']} already exists")
                continue
            
            # Check if user exists by email
            if User.objects.filter(email=user_data['email']).exists():
                print(f"User with email {user_data['email']} already exists")
                continue
            
            # Create user
            user = User.objects.create_user(**user_data)
            created_users.append(user)
            print(f"Created user: {user.registration_number} ({user.role}) - Name: {user.get_full_name()}")
            
        except Exception as e:
            print(f"Error creating user {user_data.get('registration_number', 'unknown')}: {str(e)}")
    
    print(f"\nCreated {len(created_users)} test users")
    print("\nLogin credentials:")
    print("-" * 50)
    for user in created_users:
        print(f"Registration Number: {user.registration_number}")
        print(f"Email: {user.email}")
        print(f"Password: {test_users[created_users.index(user)]['password'] if created_users.index(user) < len(test_users) else 'unknown'}")
        print(f"Role: {user.get_role_display()}")
        print("-" * 30)

if __name__ == '__main__':
    create_test_users()