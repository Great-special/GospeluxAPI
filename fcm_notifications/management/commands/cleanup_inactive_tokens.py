from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from fcm_notifications.models import DeviceToken
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cleanup inactive device tokens (run via cron)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete inactive tokens not used for this many days (default: 90)',
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
        
        inactive_tokens = DeviceToken.objects.filter(
            is_active=False,
            last_used__lt=cutoff_date
        )
        count = inactive_tokens.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'No inactive tokens older than {days} days found'
                )
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} inactive tokens not used for {days} days'
                )
            )
            for token in inactive_tokens[:10]:  # Show first 10
                self.stdout.write(
                    f'  - Token {token.id}: {token.platform} - '
                    f'Last used: {token.last_used.strftime("%Y-%m-%d")}'
                )
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
            return
        
        self.stdout.write(
            f'Deleting {count} inactive tokens not used for {days} days...'
        )
        
        deleted_count, _ = inactive_tokens.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Successfully deleted {deleted_count} inactive device tokens'
            )
        )
        
        logger.info(f'Deleted {deleted_count} inactive device tokens older than {days} days')
