import re
from datetime import datetime
from typing import Union


def validate_email(email: str) -> bool:
    """Check if email address is valid format"""
    if not email or email == 'anonymous':
        return False
        
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_date(date_str: Union[str, datetime]) -> bool:
    """Check if date string is valid"""
    if not date_str or str(date_str) in ['TBD', 'N/A', '']:
        return False
        
    try:
        # Try parsing common date formats
        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                datetime.strptime(str(date_str), fmt)
                return True
            except ValueError:
                continue
        return False
    except:
        return False


def clean_text(text: str) -> str:
    """Clean and normalize text data"""
    if not text:
        return ''
    
    # Remove extra whitespace
    text = ' '.join(str(text).split())
    
    # Convert to string and strip
    return str(text).strip()


def get_cohort_type(participant_data: dict) -> str:
    """Determine cohort type based on participant data"""
    attending = str(participant_data.get('attending', '')).lower()
    need_365 = str(participant_data.get('need_365', '')).lower()
    refugee_status = str(participant_data.get('refugee_status', '')).lower()
    disabled_status = str(participant_data.get('disabled_status', '')).lower()
    email_valid = participant_data.get('email_valid', False)
    
    # Main cohort
    if 'yes' in attending:
        main_cohort = "Primary_Cohort"
    else:
        main_cohort = "Alternative_Cohort"
    
    # Technical cohort
    if 'yes' in need_365:
        tech_cohort = "Need_Software_Setup"
    else:
        tech_cohort = "Software_Ready"
    
    # Support cohort
    if 'yes' in refugee_status or 'yes' in disabled_status:
        support_cohort = "High_Support"
    else:
        support_cohort = "Standard_Support"
    
    # Communication cohort
    if email_valid:
        comm_cohort = "Moodle_Ready"
    else:
        comm_cohort = "Email_Correction_Needed"
    
    # Readiness status
    if email_valid and 'yes' in attending and 'yes' not in need_365:
        readiness = "Ready_to_Start"
    elif email_valid and 'yes' in attending and 'yes' in need_365:
        readiness = "Need_Setup"
    else:
        readiness = "Need_Follow_up"
    
    return {
        'main_cohort': main_cohort,
        'tech_cohort': tech_cohort,
        'support_cohort': support_cohort,
        'communication_cohort': comm_cohort,
        'readiness_status': readiness
    }
