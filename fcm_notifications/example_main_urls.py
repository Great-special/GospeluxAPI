# Add this to your main project's urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # FCM Notifications API endpoints
    path('api/fcm/', include('fcm_notifications.urls')),
    
    # Django REST Framework authentication
    path('api-auth/', include('rest_framework.urls')),
    
    # ... your other URL patterns
]
