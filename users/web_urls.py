from django.urls import path
from . import views

urlpatterns = [
    path('register-web/<str:plan>/', views.web_register, name='web_register'),
]
         