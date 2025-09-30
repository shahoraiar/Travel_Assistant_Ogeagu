from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import SupportTicketSerializer
from django.core.mail import send_mail, EmailMessage
from django.conf import settings

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_support_ticket(request):
    serializer = SupportTicketSerializer(data=request.data)
    serializer.is_valid(raise_exception=True) 
    user_email = request.user.email
    user_manual_email = serializer.validated_data.get('user_manual_email') or user_email

    if user_manual_email != user_email:
        reply_to = [user_manual_email]
    else:
        reply_to = [user_email]
    try:
        subject = f"[Support Ticket] from {user_email}"
        message = f"""
        A new support request has been created.

        Registered user mail: {user_email}
        Request reply to: {user_manual_email}

        Description:
        {serializer.validated_data.get('description')}
        """
        admin_email = settings.EMAIL_HOST_USER 

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.EMAIL_HOST_USER,  
            to=[admin_email],
            reply_to=reply_to 
        ) 

        email.send(fail_silently=False) 
        ticket = serializer.save(user=request.user) 

        return Response(SupportTicketSerializer(ticket).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(f"Error sending support ticket email: {e}")

    return Response({"message": "Your support request has been submitted successfully."}, status=status.HTTP_201_CREATED)
    

