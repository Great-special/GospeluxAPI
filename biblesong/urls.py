"""
URL configuration for biblesong project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


admin.site.site_header = 'Gospelux Portal'
admin.site.site_title = 'Gospelux Portal'
admin.site.index_title = 'Welcome to My Portal'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Core app for home page and other static pages
    path('', include('users.web_urls')),  # Users app for web registration and login
    path('accounts/', include('allauth.urls')),  # Django Allauth for account management 
    path('api/v1/bible/', include('bible.urls')),  # Bible app for Bible-related APIs
    path('api/v1/songs/', include('songs.urls')),  # Songs app for song-related APIs
    path('api/v1/users/', include('users.urls')),  # Users app for user-related APIs
    
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)