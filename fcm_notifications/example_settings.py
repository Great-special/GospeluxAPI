# Add this to your Django project's settings.py

"""
FCM Notifications App Settings Configuration
"""

# ============================================
# INSTALLED APPS
# ============================================
# Add to INSTALLED_APPS:
INSTALLED_APPS = [
    # ... your other apps
    'rest_framework',
    'fcm_notifications',
]

# ============================================
# REST FRAMEWORK SETTINGS
# ============================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ============================================
# FIREBASE CLOUD MESSAGING (FCM) SETTINGS
# ============================================
# Path to your Firebase service account JSON file
# Download from Firebase Console > Project Settings > Service Accounts
FCM_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'firebase-credentials.json')

# Alternative: Use environment variable
# FCM_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')

# ============================================
# CELERY SETTINGS (for async notifications)
# ============================================
# Celery broker URL (using Redis)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule for periodic tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-scheduled-notifications': {
        'task': 'fcm_notifications.tasks.send_scheduled_notifications',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
    'cleanup-old-logs': {
        'task': 'fcm_notifications.tasks.cleanup_old_logs',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
    },
    'cleanup-inactive-tokens': {
        'task': 'fcm_notifications.tasks.cleanup_inactive_tokens',
        'schedule': crontab(day_of_week=1, hour=0, minute=0),  # Run weekly on Monday
    },
}

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'fcm_notifications.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'fcm_notifications': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
