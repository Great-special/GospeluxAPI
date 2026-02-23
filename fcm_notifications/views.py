from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import (
    DeviceToken,
    Notification,
    NotificationTemplate,
    NotificationLog,
    TopicSubscription
)
from .serializers import (
    DeviceTokenSerializer,
    RegisterDeviceSerializer,
    NotificationSerializer,
    NotificationTemplateSerializer,
    SendNotificationSerializer,
    TopicSubscriptionSerializer,
    TopicSubscriptionListSerializer,
    NotificationStatsSerializer,
    NotificationLogSerializer
)
from .fcm_service import FCMService
from .tasks import send_notification_task
import logging

logger = logging.getLogger(__name__)


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """ViewSet for managing device tokens"""
    
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return device tokens for current user"""
        if self.request.user.is_staff:
            return DeviceToken.objects.all()
        return DeviceToken.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='register')
    def register_device(self, request):
        """Register a new device token"""
        serializer = RegisterDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        platform = serializer.validated_data['platform']
        device_id = serializer.validated_data.get('device_id', '')
        device_name = serializer.validated_data.get('device_name', '')
        
        # Check if token already exists
        device_token, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': request.user,
                'platform': platform,
                'device_id': device_id,
                'device_name': device_name,
                'is_active': True,
                'last_used': timezone.now()
            }
        )
        
        response_serializer = DeviceTokenSerializer(device_token)
        
        return Response({
            'success': True,
            'message': 'Device registered successfully' if created else 'Device updated successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a device token"""
        device_token = self.get_object()
        device_token.is_active = False
        device_token.save()
        
        return Response({
            'success': True,
            'message': 'Device deactivated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a device token"""
        device_token = self.get_object()
        device_token.is_active = True
        device_token.save()
        
        return Response({
            'success': True,
            'message': 'Device activated successfully'
        })
    
    @action(detail=False, methods=['get'])
    def my_devices(self, request):
        """Get all devices for current user"""
        devices = DeviceToken.objects.filter(user=request.user)
        serializer = self.get_serializer(devices, many=True)
        
        return Response({
            'success': True,
            'count': devices.count(),
            'data': serializer.data
        })


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notifications"""
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications based on user role"""
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(
            Q(created_by=self.request.user) | 
            Q(target_users=self.request.user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def send(self, request):
        """Send notification immediately"""
        serializer = SendNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_type = serializer.validated_data['notification_type']
        title = serializer.validated_data['title']
        body = serializer.validated_data['body']
        data = serializer.validated_data.get('data', {})
        icon = serializer.validated_data.get('icon')
        image = serializer.validated_data.get('image')
        click_action = serializer.validated_data.get('click_action')
        
        # Create notification record
        notification = Notification.objects.create(
            title=title,
            body=body,
            notification_type=notification_type,
            data=data,
            icon=icon,
            image=image,
            click_action=click_action,
            created_by=request.user,
            status='pending'
        )
        
        if notification_type == 'topic':
            topic = serializer.validated_data['topic']
            notification.topic = topic
            notification.save()
            
            # Send to topic
            result = FCMService.send_to_topic(
                topic=topic,
                title=title,
                body=body,
                data=data,
                icon=icon,
                image=image,
                click_action=click_action
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
            condition = serializer.validated_data['condition']
            notification.condition = condition
            notification.save()
            
            # Send to condition
            result = FCMService.send_to_condition(
                condition=condition,
                title=title,
                body=body,
                data=data,
                icon=icon,
                image=image,
                click_action=click_action
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
            user_ids = serializer.validated_data['user_ids']
            
            # Get active device tokens for users
            device_tokens = DeviceToken.objects.filter(
                user_id__in=user_ids,
                is_active=True
            )
            
            if not device_tokens.exists():
                notification.status = 'failed'
                notification.error_message = 'No active device tokens found'
                notification.save()
                
                return Response({
                    'success': False,
                    'message': 'No active device tokens found for specified users',
                    'notification_id': notification.id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            tokens = list(device_tokens.values_list('token', flat=True))
            notification.total_tokens = len(tokens)
            notification.target_users.set(user_ids)
            notification.save()
            
            # Send notifications
            result = FCMService.send_multicast(
                tokens=tokens,
                title=title,
                body=body,
                data=data,
                icon=icon,
                image=image,
                click_action=click_action
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
        
        response_serializer = NotificationSerializer(notification)
        
        return Response({
            'success': True,
            'message': 'Notification sent successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def send_async(self, request):
        """Send notification asynchronously using Celery"""
        serializer = SendNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create notification record
        notification = Notification.objects.create(
            title=serializer.validated_data['title'],
            body=serializer.validated_data['body'],
            notification_type=serializer.validated_data['notification_type'],
            data=serializer.validated_data.get('data', {}),
            icon=serializer.validated_data.get('icon'),
            image=serializer.validated_data.get('image'),
            click_action=serializer.validated_data.get('click_action'),
            topic=serializer.validated_data.get('topic'),
            condition=serializer.validated_data.get('condition'),
            created_by=request.user,
            status='pending'
        )
        
        if serializer.validated_data['notification_type'] in ['single', 'bulk']:
            user_ids = serializer.validated_data['user_ids']
            notification.target_users.set(user_ids)
        
        # Queue task
        try:
            send_notification_task.delay(notification.id)
            message = 'Notification queued for sending'
        except Exception as e:
            logger.error(f"Error queueing notification: {str(e)}")
            message = 'Notification created but could not be queued. Will be sent manually.'
        
        response_serializer = NotificationSerializer(notification)
        
        return Response({
            'success': True,
            'message': message,
            'data': response_serializer.data
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for a notification"""
        notification = self.get_object()
        logs = NotificationLog.objects.filter(notification=notification)
        serializer = NotificationLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'count': logs.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get notification statistics"""
        total_notifications = Notification.objects.count()
        total_sent = Notification.objects.filter(status='sent').count()
        total_failed = Notification.objects.filter(status='failed').count()
        total_pending = Notification.objects.filter(status='pending').count()
        
        success_rate = (total_sent / total_notifications * 100) if total_notifications > 0 else 0
        
        total_devices = DeviceToken.objects.count()
        active_devices = DeviceToken.objects.filter(is_active=True).count()
        
        devices_by_platform = DeviceToken.objects.filter(
            is_active=True
        ).values('platform').annotate(count=Count('id'))
        
        devices_dict = {item['platform']: item['count'] for item in devices_by_platform}
        
        serializer = NotificationStatsSerializer(data={
            'total_notifications': total_notifications,
            'total_sent': total_sent,
            'total_failed': total_failed,
            'total_pending': total_pending,
            'success_rate': round(success_rate, 2),
            'total_devices': total_devices,
            'active_devices': active_devices,
            'devices_by_platform': devices_dict
        })
        serializer.is_valid()
        
        return Response({
            'success': True,
            'data': serializer.data
        })


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notification templates"""
    
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active templates"""
        templates = NotificationTemplate.objects.filter(is_active=True)
        serializer = self.get_serializer(templates, many=True)
        
        return Response({
            'success': True,
            'count': templates.count(),
            'data': serializer.data
        })


class TopicSubscriptionViewSet(viewsets.ViewSet):
    """ViewSet for managing topic subscriptions"""
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List all topic subscriptions"""
        if request.user.is_staff:
            subscriptions = TopicSubscription.objects.all()
        else:
            subscriptions = TopicSubscription.objects.filter(user=request.user)
        
        serializer = TopicSubscriptionListSerializer(subscriptions, many=True)
        
        return Response({
            'success': True,
            'count': subscriptions.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Subscribe to a topic"""
        serializer = TopicSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        topic = serializer.validated_data['topic']
        device_token_id = serializer.validated_data.get('device_token_id')
        
        # Get device tokens
        if device_token_id:
            device_tokens = DeviceToken.objects.filter(
                id=device_token_id,
                user=request.user,
                is_active=True
            )
        else:
            # Subscribe all user's active devices
            device_tokens = DeviceToken.objects.filter(
                user=request.user,
                is_active=True
            )
        
        if not device_tokens.exists():
            return Response({
                'success': False,
                'message': 'No active device tokens found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tokens = list(device_tokens.values_list('token', flat=True))
        
        # Subscribe to topic
        result = FCMService.subscribe_to_topic(tokens, topic)
        
        # Create subscription records
        for device_token in device_tokens:
            TopicSubscription.objects.update_or_create(
                user=request.user,
                device_token=device_token,
                topic=topic,
                defaults={
                    'is_subscribed': True,
                    'unsubscribed_at': None
                }
            )
        
        return Response({
            'success': True,
            'message': f'Successfully subscribed to topic: {topic}',
            'details': result
        })
    
    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """Unsubscribe from a topic"""
        serializer = TopicSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        topic = serializer.validated_data['topic']
        device_token_id = serializer.validated_data.get('device_token_id')
        
        # Get device tokens
        if device_token_id:
            device_tokens = DeviceToken.objects.filter(
                id=device_token_id,
                user=request.user,
                is_active=True
            )
        else:
            # Unsubscribe all user's active devices
            device_tokens = DeviceToken.objects.filter(
                user=request.user,
                is_active=True
            )
        
        if not device_tokens.exists():
            return Response({
                'success': False,
                'message': 'No active device tokens found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tokens = list(device_tokens.values_list('token', flat=True))
        
        # Unsubscribe from topic
        result = FCMService.unsubscribe_from_topic(tokens, topic)
        
        # Update subscription records
        TopicSubscription.objects.filter(
            user=request.user,
            device_token__in=device_tokens,
            topic=topic
        ).update(
            is_subscribed=False,
            unsubscribed_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'Successfully unsubscribed from topic: {topic}',
            'details': result
        })
    
    @action(detail=False, methods=['get'])
    def my_topics(self, request):
        """Get all topics current user is subscribed to"""
        subscriptions = TopicSubscription.objects.filter(
            user=request.user,
            is_subscribed=True
        ).values('topic').distinct()
        
        topics = [sub['topic'] for sub in subscriptions]
        
        return Response({
            'success': True,
            'count': len(topics),
            'topics': topics
        })
