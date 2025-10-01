from rest_framework import serializers
from .models import *
from django.utils import timezone
from datetime import date

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name', 'slug', 'created_at', 'updated_at']

class UserPreferenceListSerializer(serializers.ModelSerializer):
    preferences_id = serializers.IntegerField(source='preferences.id', read_only=True)
    preferences_name = serializers.CharField(source='preferences.name', read_only=True)
    class Meta:
        model = UserPreference
        fields = ['preferences_id', 'preferences_name']

  
class ItineraryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Itinerary
        fields = [
            'id', 'destination_name', 'latitude', 'longitude', 'trip_type', 'budget', 'duration', 'start_date', 'end_date'
        ]
        read_only_fields = ['id', ]

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("End date must be after the start date.")
        
        return data
    
    def create(self, validated_data):
        start_date = validated_data.get('start_date')
        end_date = validated_data.get('end_date')

        if start_date and end_date:
            validated_data['duration'] = (end_date - start_date).days + 1

        return super().create(validated_data)
    
class TouristSpotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TouristSpot
        fields = ['id', 'day', 'name', 'location']
        
class TouristSpotReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TouristSpot
        fields = ['id', 'name', 'location']


class DayReadSerializer(serializers.ModelSerializer):
    spots = TouristSpotReadSerializer(many=True, read_only=True)

    class Meta:
        model = Day
        fields = ['id', 'day_number', 'spots']


class ItineraryReadSerializer(serializers.ModelSerializer):
    # days = DayReadSerializer(many=True, read_only=True)
    days_left = serializers.SerializerMethodField()
    planning_progress = serializers.SerializerMethodField()

    class Meta:
        model = Itinerary
        fields = [
            'id', 'destination_name', 'latitude', 'longitude', 'trip_type', 'budget',
            'duration', 'start_date', 'end_date', 
            'days_left', 'planning_progress'
        ]

    def get_days_left(self, obj):
        today = date.today()
        if today < obj.start_date:
            days = (obj.start_date - today).days
            return f"Starts in {days} day{'s' if days > 1 else ''}"

        elif obj.start_date <= today <= obj.end_date:
            days = (obj.end_date - today).days + 1
            return f"{days} day{'s' if days > 1 else ''} left"

        else:
            return "Completed"

    def get_planning_progress(self, obj):
        today = date.today()
        total_days = (obj.end_date - obj.start_date).days + 1

        if today < obj.start_date:
            return 0

        elif obj.start_date <= today <= obj.end_date:
            days_passed = (today - obj.start_date).days + 1
            return int((days_passed / total_days) * 100)

        else:
            return 100
        
class RecommendationRequestSerializer(serializers.Serializer):
    """
    Validates the data for a "What's Happening" recommendation request.
    This is not a ModelSerializer as it represents a query, not a database object.
    """
    # --- User's Current Location (sent from the frontend) ---
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=6, required=True)

    # --- User's Filters ---
    preferences = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Interest.objects.all(),
        required=False # Allow requests with no specific preference
    )
    timing = serializers.ChoiceField(
        choices=['ALL_DAY', 'MORNING', 'AFTERNOON', 'EVENING'],
        default='ALL_DAY'
    )
    distance = serializers.ChoiceField(
        choices=[2, 5, 10], # Kilometers
        default=5
    )