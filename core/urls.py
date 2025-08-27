from django.urls import path
from .admin import admin_site
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('info/', views.api_info, name='api_info'),
    path('', views.home_page, name='home'),
    path('contact/', views.contact_page, name='contact_page'),
    path('download/<slug:slug>/', views.download_file, name='download_file'),
    path('@gig-admin/', admin_site.urls, name='magic-admin'),
]