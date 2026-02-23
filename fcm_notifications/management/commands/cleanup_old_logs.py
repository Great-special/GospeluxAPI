from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from fcm_notifications.models import NotificationLog
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cleanup old notification logs (run via cron)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete logs older than this many days (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        old_logs = NotificationLog.objects.filter(sent_at__lt=cutoff_date)
        count = old_logs.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'No logs older than {days} days found')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} logs older than {days} days'
                )
            )
            return
        
        self.stdout.write(f'Deleting {count} logs older than {days} days...')
        
        deleted_count, _ = old_logs.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successfully deleted {deleted_count} old notification logs')
        )
        
        logger.info(f'Deleted {deleted_count} notification logs older than {days} days')
