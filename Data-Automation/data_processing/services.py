import pandas as pd
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from django.conf import settings

from .models import ExcelFile, Participant, Cohort
from .utils import validate_email, validate_date
from django.db import models


class DataProcessingService:
    """Service for processing Excel files and extracting participant data"""
    
    def __init__(self):
        self.required_fields = [
            'full_name', 'moodle_email', 'attending', 'need_365'
        ]
    
    def process_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single Excel file and extract participant data"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Create ExcelFile record
            excel_file = ExcelFile.objects.create(
                name=os.path.basename(file_path),
                file=file_path,
                status='processing'
            )
            
            participants = []
            for _, row in df.iterrows():
                participant_data = self._extract_participant_data(row, excel_file)
                if participant_data:
                    participant = Participant.objects.create(**participant_data)
                    participants.append(participant)
            
            excel_file.status = 'processed'
            excel_file.participant_count = len(participants)
            excel_file.save()
            
            return {
                'participant_count': len(participants),
                'file_id': excel_file.id,
                'status': 'success'
            }
            
        except Exception as e:
            if 'excel_file' in locals():
                excel_file.status = 'error'
                excel_file.error_message = str(e)
                excel_file.save()
            raise e
    
    def _extract_participant_data(self, row: pd.Series, excel_file: ExcelFile) -> Dict[str, Any]:
        """Extract participant data from a single row"""
        try:
            # Map Excel column names to our expected field names
            column_mapping = {
                'Full name': 'full_name',
                'Please enter your email address (For Moodle Access)': 'moodle_email',
                'The next cohort starts 11/15/2025 for 6 weeks, Monday & Wednesday evenings 6:00-8:00pm?': 'attending',
                'Do you require Ms Office 365 Software (You need this for the course)': 'need_365',
                'If you cannot attend these dates - Could you let us know us when you would be available to attend (Please note we have a waiting list for these courses and we cannot hold your place for long)': 'alternative_dates',
                'What is your postcode?': 'postcode',
                'Are you a refugee?': 'refugee_status',
                'Are you disabled?': 'disabled_status'
            }
            
            # Get basic information using mapped column names
            full_name = str(row.get('Full name', '')).strip()
            email = str(row.get('Please enter your email address (For Moodle Access)', '')).strip()
            
            if not full_name or not email:
                return None
            
            # Validate email
            email_valid = validate_email(email)
            
            # Get other fields using mapped column names
            attending = str(row.get('The next cohort starts 11/15/2025 for 6 weeks, Monday & Wednesday evenings 6:00-8:00pm?', '')).strip()
            alternative_dates = str(row.get('If you cannot attend these dates - Could you let us know us when you would be available to attend (Please note we have a waiting list for these courses and we cannot hold your place for long)', '')).strip()
            need_365 = str(row.get('Do you require Ms Office 365 Software (You need this for the course)', '')).strip()
            postcode = str(row.get('What is your postcode?', '')).strip()
            refugee_status = str(row.get('Are you a refugee?', '')).strip()
            disabled_status = str(row.get('Are you disabled?', '')).strip()
            
            return {
                'full_name': full_name,
                'email': email,
                'email_valid': email_valid,
                'attending': attending,
                'alternative_dates': alternative_dates,
                'need_365': need_365,
                'postcode': postcode,
                'refugee_status': refugee_status,
                'disabled_status': disabled_status,
                'source_file': excel_file
            }
        except Exception as e:
            print(f"Error extracting participant data: {e}")
            return None
    
    def process_multiple_files(self, file_ids: List[int]) -> Dict[str, Any]:
        """Process multiple Excel files"""
        files = ExcelFile.objects.filter(id__in=file_ids)
        total_participants = 0
        
        for file_obj in files:
            if file_obj.file:
                result = self.process_excel_file(file_obj.file.path)
                total_participants += result['participant_count']
        
        return {
            'files_processed': len(files),
            'total_participants': total_participants,
            'status': 'success'
        }
    
    def analyze_data(self, file_ids: List[int]) -> Dict[str, Any]:
        """Analyze data from multiple files"""
        participants = Participant.objects.filter(source_file_id__in=file_ids)
        
        if not participants.exists():
            return {
                'total_participants': 0,
                'valid_emails': 0,
                'invalid_emails': 0,
                'attending_yes': 0,
                'attending_no': 0,
                'need_365_yes': 0,
                'need_365_no': 0,
                'refugees': 0,
                'disabled': 0,
                'email_issues': [],
                'duplicate_names': [],
                'status': 'success',
                'message': 'No participants found for the specified files'
            }
        
        # Calculate statistics
        total_participants = participants.count()
        valid_emails = participants.filter(email_valid=True).count()
        attending_yes = participants.filter(attending__icontains='yes').count()
        need_365_yes = participants.filter(need_365__icontains='yes').count()
        refugees = participants.filter(refugee_status__icontains='yes').count()
        disabled = participants.filter(disabled_status__icontains='yes').count()
        
        # Email issues
        email_issues = participants.filter(email_valid=False).values('full_name', 'email')
        
        # Duplicate names
        from django.db.models import Count
        name_counts = participants.values('full_name').annotate(count=Count('id')).filter(count__gt=1)
        
        return {
            'total_participants': total_participants,
            'valid_emails': valid_emails,
            'invalid_emails': total_participants - valid_emails,
            'attending_yes': attending_yes,
            'attending_no': total_participants - attending_yes,
            'need_365_yes': need_365_yes,
            'need_365_no': total_participants - need_365_yes,
            'refugees': refugees,
            'disabled': disabled,
            'email_issues': list(email_issues),
            'duplicate_names': list(name_counts),
            'status': 'success'
        }
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate Excel file compatibility"""
        try:
            df = pd.read_excel(file_path)
            
            # Check for required fields
            missing_fields = [field for field in self.required_fields if field not in df.columns]
            
            # Check data quality
            total_rows = len(df)
            empty_rows = df.isnull().all(axis=1).sum()
            
            # Check email field
            email_field = 'moodle_email' if 'moodle_email' in df.columns else None
            valid_emails = 0
            if email_field:
                valid_emails = df[email_field].apply(validate_email).sum()
            
            compatibility_score = 100
            if missing_fields:
                compatibility_score -= len(missing_fields) * 10
            if empty_rows > total_rows * 0.1:  # More than 10% empty rows
                compatibility_score -= 20
            if email_field and valid_emails < total_rows * 0.5:  # Less than 50% valid emails
                compatibility_score -= 30
            
            return {
                'compatible': compatibility_score >= 70,
                'compatibility_score': max(0, compatibility_score),
                'total_rows': total_rows,
                'missing_fields': missing_fields,
                'valid_emails': valid_emails,
                'recommendations': self._get_recommendations(missing_fields, valid_emails, total_rows)
            }
            
        except Exception as e:
            return {
                'compatible': False,
                'error': str(e)
            }
    
    def _get_recommendations(self, missing_fields: List[str], valid_emails: int, total_rows: int) -> List[str]:
        """Get recommendations for improving file compatibility"""
        recommendations = []
        
        if missing_fields:
            recommendations.append(f"Add missing fields: {', '.join(missing_fields)}")
        
        if valid_emails < total_rows * 0.5:
            recommendations.append("Improve email data quality - many invalid email addresses")
        
        if total_rows < 10:
            recommendations.append("Consider adding more data for better analysis")
        
        return recommendations


class CohortAnalysisService:
    """Service for creating and managing cohorts"""
    
    def create_cohorts_from_files(self, file_ids: List[int]) -> Dict[str, Any]:
        """Create cohorts from participant data in files using BPA logic"""
        participants = Participant.objects.filter(source_file_id__in=file_ids)
        
        if not participants.exists():
            return {'error': 'No participants found for the specified files'}
        
        # Get file information for better naming
        files = ExcelFile.objects.filter(id__in=file_ids)
        file_names = [f.name for f in files]
        total_participants = participants.count()
        
        # Clear existing cohorts for these files to prevent duplicates
        existing_cohorts = Cohort.objects.filter(
            participants__source_file_id__in=file_ids
        ).distinct()
        existing_cohorts.delete()
        
        # Create cohorts based on participant characteristics using BPA logic
        cohorts_created = []
        
        # BPA Analysis: Analyze participant data intelligently
        bpa_analysis = self._analyze_participants_for_cohorts(participants, file_names)
        
        # Create cohorts based on BPA analysis
        cohorts_created = []
        
        # Main cohorts (attending vs not attending)
        attending_participants = participants.filter(attending__icontains='yes')
        not_attending_participants = participants.exclude(attending__icontains='yes')
        
        if attending_participants.exists():
            primary_cohort = self._create_cohort(
                f'Primary Cohort - Confirmed Attendees ({attending_participants.count()})', 
                'primary', 
                attending_participants,
                f"Participants confirmed for the course from {', '.join(file_names)}"
            )
            if primary_cohort:
                cohorts_created.append(primary_cohort)
        
        if not_attending_participants.exists():
            alternative_cohort = self._create_cohort(
                f'Alternative Cohort - Different Scheduling ({not_attending_participants.count()})', 
                'alternative',
                not_attending_participants,
                f"Participants requiring alternative scheduling from {', '.join(file_names)}"
            )
            if alternative_cohort:
                cohorts_created.append(alternative_cohort)
        
        # Technical cohorts
        need_software_participants = participants.filter(need_365__icontains='yes')
        software_ready_participants = participants.exclude(need_365__icontains='yes')
        
        if need_software_participants.exists():
            need_software_cohort = self._create_cohort(
                f'Need Software Setup - Office 365 Required ({need_software_participants.count()})', 
                'need_software',
                need_software_participants,
                f"Participants requiring Microsoft Office 365 software installation"
            )
            if need_software_cohort:
                cohorts_created.append(need_software_cohort)
        
        if software_ready_participants.exists():
            software_ready_cohort = self._create_cohort(
                f'Software Ready - Setup Complete ({software_ready_participants.count()})', 
                'software_ready',
                software_ready_participants,
                f"Participants with existing software setup"
            )
            if software_ready_cohort:
                cohorts_created.append(software_ready_cohort)
        
        # Support cohorts
        from django.db.models import Q
        high_support_participants = participants.filter(
            Q(refugee_status__icontains='yes') |
            Q(disabled_status__icontains='yes')
        )
        standard_support_participants = participants.exclude(
            Q(refugee_status__icontains='yes') |
            Q(disabled_status__icontains='yes')
        )
        
        if high_support_participants.exists():
            high_support_cohort = self._create_cohort(
                f'High Support - Enhanced Assistance ({high_support_participants.count()})', 
                'high_support',
                high_support_participants,
                f"Refugees, disabled, or participants needing extra assistance"
            )
            if high_support_cohort:
                cohorts_created.append(high_support_cohort)
        
        if standard_support_participants.exists():
            standard_support_cohort = self._create_cohort(
                f'Standard Support - Regular Participants ({standard_support_participants.count()})', 
                'standard_support',
                standard_support_participants,
                f"Participants with standard support requirements"
            )
            if standard_support_cohort:
                cohorts_created.append(standard_support_cohort)
        
        # Communication cohorts
        moodle_ready_participants = participants.filter(email_valid=True)
        email_correction_participants = participants.filter(email_valid=False)
        
        if moodle_ready_participants.exists():
            moodle_ready_cohort = self._create_cohort(
                f'Moodle Ready - Valid Email Access ({moodle_ready_participants.count()})', 
                'moodle_ready',
                moodle_ready_participants,
                f"Participants with valid email addresses for Moodle access"
            )
            if moodle_ready_cohort:
                cohorts_created.append(moodle_ready_cohort)
        
        if email_correction_participants.exists():
            email_correction_cohort = self._create_cohort(
                f'Email Correction Needed - Invalid Addresses ({email_correction_participants.count()})', 
                'email_correction',
                email_correction_participants,
                f"Participants requiring email address correction"
            )
            if email_correction_cohort:
                cohorts_created.append(email_correction_cohort)
        
        return {
            'cohorts_created': len(cohorts_created),
            'cohort_details': [
                {
                    'id': cohort.id,
                    'name': cohort.name,
                    'type': cohort.cohort_type,
                    'participant_count': cohort.participant_count
                }
                for cohort in cohorts_created
            ],
            'status': 'success'
        }
    
    def _create_cohort(self, name: str, cohort_type: str, participants_query, description: str = None) -> Cohort:
        """Create a cohort with the given participants"""
        if not participants_query.exists():
            return None
        
        cohort = Cohort.objects.create(
            name=name,
            cohort_type=cohort_type,
            description=description or f"Automatically created cohort for {name.lower()}"
        )
        
        cohort.participants.set(participants_query)
        return cohort
    
    def _analyze_participants_for_cohorts(self, participants, file_names):
        """BPA Analysis: Analyze participant data for intelligent cohort creation"""
        analysis = {
            'total_participants': participants.count(),
            'attending_yes': participants.filter(attending__icontains='yes').count(),
            'attending_no': participants.exclude(attending__icontains='yes').count(),
            'need_software': participants.filter(need_365__icontains='yes').count(),
            'software_ready': participants.exclude(need_365__icontains='yes').count(),
            'refugees': participants.filter(refugee_status__icontains='yes').count(),
            'disabled': participants.filter(disabled_status__icontains='yes').count(),
            'valid_emails': participants.filter(email_valid=True).count(),
            'invalid_emails': participants.filter(email_valid=False).count(),
            'files_processed': file_names
        }
        
        # BPA Logic: Determine optimal cohort distribution
        analysis['recommendations'] = []
        
        if analysis['attending_yes'] > analysis['attending_no']:
            analysis['recommendations'].append("Primary cohort should be prioritized - majority attending")
        
        if analysis['need_software'] > analysis['software_ready']:
            analysis['recommendations'].append("Software setup support needed for majority")
        
        if analysis['refugees'] + analysis['disabled'] > analysis['total_participants'] * 0.3:
            analysis['recommendations'].append("High support cohort needed - significant special needs")
        
        if analysis['invalid_emails'] > analysis['total_participants'] * 0.2:
            analysis['recommendations'].append("Email verification priority - many invalid addresses")
        
        return analysis


class BPAService:
    """Service for Business Process Automation"""
    
    def process_cohorts(self, cohort_ids: List[int]) -> Dict[str, Any]:
        """Apply BPA logic to process cohorts and resolve duplicates"""
        cohorts = Cohort.objects.filter(id__in=cohort_ids)
        
        if len(cohorts) < 2:
            return {'error': 'At least 2 cohorts required for BPA processing'}
        
        # Get all participants from the cohorts
        all_participants = Participant.objects.filter(cohorts__in=cohorts).distinct()
        
        # Group participants by name to find duplicates
        participant_groups = {}
        for participant in all_participants:
            name = participant.full_name.lower().strip()
            if name not in participant_groups:
                participant_groups[name] = []
            participant_groups[name].append(participant)
        
        # Process duplicates
        duplicates_resolved = 0
        processing_notes = []
        
        for name, participants in participant_groups.items():
            if len(participants) > 1:
                # Find the smallest cohort among these participants
                cohort_sizes = {}
                for participant in participants:
                    for cohort in participant.cohorts.all():
                        if cohort.id in cohort_ids:
                            cohort_sizes[cohort.id] = cohort.participants.count()
                
                if cohort_sizes:
                    smallest_cohort_id = min(cohort_sizes.keys(), key=lambda x: cohort_sizes[x])
                    smallest_cohort = Cohort.objects.get(id=smallest_cohort_id)
                    
                    # Assign all participants with this name to the smallest cohort
                    for participant in participants:
                        participant.bpa_cohort = smallest_cohort.name
                        participant.bpa_processing_notes = f"Duplicate resolved: assigned to {smallest_cohort.name}"
                        participant.save()
                        
                        # Remove from other cohorts and add to smallest
                        participant.cohorts.clear()
                        participant.cohorts.add(smallest_cohort)
                    
                    duplicates_resolved += 1
                    processing_notes.append(f"Resolved {len(participants)} duplicates for '{name}' in {smallest_cohort.name}")
        
        return {
            'duplicates_resolved': duplicates_resolved,
            'processing_notes': processing_notes,
            'status': 'success'
        }
    
    def run_demo(self) -> Dict[str, Any]:
        """Run BPA demonstration with sample data"""
        # Sample data similar to the CLI demo
        cohort1 = [1, 2, 3, 4, 5, 77, 78, 79, 80]
        cohort2 = [5, 6, 7, 8, 1, 12, 66, 88, 44, 65, 77, 78, 79, 80]
        
        # Find duplicates
        duplicates = [x for x in cohort1 if x in cohort2]
        
        # Apply BPA logic: assign duplicates to smaller cohort
        new_cohort1 = [x for x in cohort1 if x not in duplicates]
        new_cohort2 = [x for x in cohort2 if x not in duplicates]
        
        # Add duplicates to smaller cohort
        if len(new_cohort1) < len(new_cohort2):
            new_cohort1.extend(duplicates)
        else:
            new_cohort2.extend(duplicates)
        
        return {
            'original_cohort1': cohort1,
            'original_cohort2': cohort2,
            'processed_cohort1': new_cohort1,
            'processed_cohort2': new_cohort2,
            'duplicates_found': len(duplicates),
            'duplicates_resolved': len(duplicates),
            'balancing_achieved': abs(len(new_cohort1) - len(new_cohort2)) <= 1,
            'status': 'success'
        }
