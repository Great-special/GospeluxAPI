# management/commands/sync_bible_data.py
from django.core.management.base import BaseCommand
from ...data_sync_service import DataSyncService
from django.conf import settings

class Command(BaseCommand):
    help = 'Sync Bible data from API.Bible to local database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--bible-version',
            type=str,
            help='ID of specific Bible version to sync'
        )
        parser.add_argument(
            '--full-sync',
            action='store_true',
            help='Perform a full sync of all data'
        )
    
    def handle(self, *args, **options):
        if not hasattr(settings, 'BIBLE_API_KEY') or not settings.BIBLE_API_KEY:
            self.stderr.write(self.style.ERROR('BIBLE_API_KEY is not set in settings'))
            return
        
        sync_service = DataSyncService()
        bible_version_id = options.get('bible_version')
        full_sync = options.get('full_sync')
        
        if full_sync:
            self.stdout.write(self.style.SUCCESS('Starting full sync...'))
            success, messages = sync_service.full_sync(bible_version_id)
            
            for message in messages:
                if 'Error' in message:
                    self.stderr.write(self.style.ERROR(message))
                else:
                    self.stdout.write(self.style.SUCCESS(message))
            
            if success:
                self.stdout.write(self.style.SUCCESS('Full sync completed successfully'))
            else:
                self.stderr.write(self.style.ERROR('Full sync completed with errors'))
        else:
            self.stdout.write(self.style.SUCCESS('Syncing Bible versions...'))
            success, message = sync_service.sync_bible_versions()
            
            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stderr.write(self.style.ERROR(message))