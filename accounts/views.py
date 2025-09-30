from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken  # Import RefreshToken
from .serializers import (UserSignupSerializer, MyTokenObtainPairSerializer,
CustomUserSerializer, PasswordResetSerializer, ChangePasswordSerializer, EmailChangeRequestSerializer,
UserProfileUpdateSerializer)
from .models import CustomUser
import random
from datetime import datetime, timedelta, timezone
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema

# @extend_schema(request=UserSignupSerializer)
@api_view(['POST'])  
@permission_classes([AllowAny])
def signup(request):
    serializer = UserSignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()

    return Response({"satus": "success", "data": UserSignupSerializer(user).data}, status=status.HTTP_201_CREATED)
    
   
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
  
@api_view(['POST'])
def social_signup_signup(request):
    email = request.data.get('email')
    full_name = request.data.get('full_name')
    auth_provider = request.data.get('auth_provider')

    if not email or not full_name or not auth_provider:
        return Response({
            "email": "This field is required." ,
            "full_name": "This field is required." ,
            "auth_provider": "This field is required." ,
        }, status=400)

    user, created = CustomUser.objects.get_or_create(
        email=email, 
        defaults={'username': email, 'email':email, 'full_name': full_name}
    )

    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    token = {
        'refresh': str(refresh),
        'access': str(access_token),
    }

    user_details = {
        'full_name': user.full_name,
        'email': user.email,
    }

    return Response({
        'message': 'Successfully authenticated.',
        'token': token,
        'user_details': user_details,
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    


@api_view(['POST'])
@permission_classes([AllowAny])
def send_password_reset_otp(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "email is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({"error": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)

    otp = random.randint(1000, 9999)
    subject = 'Travel O - Forgot Password OTP'
    message = f'Your OTP code is {otp}. It is valid for 5 minutes.'

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        user.otp = str(otp)
        user.save() 

    except Exception as e:
        return Response({"error": "Failed to send OTP email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Password reset OTP sent to your email."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_password_reset_otp(request):
    submitted_otp = request.data.get('otp')
    email = request.data.get('email')

    if not submitted_otp or not email:
        return Response({"error": "'email' and 'otp' field are required."}, status=status.HTTP_400_BAD_REQUEST)

    if not CustomUser.objects.filter(email=email).exists():  
        return Response({"error": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)
    
    user = CustomUser.objects.get(email=email)
    
    print('updated at : ', user.updated_at + timedelta(minutes=5))
    print('current time : ', datetime.now(timezone.utc))
    if submitted_otp != user.otp or user.updated_at + timedelta(minutes=5) < datetime.now(timezone.utc):
        return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

    user.otp = ""

    return Response({"message": "OTP verified successfully. You can now set a new password."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def set_new_password(request):
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if not CustomUser.objects.filter(email=serializer.validated_data['email']).exists():  
        return Response({"error": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)
    
    user = CustomUser.objects.get(email=serializer.validated_data['email'])
    user.set_password(serializer.validated_data['password'])
    user.save()

    return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  
def change_password(request):
    user = request.user
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if not user.check_password(serializer.validated_data['current_password']):
        return Response(
            {"error": "Your current password is not correct."},
            status=status.HTTP_400_BAD_REQUEST
        )
     
    new_password = serializer.validated_data['new_password']
    
    user.set_password(new_password)
    user.save()

    return Response(
        {"message": "Password changed successfully."},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Blacklists the refresh token for the current user to log them out.
    """
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    
    except Exception as e:
        # This can happen if the token is malformed or already blacklisted
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    if request.method == 'GET':
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_email_change(request):
    """
    Step 1: User requests an email change.
    Verifies password and sends OTP to the new email address.
    """
    user = request.user
    serializer = EmailChangeRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    current_password = serializer.validated_data['current_password']
    new_email = serializer.validated_data['new_email']

    # 1. Verify the user's current password
    if not user.check_password(current_password):
        return Response({"error": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Generate and send OTP to the NEW email address
    otp = random.randint(100000, 999999)
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5) # 5-minute expiry

    # 3. Store OTP and the new email in the session
    request.session['email_change_otp'] = otp
    request.session['email_change_otp_expiry'] = otp_expiry.isoformat()
    request.session['new_email_for_change'] = new_email
    
    try:
        send_mail(
            'Verify Your New Email Address',
            f'Your OTP to confirm your new email address is: {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [new_email],
            fail_silently=False,
        )
    except Exception as e:
        return Response({"error": "Failed to send OTP email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "An OTP has been sent to your new email address."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email_change(request):
    """
    Step 2: User provides the OTP to confirm the email change.
    """
    user = request.user
    submitted_otp = request.data.get('otp')

    if not submitted_otp:
        return Response({"error": "OTP is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve data from session
    stored_otp = request.session.get('email_change_otp')
    otp_expiry_str = request.session.get('email_change_otp_expiry')
    new_email = request.session.get('new_email_for_change')

    if not all([stored_otp, otp_expiry_str, new_email]):
        return Response({"error": "No pending email change request found. Please start again."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check for OTP expiration
    otp_expiry = datetime.fromisoformat(otp_expiry_str)
    if datetime.now(timezone.utc) > otp_expiry:
        return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if OTP is correct
    if int(submitted_otp) != stored_otp:
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

    # If all checks pass, update the user's email
    old_email = user.email
    user.email = new_email
    user.save(update_fields=['email'])

    # Clear the session data
    del request.session['email_change_otp']
    del request.session['email_change_otp_expiry']
    del request.session['new_email_for_change']

    # (Optional but recommended) Notify the old email address
    try:
        send_mail(
            'Your Email Address Has Been Changed',
            f'This is a notification that the email address for your account has been changed from {old_email} to {new_email}.',
            settings.DEFAULT_FROM_EMAIL,
            [old_email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send notification to old email: {e}")

    return Response({"message": "Your email address has been updated successfully."}, status=status.HTTP_200_OK)