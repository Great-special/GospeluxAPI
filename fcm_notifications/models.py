from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class DeviceToken(models.Model):
    """Store FCM device tokens for users"""
    
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='device_tokens',
        null=True,
        blank=True
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    device_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'fcm_device_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['platform', 'is_active']),
        ]

    def __str__(self):
        user_info = f"User {self.user.id}" if self.user else "Anonymous"
        return f"{user_info} - {self.platform} - {self.token[:20]}..."

    def mark_as_used(self):
        """Update last_used timestamp"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class NotificationTemplate(models.Model):
    """Reusable notification templates"""
    
    name = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    icon = models.URLField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    click_action = models.URLField(blank=True, null=True)
    data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fcm_notification_templates'
        ordering = ['name']

    def __str__(self):
        return self.name


class Notification(models.Model):
    """Store notification history"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('partial', 'Partially Sent'),
    ]
    
    NOTIFICATION_TYPE_CHOICES = [
        ('single', 'Single User'),
        ('bulk', 'Bulk'),
        ('topic', 'Topic'),
        ('condition', 'Condition'),
    ]
    
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPE_CHOICES,
        default='single'
    )
    target_users = models.ManyToManyField(
        User, 
        related_name='notifications_received',
        blank=True
    )
    topic = models.CharField(max_length=255, blank=True, null=True)
    condition = models.CharField(max_length=500, blank=True, null=True)
    data = models.JSONField(default=dict, blank=True)
    icon = models.URLField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    click_action = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    total_tokens = models.IntegerField(default=0)
    successful_sends = models.IntegerField(default=0)
    failed_sends = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fcm_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.status}"


class NotificationLog(models.Model):
    """Individual notification delivery logs"""
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    device_token = models.ForeignKey(
        DeviceToken,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fcm_message_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True)
    response_data = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fcm_notification_logs'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['notification', 'status']),
            models.Index(fields=['device_token', '-sent_at']),
        ]

    def __str__(self):
        return f"{self.notification.title} - {self.status}"


class TopicSubscription(models.Model):
    """Track topic subscriptions for users"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='topic_subscriptions'
    )
    device_token = models.ForeignKey(
        DeviceToken,
        on_delete=models.CASCADE,
        related_name='topic_subscriptions'
    )
    topic = models.CharField(max_length=255, db_index=True)
    is_subscribed = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'fcm_topic_subscriptions'
        unique_together = ['device_token', 'topic']
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['topic', 'is_subscribed']),
        ]

    def __str__(self):
        return f"{self.user} - {self.topic} - {'Subscribed' if self.is_subscribed else 'Unsubscribed'}"
