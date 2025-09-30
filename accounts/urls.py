from django.urls import path
from .views import *
    
   
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('social-login/', social_signup_signup, name='social_signup_signup'),
    path('password-reset/send-otp/', send_password_reset_otp, name='send_password_reset_otp'),
    path('password-reset/verify-otp/', verify_password_reset_otp, name='verify_password_reset_otp'),
    path('password-reset/set-new/', set_new_password, name='set_new_password'),
    path('change-password/', change_password, name='change_password'),
    
    path('profile/', user_profile, name='user-profile'),
    path('profile/request-email-change/', request_email_change, name='request-email-change'),
    path('profile/verify-email-change/', verify_email_change, name='verify-email-change'),
    path('logout/', logout, name='logout'),
]