from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import DeviceToken, Notification, NotificationTemplate, TopicSubscription
from .fcm_service import FCMService

User = get_user_model()


class DeviceTokenModelTest(TestCase):
    """Test cases for DeviceToken model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_device_token(self):
        """Test creating a device token"""
        device = DeviceToken.objects.create(
            user=self.user,
            token='test_fcm_token_12345',
            platform='android',
            device_id='device_001',
            device_name='Test Device'
        )
        
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.platform, 'android')
        self.assertTrue(device.is_active)
        self.assertIsNotNone(device.created_at)
    
    def test_device_token_unique(self):
        """Test that device tokens must be unique"""
        DeviceToken.objects.create(
            user=self.user,
            token='unique_token',
            platform='android'
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            DeviceToken.objects.create(
                user=self.user,
                token='unique_token',
                platform='ios'
            )
    
    def test_mark_as_used(self):
        """Test marking device as used"""
        device = DeviceToken.objects.create(
            user=self.user,
            token='test_token',
            platform='web'
        )
        
        original_time = device.last_used
        device.mark_as_used()
        device.refresh_from_db()
        
        self.assertNotEqual(device.last_used, original_time)


class NotificationModelTest(TestCase):
    """Test cases for Notification model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            title='Test Notification',
            body='Test message body',
            notification_type='single',
            created_by=self.user
        )
        
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.status, 'pending')
        self.assertEqual(notification.total_tokens, 0)
    
    def test_notification_status_choices(self):
        """Test notification status choices"""
        notification = Notification.objects.create(
            title='Test',
            body='Body',
            status='sent',
            created_by=self.user
        )
        
        self.assertEqual(notification.status, 'sent')


class DeviceTokenAPITest(APITestCase):
    """Test cases for Device Token API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_register_device(self):
        """Test registering a device token"""
        data = {
            'token': 'test_fcm_token_abc123',
            'platform': 'android',
            'device_id': 'device_123',
            'device_name': 'Test Phone'
        }
        
        response = self.client.post('/api/fcm/devices/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['platform'], 'android')
        
        # Verify device was created in database
        device = DeviceToken.objects.get(token='test_fcm_token_abc123')
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.platform, 'android')
    
    def test_register_device_invalid_platform(self):
        """Test registering device with invalid platform"""
        data = {
            'token': 'test_token',
            'platform': 'invalid_platform'
        }
        
        response = self.client.post('/api/fcm/devices/register/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_my_devices(self):
        """Test getting user's devices"""
        # Create devices
        DeviceToken.objects.create(
            user=self.user,
            token='token1',
            platform='android'
        )
        DeviceToken.objects.create(
            user=self.user,
            token='token2',
            platform='ios'
        )
        
        response = self.client.get('/api/fcm/devices/my_devices/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 2)
    
    def test_deactivate_device(self):
        """Test deactivating a device"""
        device = DeviceToken.objects.create(
            user=self.user,
            token='token_to_deactivate',
            platform='web'
        )
        
        response = self.client.post(f'/api/fcm/devices/{device.id}/deactivate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify device was deactivated
        device.refresh_from_db()
        self.assertFalse(device.is_active)


class NotificationAPITest(APITestCase):
    """Test cases for Notification API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.admin)
    
    @patch('fcm_notifications.fcm_service.FCMService.send_to_topic')
    def test_send_topic_notification(self, mock_send):
        """Test sending notification to topic"""
        mock_send.return_value = {
            'success': True,
            'message_id': 'test_message_id',
            'error': None
        }
        
        data = {
            'title': 'Test Topic Notification',
            'body': 'Test message',
            'notification_type': 'topic',
            'topic': 'general',
            'data': {'key': 'value'}
        }
        
        response = self.client.post('/api/fcm/notifications/send/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify notification was created
        notification = Notification.objects.get(title='Test Topic Notification')
        self.assertEqual(notification.status, 'sent')
        self.assertEqual(notification.topic, 'general')
    
    @patch('fcm_notifications.fcm_service.FCMService.send_multicast')
    def test_send_bulk_notification(self, mock_send):
        """Test sending bulk notification"""
        # Create device tokens
        DeviceToken.objects.create(
            user=self.user,
            token='token1',
            platform='android',
            is_active=True
        )
        
        mock_send.return_value = {
            'success_count': 1,
            'failure_count': 0,
            'failed_tokens': []
        }
        
        data = {
            'title': 'Bulk Notification',
            'body': 'Test bulk message',
            'notification_type': 'bulk',
            'user_ids': [self.user.id]
        }
        
        response = self.client.post('/api/fcm/notifications/send/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])


class FCMServiceTest(TestCase):
    """Test cases for FCM Service"""
    
    @patch('fcm_notifications.fcm_service.messaging.send')
    @patch('fcm_notifications.fcm_service.FCMService.initialize')
    def test_send_notification(self, mock_init, mock_send):
        """Test sending a single notification"""
        mock_send.return_value = 'test_message_id'
        
        result = FCMService.send_notification(
            token='test_token',
            title='Test',
            body='Test message',
            data={'key': 'value'}
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'test_message_id')
        self.assertIsNone(result['error'])
    
    @patch('fcm_notifications.fcm_service.messaging.send_multicast')
    @patch('fcm_notifications.fcm_service.FCMService.initialize')
    def test_send_multicast(self, mock_init, mock_send):
        """Test sending multicast notification"""
        mock_response = MagicMock()
        mock_response.success_count = 3
        mock_response.failure_count = 0
        mock_response.responses = [
            MagicMock(success=True),
            MagicMock(success=True),
            MagicMock(success=True)
        ]
        mock_send.return_value = mock_response
        
        result = FCMService.send_multicast(
            tokens=['token1', 'token2', 'token3'],
            title='Test',
            body='Test message'
        )
        
        self.assertEqual(result['success_count'], 3)
        self.assertEqual(result['failure_count'], 0)
        self.assertEqual(len(result['failed_tokens']), 0)


class TopicSubscriptionTest(APITestCase):
    """Test cases for Topic Subscription"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.device = DeviceToken.objects.create(
            user=self.user,
            token='test_token',
            platform='android',
            is_active=True
        )
    
    @patch('fcm_notifications.fcm_service.FCMService.subscribe_to_topic')
    def test_subscribe_to_topic(self, mock_subscribe):
        """Test subscribing to a topic"""
        mock_subscribe.return_value = {
            'success_count': 1,
            'failure_count': 0,
            'errors': []
        }
        
        data = {
            'topic': 'news',
            'device_token_id': self.device.id
        }
        
        response = self.client.post('/api/fcm/topics/subscribe/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify subscription was created
        subscription = TopicSubscription.objects.get(
            user=self.user,
            device_token=self.device,
            topic='news'
        )
        self.assertTrue(subscription.is_subscribed)
    
    @patch('fcm_notifications.fcm_service.FCMService.unsubscribe_from_topic')
    def test_unsubscribe_from_topic(self, mock_unsubscribe):
        """Test unsubscribing from a topic"""
        # Create subscription first
        TopicSubscription.objects.create(
            user=self.user,
            device_token=self.device,
            topic='news',
            is_subscribed=True
        )
        
        mock_unsubscribe.return_value = {
            'success_count': 1,
            'failure_count': 0,
            'errors': []
        }
        
        data = {'topic': 'news'}
        
        response = self.client.post('/api/fcm/topics/unsubscribe/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_get_my_topics(self):
        """Test getting user's subscribed topics"""
        # Create subscriptions
        TopicSubscription.objects.create(
            user=self.user,
            device_token=self.device,
            topic='news',
            is_subscribed=True
        )
        TopicSubscription.objects.create(
            user=self.user,
            device_token=self.device,
            topic='sports',
            is_subscribed=True
        )
        
        response = self.client.get('/api/fcm/topics/my_topics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIn('news', response.data['topics'])
        self.assertIn('sports', response.data['topics'])


class NotificationTemplateTest(TestCase):
    """Test cases for Notification Templates"""
    
    def test_create_template(self):
        """Test creating a notification template"""
        template = NotificationTemplate.objects.create(
            name='welcome',
            title='Welcome!',
            body='Welcome to our app',
            data={'type': 'welcome'}
        )
        
        self.assertEqual(template.name, 'welcome')
        self.assertTrue(template.is_active)
    
    def test_template_name_unique(self):
        """Test that template names must be unique"""
        NotificationTemplate.objects.create(
            name='unique_template',
            title='Test',
            body='Test body'
        )
        
        with self.assertRaises(Exception):
            NotificationTemplate.objects.create(
                name='unique_template',
                title='Another',
                body='Another body'
            )
