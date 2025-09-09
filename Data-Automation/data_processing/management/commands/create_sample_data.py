from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from data_processing.models import ExcelFile, Participant, Cohort
from email_system.models import EmailTemplate
import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Create sample data for testing the application'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create superuser if doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write('Created admin user (admin/admin123)')
        
        # Create sample Excel file
        sample_file = self.create_sample_excel_file()
        
        # Create sample participants
        self.create_sample_participants(sample_file)
        
        # Create sample cohorts
        self.create_sample_cohorts()
        
        # Create sample email templates
        self.create_sample_email_templates()
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))

    def create_sample_excel_file(self):
        """Create a sample Excel file with participant data"""
        # Create sample data
        data = {
            'ID': range(1, 21),
            'Start_time': [datetime.now() - timedelta(days=i) for i in range(20)],
            'Completion_time': [datetime.now() - timedelta(days=i, hours=2) for i in range(20)],
            'User_Email': [f'user{i}@example.com' for i in range(20)],
            'Name': [f'User {i}' for i in range(20)],
            'Last_modified_time': [datetime.now() - timedelta(days=i) for i in range(20)],
            'full_name': [f'John Doe {i}' for i in range(20)],
            'moodle_email': [f'john.doe{i}@gmail.com' for i in range(20)],
            'need_365': ['Yes' if i % 3 == 0 else 'No' for i in range(20)],
            'attending': ['Yes' if i % 2 == 0 else 'No' for i in range(20)],
            'alternative_dates': [f'2024-{i+1:02d}-15' if i % 2 == 1 else 'TBD' for i in range(20)],
            'postcode': [f'SW{i+1:02d} 1AA' for i in range(20)],
            'refugee_status': ['Yes' if i % 5 == 0 else 'No' for i in range(20)],
            'disabled_status': ['Yes' if i % 7 == 0 else 'No' for i in range(20)]
        }
        
        # Create temporary Excel file
        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False, engine='openpyxl')
        temp_file.close()
        
        # Create ExcelFile record
        excel_file = ExcelFile.objects.create(
            name='sample_data.xlsx',
            file=temp_file.name,
            status='processed',
            participant_count=20,
            uploaded_by=User.objects.get(username='admin')
        )
        
        return excel_file

    def create_sample_participants(self, excel_file):
        """Create sample participants"""
        participants_data = [
            {
                'full_name': f'John Doe {i}',
                'email': f'john.doe{i}@gmail.com',
                'email_valid': True,
                'attending': 'Yes' if i % 2 == 0 else 'No',
                'alternative_dates': f'2024-{i+1:02d}-15' if i % 2 == 1 else 'TBD',
                'need_365': 'Yes' if i % 3 == 0 else 'No',
                'postcode': f'SW{i+1:02d} 1AA',
                'refugee_status': 'Yes' if i % 5 == 0 else 'No',
                'disabled_status': 'Yes' if i % 7 == 0 else 'No',
                'source_file': excel_file
            }
            for i in range(20)
        ]
        
        for data in participants_data:
            Participant.objects.create(**data)

    def create_sample_cohorts(self):
        """Create sample cohorts"""
        cohorts_data = [
            {
                'name': 'Primary Cohort',
                'cohort_type': 'primary',
                'description': 'Students attending original course dates',
            },
            {
                'name': 'Alternative Cohort',
                'cohort_type': 'alternative',
                'description': 'Students needing different scheduling',
            },
            {
                'name': 'Need Software Setup',
                'cohort_type': 'need_software',
                'description': 'Participants requiring MS Office 365 installation',
            },
            {
                'name': 'High Support Group',
                'cohort_type': 'high_support',
                'description': 'Refugees, disabled, or participants needing extra assistance',
            },
        ]
        
        for data in cohorts_data:
            cohort = Cohort.objects.create(**data)
            # Assign some participants to cohorts
            if cohort.cohort_type == 'primary':
                participants = Participant.objects.filter(attending__icontains='yes')[:5]
                cohort.participants.set(participants)
            elif cohort.cohort_type == 'alternative':
                participants = Participant.objects.filter(attending__icontains='no')[:5]
                cohort.participants.set(participants)

    def create_sample_email_templates(self):
        """Create sample email templates"""
        templates_data = [
            {
                'name': 'Primary Cohort Welcome',
                'template_type': 'primary_cohort',
                'subject': 'Welcome to the Primary Cohort - Course Starting Soon!',
                'body': '''Dear {name},

🎉 Welcome to the Primary Cohort!

We're excited to confirm your participation in our upcoming course. You've been assigned to the Primary Cohort, which means you'll be attending the original scheduled dates.

📋 YOUR COURSE DETAILS:
• Course: Data Analysis Fundamentals
• Start Date: March 15, 2024
• Your email: {email}
• Software status: {software_status}

📅 NEXT STEPS:
1. Check your email regularly for updates
2. Prepare your learning environment
3. Contact us if you have any questions

We look forward to working with you!

Best regards,
Course Coordination Team

---
This is an automated message from the Data Automation System.
Reference: PRIMARY-{timestamp}''',
                'created_by': User.objects.get(username='admin')
            },
            {
                'name': 'Alternative Dates Coordination',
                'template_type': 'alternative_cohort',
                'subject': 'Alternative Dates Available - Let\'s Find the Right Time',
                'body': '''Dear {name},

📅 Alternative Dates Coordination

Thank you for your interest in our course! We understand that the original dates don't work for you, so we're reaching out to coordinate alternative scheduling.

📋 YOUR PREFERENCES:
• Your email: {email}
• Alternative dates: {alternative_dates}
• Software status: {software_status}

🔄 NEXT STEPS:
1. We'll contact you with available alternative dates
2. Please respond with your preferred options
3. We'll confirm your new schedule

Thank you for your flexibility!

Best regards,
Course Coordination Team

---
This is an automated message from the Data Automation System.
Reference: ALTERNATIVE-{timestamp}''',
                'created_by': User.objects.get(username='admin')
            },
            {
                'name': 'Software Setup Instructions',
                'template_type': 'need_software_setup',
                'subject': 'Software Setup Required - MS Office 365 Installation',
                'body': '''Dear {name},

💻 Software Setup Required

You've been identified as needing MS Office 365 for the course. Please follow these setup instructions before the course begins.

📋 SOFTWARE REQUIREMENTS:
• MS Office 365 (required)
• Your email: {email}
• Setup deadline: Before course start

🛠️ INSTALLATION STEPS:
1. Download MS Office 365 from the official website
2. Install using your provided license key
3. Test all applications before the course
4. Contact support if you encounter issues

📞 NEED HELP?
Our technical support team is available to assist you with the installation process.

Best regards,
Course Coordination Team

---
This is an automated message from the Data Automation System.
Reference: SOFTWARE-{timestamp}''',
                'created_by': User.objects.get(username='admin')
            }
        ]
        
        for data in templates_data:
            EmailTemplate.objects.create(**data)
