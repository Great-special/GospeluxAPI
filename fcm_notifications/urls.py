from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceTokenViewSet,
    NotificationViewSet,
    NotificationTemplateViewSet,
    TopicSubscriptionViewSet
)

app_name = 'fcm_notifications'

router = DefaultRouter()
router.register(r'devices', DeviceTokenViewSet, basename='device')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'templates', NotificationTemplateViewSet, basename='template')
router.register(r'topics', TopicSubscriptionViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
]
