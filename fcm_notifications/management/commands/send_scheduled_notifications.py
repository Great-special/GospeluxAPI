from django.core.management.base import BaseCommand
from django.utils import timezone
from fcm_notifications.models import Notification, DeviceToken, NotificationLog
from fcm_notifications.fcm_service import FCMService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send scheduled notifications (run via cron)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Get pending notifications that are scheduled to be sent
        scheduled_notifications = Notification.objects.filter(
            status='pending',
            scheduled_at__lte=now
        )
        
        count = scheduled_notifications.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would send {count} notifications')
            )
            for notification in scheduled_notifications:
                self.stdout.write(f'  - {notification.title} (ID: {notification.id})')
            return
        
        self.stdout.write(f'Processing {count} scheduled notifications...')
        
        success_count = 0
        error_count = 0
        
        for notification in scheduled_notifications:
            try:
                self.stdout.write(f'Sending notification: {notification.title} (ID: {notification.id})')
                
                if notification.notification_type == 'topic':
                    self._send_topic_notification(notification)
                elif notification.notification_type == 'condition':
                    self._send_condition_notification(notification)
                else:  # single or bulk
                    self._send_user_notification(notification)
                
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Successfully sent notification {notification.id}')
                )
                
            except Exception as e:
                error_count += 1
                notification.status = 'failed'
                notification.error_message = str(e)
                notification.save()
                
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send notification {notification.id}: {str(e)}')
                )
                logger.error(f'Error sending notification {notification.id}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {success_count} successful, {error_count} failed'
            )
        )

    def _send_topic_notification(self, notification):
        """Send notification to a topic"""
        result = FCMService.send_to_topic(
            topic=notification.topic,
            title=notification.title,
            body=notification.body,
            data=notification.data,
            icon=notification.icon,
            image=notification.image,
            click_action=notification.click_action
        )
        
        if result['success']:
            notification.status = 'sent'
            notification.successful_sends = 1
            notification.sent_at = timezone.now()
        else:
            notification.status = 'failed'
            notification.error_message = result['error']
        
        notification.save()

    def _send_condition_notification(self, notification):
        """Send notification based on condition"""
        result = FCMService.send_to_condition(
            condition=notification.condition,
            title=notification.title,
            body=notification.body,
            data=notification.data,
            icon=notification.icon,
            image=notification.image,
            click_action=notification.click_action
        )
        
        if result['success']:
            notification.status = 'sent'
            notification.successful_sends = 1
            notification.sent_at = timezone.now()
        else:
            notification.status = 'failed'
            notification.error_message = result['error']
        
        notification.save()

    def _send_user_notification(self, notification):
        """Send notification to specific users"""
        user_ids = list(notification.target_users.values_list('id', flat=True))
        
        # Get active device tokens
        device_tokens = DeviceToken.objects.filter(
            user_id__in=user_ids,
            is_active=True
        )
        
        if not device_tokens.exists():
            notification.status = 'failed'
            notification.error_message = 'No active device tokens found'
            notification.save()
            return
        
        tokens = list(device_tokens.values_list('token', flat=True))
        notification.total_tokens = len(tokens)
        notification.save()
        
        # Send notifications
        result = FCMService.send_multicast(
            tokens=tokens,
            title=notification.title,
            body=notification.body,
            data=notification.data,
            icon=notification.icon,
            image=notification.image,
            click_action=notification.click_action
        )
        
        # Update notification status
        notification.successful_sends = result['success_count']
        notification.failed_sends = result['failure_count']
        notification.sent_at = timezone.now()
        
        if result['failure_count'] == 0:
            notification.status = 'sent'
        elif result['success_count'] == 0:
            notification.status = 'failed'
        else:
            notification.status = 'partial'
        
        notification.save()
        
        # Create logs for each device
        for device_token in device_tokens:
            token_failed = any(
                ft['token'] == device_token.token 
                for ft in result['failed_tokens']
            )
            
            if token_failed:
                error_info = next(
                    (ft for ft in result['failed_tokens'] 
                     if ft['token'] == device_token.token),
                    {}
                )
                NotificationLog.objects.create(
                    notification=notification,
                    device_token=device_token,
                    status='failed',
                    error_message=error_info.get('error', 'Unknown error')
                )
                
                # Deactivate invalid tokens
                if 'unregistered' in error_info.get('error', '').lower():
                    device_token.is_active = False
                    device_token.save()
            else:
                NotificationLog.objects.create(
                    notification=notification,
                    device_token=device_token,
                    status='success',
                    fcm_message_id=f"success_{device_token.id}"
                )
                device_token.mark_as_used()
