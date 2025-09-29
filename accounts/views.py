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

@extend_schema(request=UserSignupSerializer)
@api_view(['POST'])  
@permission_classes([AllowAny])
def signup(request):
    print('requst data:', request.data)  # Debugging line to print incoming request data

    serializer = UserSignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()

    return Response({"satus": "success", "data": UserSignupSerializer(user).data}, status=status.HTTP_201_CREATED)
    
    # --- Step 2: Verify OTP and Create User ---
    # if 'otp' in request.data:
    #     submitted_otp = request.data.get('otp')
    #     email = request.data.get('email')

    #     if not submitted_otp or not email:
    #         return Response({"error": "Email and OTP are required for verification."}, status=status.HTTP_400_BAD_REQUEST)

    #     # Retrieve stored session data
    #     stored_otp = request.session.get('signup_otp')
    #     otp_expiry_str = request.session.get('signup_otp_expiry')
    #     user_data = request.session.get('signup_user_data')

    #     if not all([stored_otp, otp_expiry_str, user_data]):
    #         return Response({"error": "No pending registration found. Please start the signup process again."}, status=status.HTTP_400_BAD_REQUEST)

    #     if email != user_data.get('email'):
    #         return Response({"error": "Invalid email for this verification session."}, status=status.HTTP_400_BAD_REQUEST)

    #     # Check for OTP expiration
    #     otp_expiry = datetime.fromisoformat(otp_expiry_str)
    #     if datetime.now(timezone.utc) > otp_expiry:
    #         return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

    #     # Check if the submitted OTP is valid
    #     if int(submitted_otp) != stored_otp:
    #         return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     # If OTP is valid, proceed with user creation
    #     serializer = UserSignupSerializer(data=user_data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         # Clear the session data after successful signup
    #         request.session.flush()
    #         return Response({"message": "Account created successfully!"}, status=status.HTTP_201_CREATED)
    #     else:
    #         # This should ideally not fail if validated before, but as a safeguard:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # # --- Step 1: Validate Data and Send OTP ---
    # else:
    #     serializer = UserSignupSerializer(data=request.data)
    #     if not serializer.is_valid():
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #     validated_data = serializer.validated_data
    #     email = validated_data['email']

    #     # Check if user already exists
    #     if CustomUser.objects.filter(email=email).exists():
    #         return Response({"error": "An account with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    #     # Generate a 6-digit OTP
    #     otp = random.randint(100000, 999999)
    #     # Set OTP expiration time (e.g., 2 minutes from now)
    #     otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=2)

    #     # Store data in the session
    #     request.session['signup_otp'] = otp
    #     request.session['signup_otp_expiry'] = otp_expiry.isoformat()
    #     request.session['signup_user_data'] = validated_data
        
    #     # Send OTP via email
    #     try:
    #         send_mail(
    #             'Travel O - Your Account Verification OTP',
    #             f'Your OTP to complete your registration is: {otp}',
    #             settings.DEFAULT_FROM_EMAIL,
    #             [email],
    #             fail_silently=False,
    #         )
    #     except Exception as e:
    #         return Response({"error": f"Failed to send OTP email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #     return Response({"message": "OTP sent to your email. Please use it to complete your registration."}, status=status.HTTP_200_OK)

class MyTokenObtainPairView(TokenObtainPairView):
    
    serializer_class = MyTokenObtainPairSerializer
  
@api_view(['POST'])
@permission_classes([AllowAny])
def social_signup_signin(request):
    
    email = request.data.get('email')
    
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    if not email:
        return Response(
            {"message": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    username = email # Define username from email

  
    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'is_active': True
        }
    )


    if not created:
        updated = False
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if updated:
            user.save()

    # create JWT tokens
    refresh = RefreshToken.for_user(user)
    serializer = CustomUserSerializer(user)

    return Response({
        'refresh_token': str(refresh),
        'access_token': str(refresh.access_token),
        'user_data': serializer.data,
        'message': 'Successfully Created Account.' if created else 'Successfully Logged In.'
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

    # Generate a 6-digit OTP
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
    """
    Step 2: Verify the password reset OTP.
    """
    submitted_otp = request.data.get('otp')
    email = request.data.get('email')

    if not submitted_otp or not email:
        return Response({"error": "'email' and 'otp' field are required."}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve stored OTP data from the session
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