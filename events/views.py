from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Event, Invitation
from accounts.models import CustomUser
from django.shortcuts import get_object_or_404
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def event_list_create(request):
    if request.method == 'GET':
        events = Event.objects.filter(event_user=request.user).order_by('-event_date')
        serializer = EventListSerializer(events, many=True)
        return Response(serializer.data)  

    elif request.method == 'POST':
        serializer = EventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(event_user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def all_event_list(request):
    events = Event.objects.filter(event_date__gte=now().date()).order_by('-event_date')
    serializer = EventListSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['GET', 'PATCH', 'DELETE'])
def event_detail(request, pk):
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EventListSerializer(event)
        return Response(serializer.data)

    if event.event_user != request.user:
        return Response(
            {"error": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN
        )

    elif request.method == 'PATCH':
        serializer = EventCreateSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def all_user_list(request):
    users = CustomUser.objects.exclude(Q(id=request.user.id) | Q(is_superuser=True))
    serializer = UserInviteListSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invite(request):
    serializers = SendInviteSerializer(data=request.data)
    serializers.is_valid(raise_exception=True) 

    sender_user = request.user
    print("Sender User:", sender_user)
    receiver_user_id = serializers.validated_data['receiver_user_id']
    event_id = serializers.validated_data['event_id']

    event = get_object_or_404(Event, id=event_id)
    receiver_user = get_object_or_404(CustomUser, id=receiver_user_id)
    print("Receiver User:", receiver_user)

    if Invitation.objects.filter(event=event, invitee=receiver_user).exists():
        return Response({"error": "This user has already been invited to this event."}, status=status.HTTP_400_BAD_REQUEST)
       
    invitation = Invitation.objects.create(
        event=event,    
        inviter=sender_user,
        invitee=receiver_user,
        status=Invitation.Status.PENDING
    )   
    invitation.save()
    try : 
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{receiver_user.id}",
            {
                "type": "send_notification",
                "content": {
                    "event": event.title,
                    "from": request.user.username,
                    "message": f"{request.user.username} invited you to event {event.title}."
                }
            }
        )

        invitation.status = Invitation.Status.ACCEPTED
        invitation.save()
    except Exception as e:
        print("Error sending notification:", e)
        invitation.status = Invitation.Status.DECLINED
        invitation.save()

    return Response({"message": f"{request.user.username} invited you to event {event.title}."}, status=status.HTTP_201_CREATED)
    
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_invite_list(request, event_id):
    """
    Returns a list of users who can be invited to a specific event.
    Excludes the current user, the event organizer, and anyone already invited.
    """
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

    # Get IDs of users who have already been invited to this event
    already_invited_ids = Invitation.objects.filter(event=event).values_list('invitee__id', flat=True)
    
    # Get all users, excluding the current user, the organizer, and those already invited
    users_to_invite = CustomUser.objects.exclude(
        id__in=[request.user.id, event.organizer.id, *already_invited_ids]
    )

    serializer = UserInviteListSerializer(users_to_invite, many=True)
    return Response(serializer.data)

# --- NEW VIEW TO SEND AN INVITATION ---
# @api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
# def send_invite(request, event_id, user_id):
#     """
#     Creates an invitation from the request user to another user for a specific event.
#     """
#     try:
#         event = Event.objects.get(pk=event_id)
#         invitee = CustomUser.objects.get(pk=user_id)
#     except (Event.DoesNotExist, CustomUser.DoesNotExist):
#         return Response({"error": "Event or User not found."}, status=status.HTTP_404_NOT_FOUND)

#     # Validation checks
#     if invitee == request.user:
#         return Response({"error": "You cannot invite yourself."}, status=status.HTTP_400_BAD_REQUEST)
#     if Invitation.objects.filter(event=event, invitee=invitee).exists():
#         return Response({"error": "This user has already been invited."}, status=status.HTTP_400_BAD_REQUEST)

#     # Create the invitation
#     invitation = Invitation.objects.create(
#         event=event,
#         inviter=request.user,
#         invitee=invitee
#     )
    
#     # You could add logic here to send a push notification or email to the invitee
    
#     serializer = InvitationSerializer(invitation)
#     return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_list(request):
    invitations = Invitation.objects.filter(invitee=request.user).order_by('-id')
    serializer = NotificationSerializer(invitations, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_as_read(request):
    Invitation.objects.filter(invitee=request.user, is_read=False).update(is_read=True)
    return Response({"message": "All notifications marked as read."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def respond_to_invitation(request, invitation_id):
    """
    Allows a user to accept or decline a specific invitation.
    Expects a body like: {"response": "accept"} or {"response": "decline"}
    """
    invitation = get_object_or_404(Invitation, pk=invitation_id, invitee=request.user)
    
    response = request.data.get('response', '').lower()

    if invitation.status != 'PENDING':
        return Response({"error": "This invitation has already been responded to."}, status=status.HTTP_400_BAD_REQUEST)

    if response == 'accept':
        invitation.status = 'ACCEPTED'
        # Also add the user to the event's attendee list
        invitation.event.attendees.add(request.user)
    elif response == 'decline':
        invitation.status = 'DECLINED'
    else:
        return Response({"error": "Invalid response. Please provide 'accept' or 'decline'."}, status=status.HTTP_400_BAD_REQUEST)

    # Mark as read since the user is interacting with it.
    invitation.is_read = True
    invitation.save()
    
    serializer = NotificationSerializer(invitation)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_as_read(request, invitation_id):
    """
    Marks a single, specific invitation notification as read.
    """
    # Find the invitation, ensuring it belongs to the logged-in user to prevent
    # one user from marking another's notifications as read.
    invitation = get_object_or_404(Invitation, pk=invitation_id, invitee=request.user)

    # If it's not already read, update it.
    if not invitation.is_read:
        invitation.is_read = True
        invitation.save(update_fields=['is_read'])

    return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_bookmark(request, event_id):
    """
    Toggles a bookmark for an event for the current user.
    If the event is already bookmarked, it will be removed.
    If it's not bookmarked, it will be added.
    """
    user = request.user
    event = get_object_or_404(Event, pk=event_id)

    # Check if the user has already bookmarked this event
    if event in user.bookmarked_events.all():
        # If yes, remove it
        user.bookmarked_events.remove(event)
        return Response({"message": "Bookmark removed successfully."}, status=status.HTTP_200_OK)
    else:
        # If no, add it
        user.bookmarked_events.add(event)
        return Response({"message": "Event bookmarked successfully."}, status=status.HTTP_201_CREATED)

# --- NEW VIEW TO LIST ALL BOOKMARKED EVENTS ---
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def bookmarked_events_list(request):
    """
    Returns a list of all events bookmarked by the currently authenticated user.
    """
    user = request.user
    bookmarked_events = user.bookmarked_events.all().order_by('-created_at')
    
    # We can reuse the EventListSerializer as it contains the right info for a list
    serializer = EventListSerializer(bookmarked_events, many=True)
    return Response(serializer.data)
