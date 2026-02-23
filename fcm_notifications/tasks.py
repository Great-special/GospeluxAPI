from celery import shared_task
from django.utils import timezone
from .models import Notification, DeviceToken, NotificationLog
from .fcm_service import FCMService
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_notification_task(self, notification_id):
    """
    Celery task to send notification asynchronously
    
    Args:
        notification_id: ID of the notification to send
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.status != 'pending':
            logger.warning(f"Notification {notification_id} is not pending. Current status: {notification.status}")
            return
        
        notification_type = notification.notification_type
        
        if notification_type == 'topic':
            # Send to topic
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
            
        elif notification_type == 'condition':
            # Send to condition
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
            
        else:  # single or bulk
            # Get target users
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
        
        logger.info(f"Successfully processed notification {notification_id}")
        
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
    except Exception as e:
        logger.error(f"Error processing notification {notification_id}: {str(e)}")
        # Retry task
        raise self.retry(exc=e, countdown=60)


@shared_task
def send_scheduled_notifications():
    """
    Celery beat task to send scheduled notifications
    Run this periodically (e.g., every minute)
    """
    now = timezone.now()
    
    # Get pending notifications that are scheduled to be sent
    scheduled_notifications = Notification.objects.filter(
        status='pending',
        scheduled_at__lte=now
    )
    
    for notification in scheduled_notifications:
        send_notification_task.delay(notification.id)
    
    logger.info(f"Queued {scheduled_notifications.count()} scheduled notifications")


@shared_task
def cleanup_old_logs():
    """
    Celery beat task to cleanup old notification logs
    Run this daily
    """
    from datetime import timedelta
    
    # Delete logs older than 90 days
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count = NotificationLog.objects.filter(
        sent_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Deleted {deleted_count} old notification logs")


@shared_task
def cleanup_inactive_tokens():
    """
    Celery beat task to cleanup inactive device tokens
    Run this weekly
    """
    from datetime import timedelta
    
    # Delete inactive tokens that haven't been used in 90 days
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count = DeviceToken.objects.filter(
        is_active=False,
        last_used__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Deleted {deleted_count} inactive device tokens")
