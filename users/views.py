from asgiref.sync import async_to_sync
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from .models import User, OTP, Plan, UserPlan
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, OTPVerificationSerializer,
    ResendOTPSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    UserProfileSerializer, ChangePasswordSerializer
)
from .utils import send_otp_email, send_otp_email_task

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    print(request.data, type(request.data))
    try:
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Check if user already exists before saving
            email = serializer.validated_data.get('email')
            username = serializer.validated_data.get('username')
            if User.objects.filter(email=email).exists():
                return Response({
                    'error': 'A user with this email already exists.',
                    'email': ['This email is already registered.']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(username=username).exists():
                return Response({
                    'error': 'A user with this username already exists.',
                    'username': ['This username is already taken.']
                }, status=status.HTTP_400_BAD_REQUEST)
            user = serializer.save()
            try:
                # Create and send OTP for email verification
                otp = OTP.objects.create(
                    user=user,
                    otp_type='email_verification'
                )
                # send_otp_email(user.email, otp.otp_code, 'email_verification')
            except Exception as e:
                print(f"Error creating/sending OTP: {str(e)}")
                
            return Response({
                'message': 'User registered successfully. Please check your email for verification code.',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        otp_type = serializer.validated_data['otp_type']
        
        try:
            user = User.objects.get(email=email)
            otp = OTP.objects.filter(
                user=user,
                otp_code=otp_code,
                otp_type=otp_type,
                is_used=False
            ).first()
            
            if not otp:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not otp.is_valid():
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as used
            otp.is_used = True
            otp.save()
            
            # If email verification, mark user as verified
            if otp_type == 'email_verification':
                user.is_email_verified = True
                user.save()
            
            return Response({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    serializer = ResendOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_type = serializer.validated_data['otp_type']
        
        try:
            user = User.objects.get(email=email)
            
            # Invalidate previous OTPs
            OTP.objects.filter(user=user, otp_type=otp_type, is_used=False).update(is_used=True)
            
            # Create new OTP
            otp = OTP.objects.create(user=user, otp_type=otp_type)
            send_otp_email(user.email, otp.otp_code, otp_type)
            
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Invalidate previous password reset OTPs
            OTP.objects.filter(user=user, otp_type='password_reset', is_used=False).update(is_used=True)
            
            # Create new OTP
            otp = OTP.objects.create(user=user, otp_type='password_reset')
            # send_otp_email(user.email, otp.otp_code, 'password_reset')
            # async_to_sync(send_otp_email_task(user.email, otp.otp_code, 'password_reset'))
            async_to_sync(send_otp_email_task)(
                user.email,
                otp.otp_code,
                'password_reset'
            )

            
            return Response({'message': 'Password reset OTP sent to your email'}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(email=email)
            otp = OTP.objects.filter(
                user=user,
                otp_code=otp_code,
                otp_type='password_reset',
                is_used=False
            ).first()
            
            if not otp:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not otp.is_valid():
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update password and mark OTP as used
            user.set_password(new_password)
            user.save()
            otp.is_used = True
            otp.save()
            
            return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def web_register(request, plan):
    if request.method == 'POST' and plan in ('free', 'premium', 'lifetime'):
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        password = request.POST.get('password')
        
        if all((username, email, first_name, last_name, password)):
            if User.objects.filter(email=email).exists():
                return render(request, 'users/register.html', {'error': 'Email already in use'})
            if User.objects.filter(username=username).exists():
                return render(request, 'users/register.html', {'error': 'Username already in use'})
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            user.is_email_verified = False
            user.save()
            messages.success(request, 'Registration successful! You can now login on the app.') 
            # # Create and send OTP for email verification
            # otp = OTP.objects.create(
            #     user=user,
            #     otp_type='email_verification'
            # )
            # send_otp_email(user.email, otp.otp_code, 'email_verification')
            
            if plan != 'free':
                return redirect(sub_payment(request, plan))
            else:
                subscription(plan, user)
            
            
            return render(request, 'users/register.html', {
                'message': 'Registration successful! Please check your email for the verification code.'
            })
    
    
    return render(request, 'users/register.html')


def subscription(plan, user):
    try:
        plan_obj = Plan.objects.get(name=plan)
        userPlan = UserPlan.objects.create(user=user, plan=plan_obj)
        userPlan.start_date = timezone.now()
        userPlan.end_date = None if plan == 'lifetime' else timezone.now() + timezone.timedelta(days=plan_obj.duration_days)
        userPlan.save()
        return True
    except Plan.DoesNotExist:
        return False


def sub_payment(request, plan):
    # Placeholder for payment processing logic
    # Integrate with a payment gateway like Stripe or PayPal here
    plan_obj = Plan.objects.get(name=plan)
    return render(request, 'payment.html', {'stripe_key': settings.STRIPE_PUBLIC_KEY, 'plan':plan_obj})

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)