# FCM Notifications API Documentation

## Base URL
```
http://your-domain.com/api/fcm/
```

## Authentication
All endpoints require authentication using Django REST Framework Token Authentication.

Include the token in the Authorization header:
```
Authorization: Token <your_auth_token>
```

---

## Device Management Endpoints

### 1. Register Device Token
Register a new device for push notifications.

**Endpoint:** `POST /devices/register/`

**Request Body:**
```json
{
    "token": "fcm_device_token_here",
    "platform": "android",  // or "ios", "web"
    "device_id": "unique_device_identifier",  // Optional
    "device_name": "Samsung Galaxy S21"  // Optional
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "message": "Device registered successfully",
    "data": {
        "id": 1,
        "token": "fcm_device_token_here",
        "platform": "android",
        "device_id": "unique_device_identifier",
        "device_name": "Samsung Galaxy S21",
        "is_active": true,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "last_used": "2024-01-15T10:30:00Z"
    }
}
```

### 2. Get My Devices
Retrieve all devices registered by the current user.

**Endpoint:** `GET /devices/my_devices/`

**Response (200 OK):**
```json
{
    "success": true,
    "count": 2,
    "data": [
        {
            "id": 1,
            "token": "device_token_1",
            "platform": "android",
            "device_name": "Phone",
            "is_active": true,
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "id": 2,
            "token": "device_token_2",
            "platform": "web",
            "device_name": "Chrome Browser",
            "is_active": true,
            "created_at": "2024-01-14T09:20:00Z"
        }
    ]
}
```

### 3. Deactivate Device
Deactivate a device (will no longer receive notifications).

**Endpoint:** `POST /devices/{device_id}/deactivate/`

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Device deactivated successfully"
}
```

### 4. Activate Device
Reactivate a previously deactivated device.

**Endpoint:** `POST /devices/{device_id}/activate/`

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Device activated successfully"
}
```

---

## Notification Endpoints

### 1. Send Notification (Admin Only)
Send a push notification immediately.

**Endpoint:** `POST /notifications/send/`

**Permission:** Admin users only

**Request Body - Single User:**
```json
{
    "title": "New Message",
    "body": "You have received a new message from John",
    "notification_type": "single",
    "user_ids": [1, 2, 3],
    "data": {
        "screen": "messages",
        "message_id": "msg_123"
    },
    "icon": "https://example.com/icon.png",
    "image": "https://example.com/image.jpg",
    "click_action": "https://example.com/messages/msg_123"
}
```

**Request Body - Topic:**
```json
{
    "title": "System Maintenance",
    "body": "Scheduled maintenance at 2 AM tonight",
    "notification_type": "topic",
    "topic": "general",
    "data": {
        "type": "maintenance"
    }
}
```

**Request Body - Using Template:**
```json
{
    "template_id": 1,
    "notification_type": "bulk",
    "user_ids": [1, 2, 3, 4, 5]
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "message": "Notification sent successfully",
    "data": {
        "id": 1,
        "title": "New Message",
        "body": "You have received a new message from John",
        "notification_type": "single",
        "status": "sent",
        "total_tokens": 3,
        "successful_sends": 3,
        "failed_sends": 0,
        "sent_at": "2024-01-15T10:35:00Z",
        "created_at": "2024-01-15T10:35:00Z"
    }
}
```

### 2. Send Notification Async (Admin Only)
Queue a notification to be sent in the background using Celery.

**Endpoint:** `POST /notifications/send_async/`

**Permission:** Admin users only

**Request Body:** Same as `/notifications/send/`

**Response (202 Accepted):**
```json
{
    "success": true,
    "message": "Notification queued for sending",
    "data": {
        "id": 2,
        "title": "Bulk Notification",
        "status": "pending",
        "created_at": "2024-01-15T10:40:00Z"
    }
}
```

### 3. List Notifications
Get all notifications (filtered by user permissions).

**Endpoint:** `GET /notifications/`

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 20)

**Response (200 OK):**
```json
{
    "count": 100,
    "next": "http://api.example.com/api/fcm/notifications/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Notification Title",
            "body": "Notification body",
            "notification_type": "single",
            "status": "sent",
            "successful_sends": 5,
            "failed_sends": 0,
            "created_at": "2024-01-15T10:35:00Z"
        }
    ]
}
```

### 4. Get Notification Details
Get detailed information about a specific notification.

**Endpoint:** `GET /notifications/{notification_id}/`

**Response (200 OK):**
```json
{
    "id": 1,
    "title": "Notification Title",
    "body": "Notification body",
    "notification_type": "single",
    "status": "sent",
    "total_tokens": 5,
    "successful_sends": 5,
    "failed_sends": 0,
    "data": {"key": "value"},
    "icon": "https://example.com/icon.png",
    "image": "https://example.com/image.jpg",
    "click_action": "https://example.com/action",
    "sent_at": "2024-01-15T10:35:00Z",
    "created_at": "2024-01-15T10:35:00Z"
}
```

### 5. Get Notification Logs
Get delivery logs for a specific notification.

**Endpoint:** `GET /notifications/{notification_id}/logs/`

**Response (200 OK):**
```json
{
    "success": true,
    "count": 5,
    "data": [
        {
            "id": 1,
            "notification": 1,
            "device_token": 1,
            "device_token_info": {
                "platform": "android",
                "device_name": "Samsung Phone"
            },
            "fcm_message_id": "success_1",
            "status": "success",
            "error_message": null,
            "sent_at": "2024-01-15T10:35:00Z"
        },
        {
            "id": 2,
            "notification": 1,
            "device_token": 2,
            "device_token_info": {
                "platform": "ios",
                "device_name": "iPhone"
            },
            "status": "failed",
            "error_message": "Token is unregistered or invalid",
            "sent_at": "2024-01-15T10:35:00Z"
        }
    ]
}
```

### 6. Get Notification Statistics (Admin Only)
Get overall notification statistics.

**Endpoint:** `GET /notifications/stats/`

**Permission:** Admin users only

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "total_notifications": 150,
        "total_sent": 145,
        "total_failed": 3,
        "total_pending": 2,
        "success_rate": 96.67,
        "total_devices": 500,
        "active_devices": 480,
        "devices_by_platform": {
            "android": 250,
            "ios": 180,
            "web": 50
        }
    }
}
```

---

## Topic Management Endpoints

### 1. Subscribe to Topic
Subscribe user's device(s) to a topic.

**Endpoint:** `POST /topics/subscribe/`

**Request Body:**
```json
{
    "topic": "news",
    "device_token_id": 1  // Optional - subscribes all devices if omitted
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Successfully subscribed to topic: news",
    "details": {
        "success_count": 1,
        "failure_count": 0,
        "errors": []
    }
}
```

### 2. Unsubscribe from Topic
Unsubscribe user's device(s) from a topic.

**Endpoint:** `POST /topics/unsubscribe/`

**Request Body:**
```json
{
    "topic": "news",
    "device_token_id": 1  // Optional - unsubscribes all devices if omitted
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Successfully unsubscribed from topic: news",
    "details": {
        "success_count": 1,
        "failure_count": 0,
        "errors": []
    }
}
```

### 3. Get My Topics
Get all topics the current user is subscribed to.

**Endpoint:** `GET /topics/my_topics/`

**Response (200 OK):**
```json
{
    "success": true,
    "count": 3,
    "topics": ["general", "news", "updates"]
}
```

### 4. List Topic Subscriptions
Get detailed list of all topic subscriptions.

**Endpoint:** `GET /topics/`

**Response (200 OK):**
```json
{
    "success": true,
    "count": 5,
    "data": [
        {
            "id": 1,
            "user": 1,
            "user_email": "user@example.com",
            "device_token": 1,
            "device_platform": "android",
            "topic": "news",
            "is_subscribed": true,
            "subscribed_at": "2024-01-15T10:00:00Z"
        }
    ]
}
```

---

## Template Management Endpoints

### 1. List Templates (Admin Only)
Get all notification templates.

**Endpoint:** `GET /templates/`

**Permission:** Admin users only

**Response (200 OK):**
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "name": "welcome_notification",
            "title": "Welcome!",
            "body": "Welcome to our app",
            "icon": "https://example.com/icon.png",
            "data": {"type": "welcome"},
            "is_active": true,
            "created_at": "2024-01-10T08:00:00Z"
        }
    ]
}
```

### 2. Create Template (Admin Only)
Create a new notification template.

**Endpoint:** `POST /templates/`

**Permission:** Admin users only

**Request Body:**
```json
{
    "name": "order_shipped",
    "title": "Order Shipped",
    "body": "Your order has been shipped",
    "icon": "https://example.com/shipping-icon.png",
    "image": "https://example.com/package.jpg",
    "click_action": "https://example.com/orders",
    "data": {
        "type": "order",
        "action": "shipped"
    },
    "is_active": true
}
```

**Response (201 Created):**
```json
{
    "id": 2,
    "name": "order_shipped",
    "title": "Order Shipped",
    "body": "Your order has been shipped",
    "icon": "https://example.com/shipping-icon.png",
    "data": {"type": "order", "action": "shipped"},
    "is_active": true,
    "created_at": "2024-01-15T11:00:00Z"
}
```

### 3. Get Active Templates (Admin Only)
Get all active templates.

**Endpoint:** `GET /templates/active/`

**Permission:** Admin users only

**Response (200 OK):**
```json
{
    "success": true,
    "count": 8,
    "data": [
        {
            "id": 1,
            "name": "welcome_notification",
            "title": "Welcome!",
            "is_active": true
        }
    ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error",
    "message": "Error details"
}
```

---

## Rate Limiting

To prevent abuse, consider implementing rate limiting on your API endpoints. Recommended limits:

- Device registration: 10 requests per hour per user
- Notification sending: 100 requests per hour per admin
- Topic subscription: 50 requests per hour per user

---

## Webhook Events (Optional)

You can implement webhooks to notify your system of notification events:

### Event Types
- `notification.sent` - Notification successfully sent
- `notification.failed` - Notification failed to send
- `device.registered` - New device registered
- `device.deactivated` - Device deactivated
- `topic.subscribed` - User subscribed to topic
- `topic.unsubscribed` - User unsubscribed from topic

---

## Best Practices

1. **Token Management**
   - Refresh tokens when they expire
   - Remove inactive tokens regularly
   - Validate tokens before sending

2. **Notification Content**
   - Keep titles under 50 characters
   - Keep body text under 200 characters for best display
   - Always include relevant data payload

3. **Topics**
   - Use descriptive topic names
   - Keep topic names lowercase with underscores
   - Document available topics for developers

4. **Error Handling**
   - Always check response status codes
   - Handle token expiration gracefully
   - Implement retry logic for failed sends

5. **Testing**
   - Test on all target platforms
   - Verify notification appearance
   - Test deep links and actions
   - Monitor delivery rates

---

## Support

For issues or questions about the API, please contact your system administrator or refer to the main documentation.
