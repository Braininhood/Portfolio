from typing import Dict, List, Any
from .models import EmailTemplate
from data_processing.models import Cohort


class EmailTemplateGenerator:
    """Service for generating email templates based on cohort types"""
    
    def generate_templates_for_cohorts(self, cohort_ids: List[int] = None) -> Dict[str, Any]:
        """Generate email templates for specific cohorts or all cohorts"""
        if cohort_ids:
            cohorts = Cohort.objects.filter(id__in=cohort_ids)
        else:
            cohorts = Cohort.objects.all()
        
        if not cohorts.exists():
            return {'error': 'No cohorts found'}
        
        templates_created = []
        
        for cohort in cohorts:
            template = self._create_template_for_cohort(cohort)
            if template:
                templates_created.append(template)
        
        return {
            'templates_created': len(templates_created),
            'templates': [
                {
                    'id': template.id,
                    'name': template.name,
                    'subject': template.subject,
                    'template_type': template.template_type
                }
                for template in templates_created
            ],
            'status': 'success'
        }
    
    def _create_template_for_cohort(self, cohort: Cohort) -> EmailTemplate:
        """Create a specific email template for a cohort"""
        template_data = self._get_template_data_for_cohort_type(cohort.cohort_type)
        
        # Check if template already exists for this cohort type
        existing_template = EmailTemplate.objects.filter(
            name__icontains=template_data['name']
        ).first()
        
        if existing_template:
            return existing_template
        
        template = EmailTemplate.objects.create(
            name=template_data['name'],
            subject=template_data['subject'],
            body=template_data['body'],
            template_type=template_data['template_type']
        )
        
        return template
    
    def _get_template_data_for_cohort_type(self, cohort_type: str) -> Dict[str, Any]:
        """Get template data based on cohort type"""
        templates = {
            'primary': {
                'name': 'Course Confirmation - Confirmed Attendees',
                'subject': 'Welcome to the Course - Confirmation & Next Steps',
                'body': '''Dear {name},

Welcome to our course! We're excited to have you join us.

**Course Details:**
- Start Date: November 15, 2025
- Schedule: Mondays & Wednesdays, 6:00-8:00 PM
- Duration: 6 weeks
- Location: Online via Moodle

**Important Information:**
- Your email address ({email}) has been verified for Moodle access
- Software Status: {software_status}
- Cohort: {cohort_type}

**Next Steps:**
1. Check your email for Moodle login credentials
2. Complete the pre-course survey
3. Join our welcome session on November 10th

If you have any questions, please don't hesitate to contact us.

Best regards,
Course Team''',
                'template_type': 'confirmation'
            },
            'alternative': {
                'name': 'Alternative Schedule - Course Participants',
                'subject': 'Alternative Schedule Options - Course Participation',
                'body': '''Dear {name},

Thank you for your interest in our course. We understand that the current schedule doesn't work for you.

**Your Preferred Dates:**
{alternative_dates}

**What Happens Next:**
1. We'll review your availability
2. Contact you within 3 business days
3. Provide alternative options if available

**Current Course Details:**
- Start Date: November 15, 2025
- Schedule: Mondays & Wednesdays, 6:00-8:00 PM
- Duration: 6 weeks

We'll do our best to accommodate your schedule. In the meantime, you're on our waiting list for future courses.

Best regards,
Course Team''',
                'template_type': 'alternative'
            },
            'need_software': {
                'name': 'Software Setup Required - Office 365',
                'subject': 'Microsoft Office 365 Setup Required - Action Needed',
                'body': '''Dear {name},

You're enrolled in our course, but we need to set up Microsoft Office 365 for you.

**Why Office 365 is Required:**
- Course materials and assignments
- Collaborative projects
- Final assessments

**Setup Instructions:**
1. Check your email for Office 365 invitation
2. Follow the setup guide (attached)
3. Complete setup by November 12th
4. Contact support if you need help

**Support Available:**
- Technical support: tech@course.com
- Phone: 0800 123 456
- Office hours: Mon-Fri, 9 AM - 5 PM

**Your Course Details:**
- Start Date: November 15, 2025
- Software Status: {software_status}
- Cohort: {cohort_type}

Please complete the setup as soon as possible to ensure you're ready for the course.

Best regards,
Course Team''',
                'template_type': 'technical'
            },
            'software_ready': {
                'name': 'Software Ready - Course Preparation',
                'subject': 'You\'re All Set! - Course Preparation Complete',
                'body': '''Dear {name},

Great news! Your software setup is complete and you're ready for the course.

**What's Ready:**
✅ Microsoft Office 365 installed
✅ Email verified ({email})
✅ Moodle access configured
✅ Course materials available

**Course Reminders:**
- Start Date: November 15, 2025
- Schedule: Mondays & Wednesdays, 6:00-8:00 PM
- Duration: 6 weeks
- Cohort: {cohort_type}

**Before We Start:**
1. Test your Office 365 login
2. Explore the Moodle platform
3. Complete the pre-course survey
4. Join our welcome session on November 10th

You're all set! We look forward to seeing you in class.

Best regards,
Course Team''',
                'template_type': 'confirmation'
            },
            'high_support': {
                'name': 'Enhanced Support - Welcome & Resources',
                'subject': 'Welcome! Enhanced Support Available - Course Resources',
                'body': '''Dear {name},

Welcome to our course! We're committed to providing you with the support you need to succeed.

**Enhanced Support Available:**
- One-on-one technical assistance
- Extended office hours
- Additional learning resources
- Flexible assignment deadlines
- Peer support group

**Your Support Team:**
- Course Coordinator: coordinator@course.com
- Technical Support: tech@course.com
- Learning Support: learning@course.com

**Course Details:**
- Start Date: November 15, 2025
- Schedule: Mondays & Wednesdays, 6:00-8:00 PM
- Duration: 6 weeks
- Cohort: {cohort_type}

**Important:**
- Your email ({email}) is verified for Moodle access
- Software Status: {software_status}
- Support is available throughout the course

We're here to help you succeed. Don't hesitate to reach out with any questions or concerns.

Best regards,
Course Team''',
                'template_type': 'support'
            },
            'standard_support': {
                'name': 'Standard Support - Course Welcome',
                'subject': 'Welcome to the Course - Standard Support Available',
                'body': '''Dear {name},

Welcome to our course! We're excited to have you join us.

**Standard Support Available:**
- Technical support during office hours
- Online resources and tutorials
- Peer support through Moodle forums
- Regular check-ins with instructors

**Course Details:**
- Start Date: November 15, 2025
- Schedule: Mondays & Wednesdays, 6:00-8:00 PM
- Duration: 6 weeks
- Cohort: {cohort_type}

**Your Information:**
- Email: {email} (verified)
- Software Status: {software_status}

**Next Steps:**
1. Check your email for Moodle login credentials
2. Complete the pre-course survey
3. Join our welcome session on November 10th

If you need any assistance, our support team is here to help.

Best regards,
Course Team''',
                'template_type': 'welcome'
            },
            'moodle_ready': {
                'name': 'Moodle Access Ready - Course Access',
                'subject': 'Moodle Access Confirmed - Course Platform Ready',
                'body': '''Dear {name},

Your Moodle access is ready! You can now access the course platform.

**Moodle Access Details:**
- Email: {email} (verified)
- Platform: course.moodle.com
- Login: Use your email address
- Password: Check your email for credentials

**What You Can Do Now:**
1. Log into Moodle
2. Explore the course materials
3. Complete the pre-course survey
4. Join the welcome discussion forum

**Course Information:**
- Start Date: November 15, 2025
- Schedule: Mondays & Wednesdays, 6:00-8:00 PM
- Duration: 6 weeks
- Cohort: {cohort_type}

**Technical Support:**
- Email: tech@course.com
- Phone: 0800 123 456
- Office hours: Mon-Fri, 9 AM - 5 PM

You're all set! We look forward to seeing you in the virtual classroom.

Best regards,
Course Team''',
                'template_type': 'technical'
            },
            'email_correction': {
                'name': 'Email Verification Required - Action Needed',
                'subject': 'Email Verification Required - Please Update Your Information',
                'body': '''Dear {name},

We need to verify your email address to complete your course enrollment.

**Current Email Issue:**
The email address we have ({email}) appears to be invalid or incorrect.

**What You Need to Do:**
1. Reply to this email with your correct email address
2. Or contact us at: enrollment@course.com
3. Provide your full name and correct email
4. We'll update your information immediately

**Why This Matters:**
- Moodle access requires a valid email
- Course communications will be sent to your email
- Important updates and materials will be shared via email

**Course Details:**
- Start Date: November 15, 2025
- Schedule: Mondays & Wednesdays, 6:00-8:00 PM
- Duration: 6 weeks
- Cohort: {cohort_type}

**Contact Information:**
- Email: enrollment@course.com
- Phone: 0800 123 456
- Office hours: Mon-Fri, 9 AM - 5 PM

Please update your email address as soon as possible to ensure you don't miss any important course information.

Best regards,
Course Team''',
                'template_type': 'verification'
            }
        }
        
        return templates.get(cohort_type, {
            'name': f'General Course Communication - {cohort_type.title()}',
            'subject': 'Course Information - Important Update',
            'body': '''Dear {name},

This is an important update regarding your course enrollment.

**Course Details:**
- Start Date: November 15, 2025
- Schedule: Mondays & Wednesdays, 6:00-8:00 PM
- Duration: 6 weeks
- Cohort: {cohort_type}

**Your Information:**
- Email: {email}
- Software Status: {software_status}

If you have any questions, please contact us.

Best regards,
Course Team''',
            'template_type': 'general'
        })
    
    def generate_all_templates(self) -> Dict[str, Any]:
        """Generate templates for all cohort types"""
        cohort_types = [
            'primary', 'alternative', 'need_software', 'software_ready',
            'high_support', 'standard_support', 'moodle_ready', 'email_correction'
        ]
        
        templates_created = []
        
        for cohort_type in cohort_types:
            template_data = self._get_template_data_for_cohort_type(cohort_type)
            
            # Check if template already exists
            existing_template = EmailTemplate.objects.filter(
                name__icontains=template_data['name']
            ).first()
            
            if existing_template:
                templates_created.append(existing_template)
            else:
                template = EmailTemplate.objects.create(
                    name=template_data['name'],
                    subject=template_data['subject'],
                    body=template_data['body'],
                    template_type=template_data['template_type']
                )
                templates_created.append(template)
        
        return {
            'templates_created': len(templates_created),
            'templates': [
                {
                    'id': template.id,
                    'name': template.name,
                    'subject': template.subject,
                    'template_type': template.template_type
                }
                for template in templates_created
            ],
            'status': 'success'
        }
