# from django.core.mail import send_mail
# from django.conf import settings
# from django.template.loader import render_to_string
# from celery import shared_task

# @shared_task
# def send_otp_email_task(email, otp_code, otp_type):
#     """Celery task to send OTP email asynchronously"""
#     if otp_type == 'email_verification':
#         subject = 'Verify Your Email Address'
#         message = f'Your email verification code is: {otp_code}. This code will expire in 10 minutes.'
#     elif otp_type == 'password_reset':
#         subject = 'Password Reset Code'
#         message = f'Your password reset code is: {otp_code}. This code will expire in 10 minutes.'
#     else:
#         subject = 'OTP Code'
#         message = f'Your OTP code is: {otp_code}'

#     try:
#         send_mail(
#             subject=subject,
#             message=message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[email],
#             fail_silently=False,
#         )
#         return True
#     except Exception as e:
#         print(f"Failed to send email: {str(e)}")
#         return False


from asgiref.sync import sync_to_async
from django.core.mail import send_mail
from django.conf import settings

@sync_to_async
def _send_mail_async(subject, message, email):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

async def send_otp_email_task(email, otp_code, otp_type):
    """Send OTP email asynchronously"""

    if otp_type == 'email_verification':
        subject = 'Verify Your Email Address'
        message = f'Your email verification code is: {otp_code}. This code will expire in 10 minutes.'
    elif otp_type == 'password_reset':
        subject = 'Password Reset Code'
        message = f'Your password reset code is: {otp_code}. This code will expire in 10 minutes.'
    else:
        subject = 'OTP Code'
        message = f'Your OTP code is: {otp_code}'

    try:
        await _send_mail_async(subject, message, email)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_otp_email(email, otp_code, otp_type):
    """Send OTP email (can be synchronous for development)"""
    # For development, send synchronously
    if settings.DEBUG:
        return send_otp_email_task(email, otp_code, otp_type)
    else:
        # For production, use Celery
        send_otp_email_task.delay(email, otp_code, otp_type)
        return True