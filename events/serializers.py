from rest_framework import serializers
from .models import Event, Invitation
from personalize.serializers import InterestSerializer # Reuse for tag details
from accounts.models import CustomUser

class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'image', 'category', 'event_date',
            'start_time', 'end_time', 'venue_name', 'address', 'tags',
            'organizer_name', 'organizer_email', 'organizer_phone', 'organizer_website'
        ]

class EventListSerializer(serializers.ModelSerializer):
    event_user_full_name = serializers.CharField(source="event_user.full_name", read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'event_user', 'event_user_full_name', 'tags', 'bookmarked', 'title', 'description', 'image', 
                  'category', 'event_date', 'start_time', 'end_time', 'venue_name', 'address', 'organizer_name', 'organizer_email', 
                  'organizer_phone', 'organizer_website', 'created_at', 'updated_at']

class EventDetailSerializer(serializers.ModelSerializer):
    """A detailed serializer for the single event view."""
    tags = InterestSerializer(many=True, read_only=True) # Show full tag details
    class Meta:
        model = Event
        exclude = ['organizer'] # Exclude the user ID, but show everything else
        
class UserInviteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email']  

class SendInviteSerializer(serializers.Serializer):
    receiver_user_id = serializers.IntegerField()
    event_id = serializers.IntegerField()

class InvitationSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing invitations."""
    class Meta:
        model = Invitation
        fields = ['id', 'event', 'inviter', 'invitee', 'status']
        read_only_fields = ['inviter', 'status']
        
class NotificationSerializer(serializers.ModelSerializer):
    inviter = serializers.StringRelatedField(read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_id = serializers.IntegerField(source='event.id', read_only=True)

    class Meta:
        model = Invitation
        fields = [
            'id', 
            'inviter', 
            'event_id',
            'event_title',
            'status',
            'is_read',
        ]