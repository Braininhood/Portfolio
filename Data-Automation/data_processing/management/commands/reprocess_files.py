from django.core.management.base import BaseCommand
from data_processing.services import DataProcessingService
from data_processing.models import ExcelFile, Participant

class Command(BaseCommand):
    help = 'Reprocess all Excel files to extract participant data'

    def handle(self, *args, **options):
        service = DataProcessingService()
        
        # Clear existing participants
        Participant.objects.all().delete()
        self.stdout.write('Cleared existing participants')
        
        # Reprocess all files
        files = ExcelFile.objects.all()
        total_participants = 0
        
        for file_obj in files:
            if file_obj.file:
                try:
                    self.stdout.write(f'Processing {file_obj.name}...')
                    result = service.process_excel_file(file_obj.file.path)
                    file_obj.status = 'processed'
                    file_obj.participant_count = result.get('participant_count', 0)
                    file_obj.save()
                    total_participants += result.get('participant_count', 0)
                    self.stdout.write(f'  -> {result.get("participant_count", 0)} participants extracted')
                except Exception as e:
                    file_obj.status = 'error'
                    file_obj.error_message = str(e)
                    file_obj.save()
                    self.stdout.write(f'  -> Error: {e}')
        
        self.stdout.write(f'Total participants processed: {total_participants}')
        self.stdout.write('Reprocessing complete!')
