import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from django.utils import timezone
from typing import List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class FCMService:
    """Service class for Firebase Cloud Messaging operations"""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if not cls._initialized:
            try:
                # Check if already initialized
                firebase_admin.get_app()
                cls._initialized = True
            except ValueError:
                # Initialize with service account
                cred_path = getattr(settings, 'FCM_CREDENTIALS_PATH', None)
                
                if cred_path:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                else:
                    # Initialize with default credentials (for Google Cloud environment)
                    firebase_admin.initialize_app()
                
                cls._initialized = True
                logger.info("Firebase Admin SDK initialized successfully")
    
    @classmethod
    def send_notification(
        cls,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image: Optional[str] = None,
        icon: Optional[str] = None,
        click_action: Optional[str] = None,
        badge: Optional[int] = None,
        sound: Optional[str] = None,
        priority: str = 'high',
        ttl: Optional[int] = None,
    ) -> Dict:
        """
        Send notification to a single device
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload
            image: Image URL for notification
            icon: Icon URL for notification
            click_action: URL to open on notification click
            badge: Badge count (iOS)
            sound: Sound file name
            priority: Notification priority ('high' or 'normal')
            ttl: Time to live in seconds
            
        Returns:
            Dict with success status and message_id or error
        """
        cls.initialize()
        
        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )
            
            # Build Android config
            android_config = messaging.AndroidConfig(
                priority=priority,
                ttl=timezone.timedelta(seconds=ttl) if ttl else None,
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    icon=icon,
                    sound=sound or 'default',
                    click_action=click_action,
                    image=image,
                )
            )
            
            # Build iOS config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body,
                        ),
                        badge=badge,
                        sound=sound or 'default',
                    )
                )
            )
            
            # Build web config
            web_config = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon=icon,
                    image=image,
                    badge=icon,
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=click_action
                ) if click_action else None
            )
            
            # Build message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config,
                webpush=web_config,
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"Successfully sent message: {response}")
            
            return {
                'success': True,
                'message_id': response,
                'error': None
            }
            
        except messaging.UnregisteredError:
            logger.warning(f"Token is unregistered: {token}")
            return {
                'success': False,
                'message_id': None,
                'error': 'Token is unregistered or invalid'
            }
        except messaging.InvalidArgumentError as e:
            logger.error(f"Invalid argument: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': f'Invalid argument: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }
    
    @classmethod
    def send_multicast(
        cls,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image: Optional[str] = None,
        icon: Optional[str] = None,
        click_action: Optional[str] = None,
        batch_size: int = 500,
    ) -> Dict:
        """
        Send notification to multiple devices (up to 500 at a time)
        
        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            image: Image URL
            icon: Icon URL
            click_action: URL to open on click
            batch_size: Batch size for multicast (max 500)
            
        Returns:
            Dict with success count, failure count, and failed tokens
        """
        cls.initialize()
        
        total_success = 0
        total_failure = 0
        failed_tokens = []
        
        # Process in batches
        for i in range(0, len(tokens), batch_size):
            batch_tokens = tokens[i:i + batch_size]
            
            try:
                # Build notification
                notification = messaging.Notification(
                    title=title,
                    body=body,
                    image=image
                )
                
                # Build Android config
                android_config = messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        title=title,
                        body=body,
                        icon=icon,
                        sound='default',
                        click_action=click_action,
                        image=image,
                    )
                )
                
                # Build iOS config
                apns_config = messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                            sound='default',
                        )
                    )
                )
                
                # Build web config
                web_config = messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        icon=icon,
                        image=image,
                        badge=icon,
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=click_action
                    ) if click_action else None
                )
                
                # Build multicast message
                message = messaging.MulticastMessage(
                    notification=notification,
                    data=data or {},
                    tokens=batch_tokens,
                    android=android_config,
                    apns=apns_config,
                    webpush=web_config,
                )
                
                # Send multicast
                response = messaging.send_multicast(message)
                
                total_success += response.success_count
                total_failure += response.failure_count
                
                # Collect failed tokens
                if response.failure_count > 0:
                    for idx, resp in enumerate(response.responses):
                        if not resp.success:
                            failed_tokens.append({
                                'token': batch_tokens[idx],
                                'error': str(resp.exception) if resp.exception else 'Unknown error'
                            })
                
                logger.info(
                    f"Batch {i//batch_size + 1}: "
                    f"Success: {response.success_count}, "
                    f"Failure: {response.failure_count}"
                )
                
            except Exception as e:
                logger.error(f"Error sending multicast batch: {str(e)}")
                total_failure += len(batch_tokens)
                for token in batch_tokens:
                    failed_tokens.append({
                        'token': token,
                        'error': str(e)
                    })
        
        return {
            'success_count': total_success,
            'failure_count': total_failure,
            'failed_tokens': failed_tokens
        }
    
    @classmethod
    def send_to_topic(
        cls,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image: Optional[str] = None,
        icon: Optional[str] = None,
        click_action: Optional[str] = None,
    ) -> Dict:
        """
        Send notification to a topic
        
        Args:
            topic: Topic name
            title: Notification title
            body: Notification body
            data: Additional data payload
            image: Image URL
            icon: Icon URL
            click_action: URL to open on click
            
        Returns:
            Dict with success status and message_id or error
        """
        cls.initialize()
        
        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )
            
            # Build Android config
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    icon=icon,
                    sound='default',
                    click_action=click_action,
                    image=image,
                )
            )
            
            # Build iOS config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body,
                        ),
                        sound='default',
                    )
                )
            )
            
            # Build web config
            web_config = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon=icon,
                    image=image,
                    badge=icon,
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=click_action
                ) if click_action else None
            )
            
            # Build message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                topic=topic,
                android=android_config,
                apns=apns_config,
                webpush=web_config,
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"Successfully sent topic message: {response}")
            
            return {
                'success': True,
                'message_id': response,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error sending topic notification: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }
    
    @classmethod
    def send_to_condition(
        cls,
        condition: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image: Optional[str] = None,
        icon: Optional[str] = None,
        click_action: Optional[str] = None,
    ) -> Dict:
        """
        Send notification based on topic condition
        
        Args:
            condition: Condition string (e.g., "'TopicA' in topics && 'TopicB' in topics")
            title: Notification title
            body: Notification body
            data: Additional data payload
            image: Image URL
            icon: Icon URL
            click_action: URL to open on click
            
        Returns:
            Dict with success status and message_id or error
        """
        cls.initialize()
        
        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image
            )
            
            # Build message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                condition=condition,
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"Successfully sent condition message: {response}")
            
            return {
                'success': True,
                'message_id': response,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error sending condition notification: {str(e)}")
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }
    
    @classmethod
    def subscribe_to_topic(cls, tokens: Union[str, List[str]], topic: str) -> Dict:
        """
        Subscribe device tokens to a topic
        
        Args:
            tokens: Single token or list of tokens
            topic: Topic name
            
        Returns:
            Dict with success count and failure count
        """
        cls.initialize()
        
        if isinstance(tokens, str):
            tokens = [tokens]
        
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            
            logger.info(
                f"Topic subscription - Success: {response.success_count}, "
                f"Failure: {response.failure_count}"
            )
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [str(e) for e in response.errors] if response.errors else []
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to topic: {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'errors': [str(e)]
            }
    
    @classmethod
    def unsubscribe_from_topic(cls, tokens: Union[str, List[str]], topic: str) -> Dict:
        """
        Unsubscribe device tokens from a topic
        
        Args:
            tokens: Single token or list of tokens
            topic: Topic name
            
        Returns:
            Dict with success count and failure count
        """
        cls.initialize()
        
        if isinstance(tokens, str):
            tokens = [tokens]
        
        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            
            logger.info(
                f"Topic unsubscription - Success: {response.success_count}, "
                f"Failure: {response.failure_count}"
            )
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'errors': [str(e) for e in response.errors] if response.errors else []
            }
            
        except Exception as e:
            logger.error(f"Error unsubscribing from topic: {str(e)}")
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'errors': [str(e)]
            }
