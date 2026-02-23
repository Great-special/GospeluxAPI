from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DeviceToken,
    Notification,
    NotificationTemplate,
    NotificationLog,
    TopicSubscription
)


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    """Admin for DeviceToken model"""
    
    list_display = [
        'id', 'user', 'platform', 'device_name', 
        'is_active', 'last_used', 'created_at'
    ]
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['user__email', 'user__username', 'token', 'device_id', 'device_name']
    readonly_fields = ['created_at', 'updated_at', 'last_used']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Device Information', {
            'fields': ('user', 'token', 'platform', 'device_id', 'device_name')
        }),
        ('Status', {
            'fields': ('is_active', 'last_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin for NotificationTemplate model"""
    
    list_display = ['id', 'name', 'title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'title', 'body']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'title', 'body', 'is_active')
        }),
        ('Visual Elements', {
            'fields': ('icon', 'image', 'click_action')
        }),
        ('Additional Data', {
            'fields': ('data',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class NotificationLogInline(admin.TabularInline):
    """Inline for NotificationLog"""
    
    model = NotificationLog
    extra = 0
    readonly_fields = ['device_token', 'fcm_message_id', 'status', 'error_message', 'sent_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification model"""
    
    list_display = [
        'id', 'title', 'notification_type', 'status_badge',
        'total_tokens', 'successful_sends', 'failed_sends',
        'created_by', 'created_at'
    ]
    list_filter = ['status', 'notification_type', 'created_at']
    search_fields = ['title', 'body', 'topic', 'condition']
    readonly_fields = [
        'status', 'total_tokens', 'successful_sends', 
        'failed_sends', 'sent_at', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    inlines = [NotificationLogInline]
    
    fieldsets = (
        ('Notification Content', {
            'fields': ('title', 'body', 'notification_type')
        }),
        ('Targeting', {
            'fields': ('target_users', 'topic', 'condition')
        }),
        ('Visual Elements', {
            'fields': ('icon', 'image', 'click_action')
        }),
        ('Additional Data', {
            'fields': ('data',)
        }),
        ('Delivery Status', {
            'fields': (
                'status', 'total_tokens', 'successful_sends', 
                'failed_sends', 'error_message'
            )
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'sent_at')
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': 'orange',
            'sent': 'green',
            'failed': 'red',
            'partial': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').prefetch_related('target_users')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Admin for NotificationLog model"""
    
    list_display = [
        'id', 'notification', 'device_token', 
        'status_badge', 'fcm_message_id', 'sent_at'
    ]
    list_filter = ['status', 'sent_at']
    search_fields = ['notification__title', 'fcm_message_id', 'error_message']
    readonly_fields = [
        'notification', 'device_token', 'fcm_message_id',
        'status', 'error_message', 'response_data', 'sent_at'
    ]
    date_hierarchy = 'sent_at'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        color = 'green' if obj.status == 'success' else 'red'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'notification', 'device_token', 'device_token__user'
        )


@admin.register(TopicSubscription)
class TopicSubscriptionAdmin(admin.ModelAdmin):
    """Admin for TopicSubscription model"""
    
    list_display = [
        'id', 'user', 'topic', 'device_platform',
        'subscription_badge', 'subscribed_at'
    ]
    list_filter = ['is_subscribed', 'topic', 'subscribed_at']
    search_fields = ['user__email', 'user__username', 'topic']
    readonly_fields = ['subscribed_at', 'unsubscribed_at']
    date_hierarchy = 'subscribed_at'
    
    def device_platform(self, obj):
        """Display device platform"""
        return obj.device_token.platform
    device_platform.short_description = 'Platform'
    
    def subscription_badge(self, obj):
        """Display subscription status as colored badge"""
        color = 'green' if obj.is_subscribed else 'gray'
        text = 'SUBSCRIBED' if obj.is_subscribed else 'UNSUBSCRIBED'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            text
        )
    subscription_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'device_token'
        )
