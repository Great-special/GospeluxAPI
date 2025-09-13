from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.http import HttpResponse

from .models import ApplicationAPK, UserFeedBack, NewsLetterSubscriber


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'API is running successfully'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """API information endpoint"""
    return Response({
        'name': 'Bible Song API',
        'version': '1.0.0',
        'description': 'REST API for Bible and Songs Generation',
        'endpoints': {
            'authentication': '/api/v1/users/',
            'bible': '/api/v1/bible/',
            'songs': '/api/v1/songs/',
            'core': '/api/v1/core/'
        }
    })


def home_page(request):
    template_name = 'core/home.html'
    # template_name = 'gospelux_landing.html'
    
    return render(request, template_name)

def contact_page(request):
    template_name = 'core/contact.html'
    # template_name = 'bible_music_app_landing.html'
    
    if request.POST:
        name = request.POST.get('firstName') + ' ' + request.POST.get('lastName')
        email = request.POST.get('email')
        organization = request.POST.get('church')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        newsletter = True if request.POST.get('newsletter') == 'on' else False
        
        feedback = UserFeedBack.objects.create(
            full_name=name,
            email=email,
            organization=organization,
            subject=subject,
            message=message
        )
        feedback.save()
        
        if newsletter:
            obj = NewsLetterSubscriber.objects.create(email=email)
            obj.save()
            
    return render(request, template_name)

def about_page(request):
    template_name = 'core/about.html'
    # template_name = 'bible_music_app_landing.html'
    
    if request.POST:
        pass
    return render(request, template_name)

def download_file(request, slug):
    # Auto Detect platform
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    if 'android' in user_agent:
        platform = 'Android'
    elif 'iphone' in user_agent or 'ipad' in user_agent or 'ios' in user_agent:
        platform = 'iOS'
        
    apk = ApplicationAPK.objects.filter(slug=slug, type=platform).first()
    if apk:
        response = HttpResponse(apk.file, content_type='application/vnd.android.package-archive')
        response['Content-Disposition'] = f'attachment; filename="{apk.name}.apk"'
        return response
    else:
        return Response({'error': 'File not found'}, status=404)