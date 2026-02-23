from django.core.management.base import BaseCommand
from fcm_notifications.fcm_service import FCMService
from fcm_notifications.models import DeviceToken
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test FCM connection and send test notification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--token',
            type=str,
            help='Device token to send test notification to',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to send test notification to (uses first active device)',
        )

    def handle(self, *args, **options):
        token = options.get('token')
        user_id = options.get('user_id')
        
        self.stdout.write('Testing FCM connection...')
        
        # Initialize FCM
        try:
            FCMService.initialize()
            self.stdout.write(self.style.SUCCESS('✓ FCM initialized successfully'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to initialize FCM: {str(e)}')
            )
            return
        
        # Determine which token to use
        test_token = None
        
        if token:
            test_token = token
            self.stdout.write(f'Using provided token: {token[:20]}...')
        elif user_id:
            try:
                device = DeviceToken.objects.filter(
                    user_id=user_id,
                    is_active=True
                ).first()
                
                if device:
                    test_token = device.token
                    self.stdout.write(
                        f'Using token from user {user_id}: '
                        f'{device.platform} device'
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ No active devices found for user {user_id}'
                        )
                    )
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error finding device: {str(e)}')
                )
                return
        else:
            # Try to find any active device
            device = DeviceToken.objects.filter(is_active=True).first()
            if device:
                test_token = device.token
                self.stdout.write(
                    f'Using first available active device: {device.platform}'
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ No active devices found in database')
                )
                self.stdout.write(
                    'Please provide a token with --token or register a device first'
                )
                return
        
        # Send test notification
        self.stdout.write('\nSending test notification...')
        
        try:
            result = FCMService.send_notification(
                token=test_token,
                title='Test Notification',
                body='This is a test notification from Django FCM app',
                data={
                    'type': 'test',
                    'timestamp': str(timezone.now())
                },
                icon='https://via.placeholder.com/150',
            )
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Test notification sent successfully!'
                    )
                )
                self.stdout.write(f'Message ID: {result["message_id"]}')
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed to send test notification: {result["error"]}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error sending notification: {str(e)}')
            )
            logger.error(f'Error in test_fcm command: {str(e)}')


from django.utils import timezone
