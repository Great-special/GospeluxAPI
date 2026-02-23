from django.apps import AppConfig


class FcmNotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fcm_notifications'
    verbose_name = 'FCM Notifications'
    
    def ready(self):
        """Initialize FCM service when app is ready"""
        from .fcm_service import FCMService
        try:
            FCMService.initialize()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize FCM service: {e}")
