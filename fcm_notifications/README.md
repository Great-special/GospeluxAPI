# Django FCM Notifications App

A complete, production-ready Django application for sending push notifications to Flutter mobile apps and web applications using Firebase Cloud Messaging (FCM).

## Features

- ✅ **Multi-Platform Support**: Android, iOS, and Web
- ✅ **Multiple Notification Types**: Single user, bulk, topic-based, and condition-based
- ✅ **Device Management**: Register, track, and manage device tokens
- ✅ **Topic Subscriptions**: Subscribe/unsubscribe devices to topics
- ✅ **Notification Templates**: Create reusable notification templates
- ✅ **Notification History**: Complete audit trail with delivery logs
- ✅ **Async Processing**: Celery integration for background task processing
- ✅ **Scheduled Notifications**: Schedule notifications for future delivery
- ✅ **Admin Interface**: Full Django admin integration
- ✅ **REST API**: Complete REST API with DRF
- ✅ **Statistics**: Track notification delivery rates and device analytics

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [API Endpoints](#api-endpoints)
5. [Flutter Integration](#flutter-integration)
6. [Web Integration](#web-integration)
7. [Admin Panel](#admin-panel)
8. [Celery Tasks](#celery-tasks)
9. [Testing](#testing)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add to Django Project

Add the app to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'rest_framework',
    'fcm_notifications',
]
```

### 3. Configure URLs

Add to your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/fcm/', include('fcm_notifications.urls')),
    path('api-auth/', include('rest_framework.urls')),
]
```

### 4. Run Migrations

```bash
python manage.py makemigrations fcm_notifications
python manage.py migrate
```

## Configuration

### 1. Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. Go to **Project Settings** > **Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file as `firebase-credentials.json`
6. Place it in your project root or configure path in settings

### 2. Django Settings

Add to your `settings.py`:

```python
# FCM Configuration
FCM_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'firebase-credentials.json')

# Or use environment variable
# FCM_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')

# REST Framework
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

# Celery Configuration (Optional, for async notifications)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-scheduled-notifications': {
        'task': 'fcm_notifications.tasks.send_scheduled_notifications',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-old-logs': {
        'task': 'fcm_notifications.tasks.cleanup_old_logs',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'cleanup-inactive-tokens': {
        'task': 'fcm_notifications.tasks.cleanup_inactive_tokens',
        'schedule': crontab(day_of_week=1, hour=0, minute=0),  # Weekly on Monday
    },
}
```

### 3. Environment Variables (Optional)

Create a `.env` file:

```env
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
CELERY_BROKER_URL=redis://localhost:6379/0
```

## Usage

### Register Device Token

```python
from fcm_notifications.models import DeviceToken

# Register a device
device = DeviceToken.objects.create(
    user=user,
    token='fcm_device_token_here',
    platform='android',  # or 'ios', 'web'
    device_id='unique_device_id',
    device_name='User Phone'
)
```

### Send Notification

```python
from fcm_notifications.fcm_service import FCMService

# Send to single device
result = FCMService.send_notification(
    token='device_fcm_token',
    title='Hello!',
    body='This is a test notification',
    data={'screen': 'home', 'item_id': '123'},
    image='https://example.com/image.jpg',
    click_action='https://example.com'
)

# Send to multiple devices
result = FCMService.send_multicast(
    tokens=['token1', 'token2', 'token3'],
    title='Bulk Notification',
    body='Message for multiple users',
    data={'type': 'announcement'}
)

# Send to topic
result = FCMService.send_to_topic(
    topic='news',
    title='Breaking News',
    body='Important update',
    data={'category': 'news'}
)
```

### Subscribe to Topic

```python
from fcm_notifications.fcm_service import FCMService

# Subscribe device(s) to topic
result = FCMService.subscribe_to_topic(
    tokens=['token1', 'token2'],
    topic='general'
)

# Unsubscribe from topic
result = FCMService.unsubscribe_from_topic(
    tokens=['token1', 'token2'],
    topic='general'
)
```

## API Endpoints

### Device Management

#### Register Device
```http
POST /api/fcm/devices/register/
Content-Type: application/json
Authorization: Token <your_token>

{
    "token": "fcm_device_token",
    "platform": "android",
    "device_id": "unique_device_id",
    "device_name": "Samsung Galaxy S21"
}
```

#### Get My Devices
```http
GET /api/fcm/devices/my_devices/
Authorization: Token <your_token>
```

#### Deactivate Device
```http
POST /api/fcm/devices/{id}/deactivate/
Authorization: Token <your_token>
```

### Notifications

#### Send Notification (Admin Only)
```http
POST /api/fcm/notifications/send/
Content-Type: application/json
Authorization: Token <admin_token>

{
    "title": "Test Notification",
    "body": "This is a test message",
    "notification_type": "single",
    "user_ids": [1, 2, 3],
    "data": {
        "screen": "home",
        "item_id": "123"
    },
    "icon": "https://example.com/icon.png",
    "image": "https://example.com/image.jpg",
    "click_action": "https://example.com"
}
```

#### Send to Topic
```http
POST /api/fcm/notifications/send/
Content-Type: application/json
Authorization: Token <admin_token>

{
    "title": "Topic Notification",
    "body": "Message for all subscribers",
    "notification_type": "topic",
    "topic": "general",
    "data": {"type": "announcement"}
}
```

#### Send Async (Background)
```http
POST /api/fcm/notifications/send_async/
Content-Type: application/json
Authorization: Token <admin_token>

{
    "title": "Async Notification",
    "body": "This will be sent in background",
    "notification_type": "bulk",
    "user_ids": [1, 2, 3, 4, 5]
}
```

#### Get Notification Logs
```http
GET /api/fcm/notifications/{id}/logs/
Authorization: Token <your_token>
```

#### Get Statistics (Admin Only)
```http
GET /api/fcm/notifications/stats/
Authorization: Token <admin_token>
```

### Topics

#### Subscribe to Topic
```http
POST /api/fcm/topics/subscribe/
Content-Type: application/json
Authorization: Token <your_token>

{
    "topic": "general",
    "device_token_id": 1  // Optional, subscribes all if omitted
}
```

#### Unsubscribe from Topic
```http
POST /api/fcm/topics/unsubscribe/
Content-Type: application/json
Authorization: Token <your_token>

{
    "topic": "general"
}
```

#### Get My Topics
```http
GET /api/fcm/topics/my_topics/
Authorization: Token <your_token>
```

### Templates

#### List Templates
```http
GET /api/fcm/templates/
Authorization: Token <admin_token>
```

#### Create Template
```http
POST /api/fcm/templates/
Content-Type: application/json
Authorization: Token <admin_token>

{
    "name": "welcome_notification",
    "title": "Welcome to our app!",
    "body": "Thank you for joining us",
    "icon": "https://example.com/icon.png",
    "data": {"type": "welcome"}
}
```

#### Send Using Template
```http
POST /api/fcm/notifications/send/
Content-Type: application/json
Authorization: Token <admin_token>

{
    "template_id": 1,
    "notification_type": "single",
    "user_ids": [1, 2, 3]
}
```

## Flutter Integration

See `flutter_integration_example.dart` for complete Flutter setup.

### Key Steps:

1. **Add Dependencies**:
```yaml
dependencies:
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.9
  http: ^1.1.0
```

2. **Initialize Firebase**:
```dart
await Firebase.initializeApp();
```

3. **Request Permission** (iOS):
```dart
NotificationSettings settings = await FirebaseMessaging.instance.requestPermission();
```

4. **Get Token**:
```dart
String? token = await FirebaseMessaging.instance.getToken();
```

5. **Register with Backend**:
```dart
await http.post(
  Uri.parse('$apiBaseUrl/devices/register/'),
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Token $authToken',
  },
  body: json.encode({
    'token': token,
    'platform': Platform.isAndroid ? 'android' : 'ios',
  }),
);
```

6. **Handle Messages**:
```dart
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  print('Notification: ${message.notification?.title}');
});
```

## Web Integration

See `web_integration_example.js` for complete web setup.

### Key Steps:

1. **Install Firebase**:
```bash
npm install firebase
```

2. **Initialize Firebase**:
```javascript
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);
```

3. **Request Permission**:
```javascript
const permission = await Notification.requestPermission();
if (permission === 'granted') {
  const token = await getToken(messaging, { vapidKey: VAPID_KEY });
}
```

4. **Create Service Worker** (`firebase-messaging-sw.js`):
```javascript
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  // Handle background message
});
```

## Admin Panel

Access the Django admin panel at `/admin/` to:

- View and manage device tokens
- Create notification templates
- View notification history
- Check delivery logs
- Monitor statistics
- Manage topic subscriptions

## Task Scheduling Options

You can choose between **Celery** (distributed task queue) or **Cron Jobs** (simple scheduled tasks) for background processing.

### Option 1: Celery (Recommended for Production)

#### Start Celery Worker

```bash
celery -A your_project_name worker -l info
```

#### Start Celery Beat (for scheduled tasks)

```bash
celery -A your_project_name beat -l info
```

#### Available Celery Tasks

1. **send_notification_task**: Send notification asynchronously
2. **send_scheduled_notifications**: Send scheduled notifications (runs every 5 minutes)
3. **cleanup_old_logs**: Delete logs older than 90 days (runs daily)
4. **cleanup_inactive_tokens**: Delete inactive tokens (runs weekly)

### Option 2: Cron Jobs (Simpler Setup)

The app includes Django management commands that can be run via cron jobs.

#### Available Management Commands

```bash
# Send scheduled notifications
python manage.py send_scheduled_notifications

# Cleanup old logs (default: 90 days)
python manage.py cleanup_old_logs --days 90

# Cleanup inactive tokens (default: 90 days)
python manage.py cleanup_inactive_tokens --days 90

# Test FCM connection
python manage.py test_fcm
```

#### Setup Cron Jobs

Edit your crontab:

```bash
crontab -e
```

Add these lines (adjust paths):

```bash
# Send scheduled notifications every 5 minutes
*/5 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py send_scheduled_notifications >> /var/log/fcm_scheduled.log 2>&1

# Cleanup old logs daily at 2 AM
0 2 * * * cd /path/to/project && /path/to/venv/bin/python manage.py cleanup_old_logs >> /var/log/fcm_cleanup.log 2>&1

# Cleanup inactive tokens weekly on Monday at 3 AM
0 3 * * 1 cd /path/to/project && /path/to/venv/bin/python manage.py cleanup_inactive_tokens >> /var/log/fcm_cleanup.log 2>&1
```

**See [CRON_SETUP.md](CRON_SETUP.md) for detailed cron setup instructions.**

### Choosing Between Celery and Cron

**Use Celery when:**
- Need distributed task processing
- High-volume notifications
- Complex workflows
- Multiple workers
- Real-time processing

**Use Cron when:**
- Simple scheduling needs
- Limited resources
- Single server deployment
- Prefer simpler setup
- Small to medium scale

## Testing

### Test Notification Send

```bash
python manage.py shell
```

```python
from fcm_notifications.fcm_service import FCMService
from fcm_notifications.models import DeviceToken

# Get a device token
device = DeviceToken.objects.filter(is_active=True).first()

# Send test notification
result = FCMService.send_notification(
    token=device.token,
    title='Test Notification',
    body='This is a test message',
    data={'test': True}
)

print(result)
```

### Test API Endpoints

```bash
# Get auth token
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Register device
curl -X POST http://localhost:8000/api/fcm/devices/register/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "token": "fcm_device_token",
    "platform": "web",
    "device_name": "Test Device"
  }'

# Send notification
curl -X POST http://localhost:8000/api/fcm/notifications/send/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "title": "Test",
    "body": "Test message",
    "notification_type": "topic",
    "topic": "test"
  }'
```

## Troubleshooting

### Common Issues

1. **Firebase Credentials Error**:
   - Ensure `firebase-credentials.json` is in the correct path
   - Check file permissions
   - Verify credentials are valid in Firebase Console

2. **Token Registration Failed**:
   - Check user authentication
   - Verify FCM token format
   - Ensure device platform is valid (android/ios/web)

3. **Notifications Not Received**:
   - Verify device token is active
   - Check Firebase Console for quota limits
   - Ensure app has notification permissions
   - Check if token is registered correctly

4. **Celery Tasks Not Running**:
   - Ensure Redis is running
   - Check Celery worker is started
   - Verify Celery beat is running for scheduled tasks

## Security Considerations

1. **Protect Firebase Credentials**: Never commit `firebase-credentials.json` to version control
2. **Use Environment Variables**: Store sensitive config in environment variables
3. **API Authentication**: Always require authentication for API endpoints
4. **Token Validation**: Validate and sanitize all input data
5. **Rate Limiting**: Implement rate limiting on notification endpoints
6. **Permissions**: Use proper Django permissions for admin endpoints

## License

This project is provided as-is for integration into your Django projects.

## Support

For issues and questions:
- Check Firebase documentation
- Review Django REST Framework docs
- Check application logs for detailed error messages

---

**Note**: This is a complete, production-ready Django app. Make sure to test thoroughly before deploying to production and adjust configurations based on your specific requirements.
