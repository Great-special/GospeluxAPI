from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    DeviceToken, 
    Notification, 
    NotificationTemplate, 
    NotificationLog,
    TopicSubscription
)

User = get_user_model()


class DeviceTokenSerializer(serializers.ModelSerializer):
    """Serializer for device tokens"""
    
    class Meta:
        model = DeviceToken
        fields = [
            'id', 'token', 'platform', 'device_id', 
            'device_name', 'is_active', 'created_at', 
            'updated_at', 'last_used'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used']
    
    def validate_token(self, value):
        """Validate token format"""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid token format")
        return value
    
    def validate_platform(self, value):
        """Validate platform"""
        valid_platforms = ['android', 'ios', 'web']
        if value not in valid_platforms:
            raise serializers.ValidationError(
                f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
            )
        return value


class RegisterDeviceSerializer(serializers.Serializer):
    """Serializer for registering a device token"""
    
    token = serializers.CharField(required=True, max_length=255)
    platform = serializers.ChoiceField(
        choices=['android', 'ios', 'web'],
        required=True
    )
    device_id = serializers.CharField(required=False, allow_blank=True, max_length=255)
    device_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    
    def validate_token(self, value):
        """Validate token format"""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid token format")
        return value


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for notification templates"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'title', 'body', 'icon', 
            'image', 'click_action', 'data', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for notification logs"""
    
    device_token_info = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification', 'device_token', 'device_token_info',
            'fcm_message_id', 'status', 'error_message', 
            'response_data', 'sent_at'
        ]
        read_only_fields = ['id', 'sent_at']
    
    def get_device_token_info(self, obj):
        """Get device token information"""
        if obj.device_token:
            return {
                'platform': obj.device_token.platform,
                'device_name': obj.device_token.device_name,
            }
        return None


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    
    logs = NotificationLogSerializer(many=True, read_only=True)
    target_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'body', 'notification_type',
            'target_users', 'target_user_ids', 'topic', 'condition',
            'data', 'icon', 'image', 'click_action', 
            'status', 'total_tokens', 'successful_sends', 
            'failed_sends', 'error_message', 'scheduled_at',
            'sent_at', 'created_by', 'created_at', 
            'updated_at', 'logs'
        ]
        read_only_fields = [
            'id', 'status', 'total_tokens', 'successful_sends',
            'failed_sends', 'error_message', 'sent_at', 
            'created_by', 'created_at', 'updated_at', 'logs',
            'target_users'
        ]
    
    def validate(self, data):
        """Validate notification data based on type"""
        notification_type = data.get('notification_type', 'single')
        
        if notification_type == 'single':
            target_user_ids = data.get('target_user_ids', [])
            if not target_user_ids:
                raise serializers.ValidationError(
                    "target_user_ids is required for single user notifications"
                )
        elif notification_type == 'topic':
            if not data.get('topic'):
                raise serializers.ValidationError(
                    "topic is required for topic notifications"
                )
        elif notification_type == 'condition':
            if not data.get('condition'):
                raise serializers.ValidationError(
                    "condition is required for condition-based notifications"
                )
        
        return data


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending immediate notifications"""
    
    title = serializers.CharField(required=True, max_length=255)
    body = serializers.CharField(required=True)
    notification_type = serializers.ChoiceField(
        choices=['single', 'bulk', 'topic', 'condition'],
        default='single'
    )
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    topic = serializers.CharField(required=False, allow_blank=True, max_length=255)
    condition = serializers.CharField(required=False, allow_blank=True, max_length=500)
    data = serializers.JSONField(required=False, default=dict)
    icon = serializers.URLField(required=False, allow_blank=True)
    image = serializers.URLField(required=False, allow_blank=True)
    click_action = serializers.URLField(required=False, allow_blank=True)
    template_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        """Validate based on notification type"""
        notification_type = data.get('notification_type', 'single')
        
        # Check if template is provided
        if 'template_id' in data:
            try:
                template = NotificationTemplate.objects.get(
                    id=data['template_id'],
                    is_active=True
                )
                # Override with template data
                data['title'] = template.title
                data['body'] = template.body
                data['icon'] = template.icon or data.get('icon')
                data['image'] = template.image or data.get('image')
                data['click_action'] = template.click_action or data.get('click_action')
                data['data'] = {**template.data, **data.get('data', {})}
            except NotificationTemplate.DoesNotExist:
                raise serializers.ValidationError(
                    "Template not found or inactive"
                )
        
        if notification_type in ['single', 'bulk']:
            if not data.get('user_ids'):
                raise serializers.ValidationError(
                    "user_ids is required for single/bulk notifications"
                )
        elif notification_type == 'topic':
            if not data.get('topic'):
                raise serializers.ValidationError(
                    "topic is required for topic notifications"
                )
        elif notification_type == 'condition':
            if not data.get('condition'):
                raise serializers.ValidationError(
                    "condition is required for condition-based notifications"
                )
        
        return data


class TopicSubscriptionSerializer(serializers.Serializer):
    """Serializer for topic subscription"""
    
    topic = serializers.CharField(required=True, max_length=255)
    device_token_id = serializers.IntegerField(required=False)
    
    def validate_topic(self, value):
        """Validate topic name"""
        # Topic names can only contain letters, numbers, underscores, hyphens, and dots
        import re
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', value):
            raise serializers.ValidationError(
                "Topic name can only contain letters, numbers, underscores, hyphens, and dots"
            )
        return value


class TopicSubscriptionListSerializer(serializers.ModelSerializer):
    """Serializer for listing topic subscriptions"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    device_platform = serializers.CharField(source='device_token.platform', read_only=True)
    
    class Meta:
        model = TopicSubscription
        fields = [
            'id', 'user', 'user_email', 'device_token',
            'device_platform', 'topic', 'is_subscribed',
            'subscribed_at', 'unsubscribed_at'
        ]
        read_only_fields = ['id', 'subscribed_at', 'unsubscribed_at']


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    
    total_notifications = serializers.IntegerField()
    total_sent = serializers.IntegerField()
    total_failed = serializers.IntegerField()
    total_pending = serializers.IntegerField()
    success_rate = serializers.FloatField()
    total_devices = serializers.IntegerField()
    active_devices = serializers.IntegerField()
    devices_by_platform = serializers.DictField()
