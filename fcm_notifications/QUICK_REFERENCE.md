# Quick Reference Guide - Django FCM Notifications

## Installation

```bash
# 1. Copy app to your project
cp -r fcm_notifications /path/to/your/django/project/

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    'rest_framework',
    'fcm_notifications',
]

# 4. Configure Firebase credentials
FCM_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'firebase-credentials.json')

# 5. Add URLs
path('api/fcm/', include('fcm_notifications.urls')),

# 6. Run migrations
python manage.py migrate
```

## Common Commands

### Device Management

```bash
# Register device via API
curl -X POST http://localhost:8000/api/fcm/devices/register/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "fcm_device_token",
    "platform": "android"
  }'

# Get my devices
curl http://localhost:8000/api/fcm/devices/my_devices/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### Send Notifications

```bash
# Send to specific users
curl -X POST http://localhost:8000/api/fcm/notifications/send/ \
  -H "Authorization: Token ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hello",
    "body": "Test message",
    "notification_type": "single",
    "user_ids": [1, 2, 3]
  }'

# Send to topic
curl -X POST http://localhost:8000/api/fcm/notifications/send/ \
  -H "Authorization: Token ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Topic Message",
    "body": "For all subscribers",
    "notification_type": "topic",
    "topic": "general"
  }'
```

### Topic Management

```bash
# Subscribe to topic
curl -X POST http://localhost:8000/api/fcm/topics/subscribe/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic": "news"}'

# Unsubscribe from topic
curl -X POST http://localhost:8000/api/fcm/topics/unsubscribe/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic": "news"}'
```

## Django Management Commands

```bash
# Send scheduled notifications
python manage.py send_scheduled_notifications

# Test with dry run
python manage.py send_scheduled_notifications --dry-run

# Cleanup old logs
python manage.py cleanup_old_logs --days 90

# Cleanup inactive tokens
python manage.py cleanup_inactive_tokens --days 90

# Test FCM connection
python manage.py test_fcm --user-id 1
```

## Python Usage

```python
from fcm_notifications.fcm_service import FCMService

# Send to single device
FCMService.send_notification(
    token='device_token',
    title='Hello',
    body='Test message',
    data={'key': 'value'}
)

# Send to multiple devices
FCMService.send_multicast(
    tokens=['token1', 'token2'],
    title='Bulk Message',
    body='For all users'
)

# Send to topic
FCMService.send_to_topic(
    topic='news',
    title='Breaking News',
    body='Important update'
)

# Subscribe to topic
FCMService.subscribe_to_topic(
    tokens=['token1', 'token2'],
    topic='news'
)
```

## Cron Setup (Quick)

```bash
# Edit crontab
crontab -e

# Add these lines (adjust paths)
*/5 * * * * cd /path/to/project && python manage.py send_scheduled_notifications
0 2 * * * cd /path/to/project && python manage.py cleanup_old_logs
0 3 * * 1 cd /path/to/project && python manage.py cleanup_inactive_tokens
```

## Celery Setup (Quick)

```bash
# Install Redis
sudo apt-get install redis-server

# Start Celery worker
celery -A your_project worker -l info

# Start Celery beat (scheduler)
celery -A your_project beat -l info

# Or run both together
celery -A your_project worker -B -l info
```

## Flutter Integration (Quick)

```dart
// Get FCM token
String? token = await FirebaseMessaging.instance.getToken();

// Register with backend
await http.post(
  Uri.parse('$apiUrl/devices/register/'),
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Token $authToken',
  },
  body: json.encode({
    'token': token,
    'platform': Platform.isAndroid ? 'android' : 'ios',
  }),
);

// Listen for messages
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  print('Notification: ${message.notification?.title}');
});
```

## Web Integration (Quick)

```javascript
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const messaging = getMessaging();

// Get FCM token
const token = await getToken(messaging, { vapidKey: 'YOUR_VAPID_KEY' });

// Register with backend
await fetch('http://api.example.com/api/fcm/devices/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${authToken}`,
  },
  body: JSON.stringify({
    token: token,
    platform: 'web',
  }),
});

// Listen for messages
onMessage(messaging, (payload) => {
  console.log('Message received:', payload);
});
```

## Common Issues & Solutions

### Issue: Firebase Credentials Error
```bash
# Solution: Check credentials file path
FCM_CREDENTIALS_PATH = '/absolute/path/to/firebase-credentials.json'
```

### Issue: Notifications Not Received
```bash
# Check device is active
python manage.py shell
>>> from fcm_notifications.models import DeviceToken
>>> DeviceToken.objects.filter(is_active=True).count()

# Test FCM connection
python manage.py test_fcm --user-id 1
```

### Issue: Cron Not Running
```bash
# Check cron service
sudo service cron status

# Check cron logs
tail -f /var/log/syslog | grep CRON

# Test command manually first
cd /path/to/project && python manage.py send_scheduled_notifications
```

### Issue: Import Error
```bash
# Make sure app is in INSTALLED_APPS
INSTALLED_APPS = [
    'fcm_notifications',  # Add this
]

# Run migrations
python manage.py migrate
```

## Environment Variables

```bash
# .env file
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
CELERY_BROKER_URL=redis://localhost:6379/0
DJANGO_SETTINGS_MODULE=your_project.settings
```

## Testing Checklist

- [ ] Firebase credentials configured
- [ ] App added to INSTALLED_APPS
- [ ] Migrations run successfully
- [ ] Device registered via API
- [ ] Test notification sent successfully
- [ ] Cron jobs or Celery configured
- [ ] Logs directory created and writable
- [ ] Flutter/Web app integrated
- [ ] Admin panel accessible
- [ ] Production settings secured

## Production Checklist

- [ ] Use environment variables for sensitive data
- [ ] Set up proper logging
- [ ] Configure log rotation
- [ ] Set up monitoring/alerts
- [ ] Use HTTPS for API
- [ ] Implement rate limiting
- [ ] Back up Firebase credentials
- [ ] Set up Redis for Celery (if using)
- [ ] Configure supervisord for process management
- [ ] Test notification delivery on all platforms
- [ ] Document API for team
- [ ] Set up error tracking (Sentry)

## Useful URLs

- Django Admin: `http://localhost:8000/admin/`
- API Root: `http://localhost:8000/api/fcm/`
- API Docs: See `API_DOCUMENTATION.md`
- Cron Setup: See `CRON_SETUP.md`
- Main Docs: See `README.md`

## Support

For detailed documentation, see:
- `README.md` - Complete setup guide
- `API_DOCUMENTATION.md` - API reference
- `CRON_SETUP.md` - Cron job setup
- Flutter/Web examples in the project folder
