#!/usr/bin/env python
"""
Setup script for the Finance Assistant Django project.
This script helps initialize the project with migrations and sample data.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Run the setup process."""
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_assist.settings')
    django.setup()
    
    print("Setting up Finance Assistant Django Backend...")
    print("=" * 50)
    
    # Run migrations
    print("1. Running migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Populate data
    print("2. Populating initial data...")
    execute_from_command_line(['manage.py', 'populate_data'])
    
    print("=" * 50)
    print("Setup completed successfully!")
    print("You can now run: python manage.py runserver")
    print("The API will be available at: http://localhost:8000/api/")
    print("Admin interface at: http://localhost:8000/admin/")

if __name__ == '__main__':
    main()
