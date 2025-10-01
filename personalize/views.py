from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from .serializers import InterestSerializer, UserPreferenceSerializer, ItineraryCreateSerializer, ItineraryReadSerializer, RecommendationRequestSerializer
from math import radians, sin, cos, sqrt, atan2
from datetime import time
from django.http import JsonResponse
import json
from django.utils.timezone import now

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Import from your new modules
from . import utils
from . import ai
from .models import Itinerary

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interests(request):
    all_interests = Interest.objects.all()
    serializer = InterestSerializer(all_interests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_preference(request):
    user = request.user
    pref_ids = request.data.get("preferences", [])

    if not isinstance(pref_ids, list) or len(pref_ids) == 0:
        return Response(
            {"error": "At least one preference must be provided, e.g. preferences: [1, 2, 3]"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    interests = Interest.objects.all()
    interest_ids = [interest.id for interest in interests]
    invalid_ids = []
    for pid in pref_ids:
        if pid not in interest_ids:
            print('not matched : ', pid)
            invalid_ids.append(pid)

    if invalid_ids:
        return Response(
            {"error": f"The following preference IDs are invalid: {invalid_ids}"},        
            status=status.HTTP_400_BAD_REQUEST
        )
            
    user_pref, _ = UserPreference.objects.get_or_create(user=user)

    user_pref.preferences.add(*pref_ids)

    prefs_data = list(user_pref.preferences.values("id", "name"))

    return Response(
        {
            "message": "Preferences saved successfully",
            "preferences": prefs_data
        },
        status=status.HTTP_200_OK
    )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_preference(request):
    user = request.user
    print('user: ', user, user.id, user.username)
    pref_ids = request.data.get("preferences", [])

    if not isinstance(pref_ids, list) or len(pref_ids) == 0:
        return Response(
            {"error": "At least one preference ID must be provided to delete, e.g. preferences: [1, 2, 3]"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    interests = Interest.objects.all()
    interest_ids = [interest.id for interest in interests]
    invalid_ids = []
    for pid in pref_ids:
        if pid not in interest_ids:
            print('not matched : ', pid)
            invalid_ids.append(pid)

    if invalid_ids:
        return Response(
            {"error": f"The following preference IDs are invalid: {invalid_ids}"},        
            status=status.HTTP_400_BAD_REQUEST
        )
            
    try:
        user_pref = UserPreference.objects.get(user=user)
        interests = user_pref.preferences.all()  # This gives you all related interests
        user_pref_ids = list(interests.values_list('id', flat=True))
        print("user's interest IDs:", user_pref_ids)
    except UserPreference.DoesNotExist:
        return Response(
            {"error": "No preferences found for the user."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # user_pref_ids = list(user_pref.values_list('id', flat=True))
    # print('user_pref_ids: ', user_pref_ids)
    not_owned = []
    for pid in pref_ids:
        if pid not in user_pref_ids:
            not_owned.append(pid)
    if not_owned:
        return Response(
            {"error": f"User does not have these preferences: {not_owned}"},
            status=status.HTTP_400_BAD_REQUEST
        ) 

    if not_owned:
        return Response(
            {"error": f"User does not have these preferences: {not_owned}"},
            status=status.HTTP_400_BAD_REQUEST
        ) 

    user_pref.preferences.remove(*pref_ids)

    prefs_data = list(user_pref.preferences.values("id", "name"))

    return Response(
        {
            "message": "Preferences deleted successfully",
            "availble_preferences": prefs_data
        },
        status=status.HTTP_200_OK
    )

# --- Function 3: Update user preference list ---
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_preference(request):
    """Updates (replaces) the user's entire preference list."""
    user = request.user
    serializer = UserPreferenceSerializer(data=request.data)
    if serializer.is_valid():
        preference_ids = serializer.validated_data['preferences']
        user.preferences.set(preference_ids)
        return Response({"message": "Preference list updated successfully."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# --- Function 4: Create a new itinerary ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_itinerary(request):
    user = request.user
    user_preferences = user.preferences 
    
    if not user_preferences.preferences.exists():
        return Response(
            {"error": "Your preference list is empty. Please choose at least one interest to create an itinerary."},
            status=status.HTTP_400_BAD_REQUEST
        )
    print('request data: ', request.data)
    serializer = ItineraryCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    print('validated data: ', serializer.validated_data)

    itinerary = serializer.save(user=user)

    return Response(ItineraryCreateSerializer(itinerary).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_itinerary(request):
    try:
        print('time : ', now().date())
        itinerary = Itinerary.objects.filter(
            user=request.user,
            end_date__gte=now().date()  
        ) 
    except Itinerary.DoesNotExist:
        return Response({"error": "Itinerary not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ItineraryReadSerializer(itinerary, many=True) 
    return Response(serializer.data)






@api_view(["GET"])
def generate_ai_detailed_itinerary(request, pk):
    """
    Generate AI-powered detailed itinerary with real place details
    """
    try:
        itinerary = Itinerary.objects.get(pk=pk)
    except Itinerary.DoesNotExist:
        return Response(
            {"error": f"Itinerary with ID {pk} not found."}, 
            status=status.HTTP_404_NOT_FOUND
        )

    # Validate and parse destination coordinates
    try:
        if not itinerary.destination or ',' not in itinerary.destination:
            return Response(
                {"error": "Invalid destination format. Expected 'latitude, longitude'."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        lat_str, lng_str = itinerary.destination.split(',')
        dest_lat, dest_lng = float(lat_str.strip()), float(lng_str.strip())
        
        # Validate coordinate ranges
        if not (-90 <= dest_lat <= 90) or not (-180 <= dest_lng <= 180):
            return Response(
                {"error": "Invalid coordinate values."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except (ValueError, AttributeError, TypeError):
        return Response(
            {"error": "Invalid destination format. Expected 'latitude, longitude'."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    # Determine trip duration with better validation
    duration = calculate_trip_duration(itinerary)
    if duration <= 0:
        return Response(
            {"error": "Could not determine a valid trip duration. Please provide either start/end dates or duration."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get destination name from coordinates
        destination_name = utils.get_location_name_from_coords(dest_lat, dest_lng)
        if not destination_name or destination_name == "Unknown Location":
            return Response(
                {"error": "Could not determine destination name from coordinates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate AI plan
        ai_plan = ai.generate_ai_plan(
            duration=duration,
            destination_name=destination_name,
            trip_type=itinerary.get_trip_type_display(),
            budget=itinerary.get_budget_display()
        )

        # Validate AI response structure
        if not ai_plan or not isinstance(ai_plan.get("itinerary_plan"), list):
            return Response(
                {"error": "AI service returned invalid itinerary structure."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Enrich with real place details
        final_itinerary = enrich_itinerary_with_places(
            ai_plan["itinerary_plan"], 
            dest_lat, 
            dest_lng, 
            destination_name
        )

        return Response(
            {
                "itinerary_plan": final_itinerary,
                "destination_name": destination_name,
                "duration": duration,
                "trip_type": itinerary.get_trip_type_display(),
                "budget": itinerary.get_budget_display()
            }, 
            status=status.HTTP_200_OK
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"External API error: {str(e)}")
        return Response(
            {"error": "Service temporarily unavailable. Please try again later."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.error(f"Unexpected error in itinerary generation: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred while generating your itinerary."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def calculate_trip_duration(itinerary):
    """Calculate trip duration from dates or duration field"""
    if itinerary.start_date and itinerary.end_date:
        duration = (itinerary.end_date - itinerary.start_date).days + 1
        if duration > 0:
            return duration
    
    # Fallback to duration field
    duration_map = {
        '3_DAYS': 3, 
        '5_DAYS': 5, 
        '1_WEEK': 7, 
        '10_DAYS': 10, 
        '2_WEEKS': 14
    }
    return duration_map.get(itinerary.duration, 0)


def enrich_itinerary_with_places(ai_plan, dest_lat, dest_lng, destination_name):
    """Enrich AI-generated plan with real place details"""
    final_itinerary = []
    
    for day_plan in ai_plan:
        enriched_activities = []
        
        for activity in day_plan.get("activities", []):
            search_query = activity.get("search_query", activity.get("title", ""))
            if not search_query:
                continue
                
            place_details = utils.get_actual_places_details(
                search_query, 
                dest_lat, 
                dest_lng
            )
            
            if place_details:
                enriched_activities.append({
                    "title": place_details.get("name", activity["title"]),
                    "location": place_details.get("formatted_address", destination_name),
                    "description": place_details.get("description", f"A highly-rated spot for {activity['title'].lower()}."),
                    "rating": place_details.get("rating"),
                    "place_id": place_details.get("place_id"),
                    "types": place_details.get("types", []),
                    "user_ratings_total": place_details.get("user_ratings_total"),
                    "original_activity": activity["title"]
                })
            else:
                # Fallback to AI-generated activity
                enriched_activities.append({
                    "title": activity["title"],
                    "location": destination_name,
                    "description": activity.get("description", "A suggested activity."),
                    "rating": None,
                    "place_id": None,
                    "original_activity": activity["title"]
                })
        
        final_itinerary.append({
            "day": day_plan.get("day"),
            "theme": day_plan.get("theme", ""),
            "activities": enriched_activities
        })
    
    return final_itinerary
















# import google.generativeai as genai
# import requests

# genai.configure(api_key="AIzaSyDy8Q6MoVTQqGdWvypYZ1BDHzHv2Go_tHE")
# @api_view(["POST"])
# def place_ai_response(request):
#     # prompt = request.data.get("prompt")
#     # if not prompt:
#     #     return Response({"error": "Prompt is required"}, status=400)

#     model = genai.GenerativeModel("gemini-pro")
#     response = model.generate_content("dhaka")

#     return Response({"response": response.text})

# Configure Gemini
# GEMINI_API_KEY = "AIzaSyDKGP3QI-1x7BSvpcXQS5gs5YeU9IDhAYM"
# PLACES_API_KEY = "AIzaSyDy8Q6MoVTQqGdWvypYZ1BDHzHv2Go_tHE"

# genai.configure(api_key=GEMINI_API_KEY)

# @api_view(["POST"])
# def place_ai_response(request):
#     query = request.data.get("textQuery", None)
#     if not query:
#         return Response({"error": "textQuery is required"}, status=400)

#     url = "https://places.googleapis.com/v1/places:searchText"
#     headers = {
#         "Content-Type": "application/json",
#         "X-Goog-Api-Key": PLACES_API_KEY,
#         "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.priceLevel"
#     }
#     data = {"textQuery": query}

#     response = requests.post(url, headers=headers, json=data)

#     # Return API response
#     return Response(response.json(), status=response.status_code)

# @api_view(["GET"])
# def get_google_access_token(request):
#     data = {
#         "code": auth_code,
#         "client_id": "854610349372-a4bt1op18sh2mer9vbf069acpgsi74qr.apps.googleusercontent.com",
#         "client_secret": "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",
#         "redirect_uri": "http://localhost",
#         "grant_type": "authorization_code"
#     }
#     response = requests.post("https://oauth2.googleapis.com/token", data=data)
#     return response.json() 

# @api_view(["POST"])
# def place_ai_response(request):
#     URL = 'https://places.googleapis.com/v1/places:searchText'
    
#     # Request payload
#     payload = {
#         "textQuery": "Spicy Vegetarian Food in Sydney, Australia"
#     }
    
#     # Headers
#     headers = {
#         'Content-Type': 'application/json',
#         'X-Goog-Api-Key': PLACES_API_KEY,
#         'X-Goog-FieldMask': 'places.displayName,places.formattedAddress'
#     }
    
#     try:
#         # Make the POST request to Google Places API
#         response = requests.post(URL, json=payload, headers=headers)
        
#         # Check if the request was successful
#         if response.status_code == 200:
#             data = response.json()
#             # Return the places data or an empty list if no places are found
#             places = data.get('places', [])
#             return JsonResponse({'status': 'success', 'places': places}, status=200)
#         else:
#             # Handle API errors
#             error_message = response.json().get('error', 'Failed to fetch data from Google Places API')
#             return JsonResponse({'status': 'error', 'message': error_message}, status=response.status_code)
            
#     except requests.exceptions.RequestException as e:
#         # Handle network or request errors
#         return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
#     # query = request.data.get("textQuery")
#     # token = request.data.get("access_token")  # client must send this

#     # if not query:
#     #     return JsonResponse({"error": "textQuery is required"}, status=400)
#     # if not token:
#     #     return JsonResponse({"error": "access_token is required"}, status=400)

#     # url = "https://places.googleapis.com/v1/places:searchText"
#     # headers = {
#     #     "Authorization": f"Bearer {token}",
#     #     "Content-Type": "application/json",
#     #     "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.priceLevel"
#     # }
#     # data = {"textQuery": query}

#     # response = requests.post(url, headers=headers, json=data)
#     # return JsonResponse(response.json(), status=response.status_code)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_tourist_spot(request, day_id):
    """Add a tourist spot to a specific day of an itinerary."""
    try:
        day = Day.objects.get(id=day_id, itinerary__user=request.user)
    except Day.DoesNotExist:
        return Response({"error": "Day not found or not yours."}, status=status.HTTP_404_NOT_FOUND)

    serializer = TouristSpotSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(day=day)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points in kilometers."""
    R = 6371.0  # Radius of Earth in kilometers

    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance



# --- THE NEW RECOMMENDATION VIEW ---
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def get_recommendations(request):
    """
    Provides a list of recommended spots based on user's location,
    preferences, timing, and desired distance.
    """
    serializer = RecommendationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    user_lat = data['latitude']
    user_lon = data['longitude']
    max_distance_km = data['distance']

    # 1. Start with all spots
    queryset = Spot.objects.all()

    # 2. Filter by user preferences (tags) if provided
    if 'preferences' in data and data['preferences']:
        queryset = queryset.filter(tags__in=data['preferences']).distinct()

    # 3. Filter by timing (This requires making assumptions about your Spot model)
    #    Let's assume you have 'start_time' on your Spot model for this to work.
    #    This is a simplified example.
    timing = data['timing']
    if timing == 'MORNING':
        # Assuming you add `start_time` to your Spot model
        # queryset = queryset.filter(start_time__gte=time(6, 0), start_time__lt=time(12, 0))
        pass # Add your time filtering logic here
    elif timing == 'AFTERNOON':
        # queryset = queryset.filter(start_time__gte=time(12, 0), start_time__lt=time(18, 0))
        pass
    elif timing == 'EVENING':
        # queryset = queryset.filter(start_time__gte=time(18, 0), start_time__lt=time(23, 59))
        pass

    # 4. Filter by distance (in Python, since we are not using GeoDjango)
    all_matching_spots = list(queryset)
    recommended_spots = []

    for spot in all_matching_spots:
        if spot.latitude and spot.longitude:
            distance = haversine_distance(user_lat, user_lon, spot.latitude, spot.longitude)
            if distance <= max_distance_km:
                # You can even add the calculated distance to the spot object for the API response
                spot.distance_from_user = round(distance, 2)
                recommended_spots.append(spot)
    
    # 5. Serialize the final list of spots
    # We need a serializer that can show the 'distance_from_user'
    # For now, we reuse the SpotSerializer
    output_serializer = SpotSerializer(recommended_spots, many=True)
    return Response(output_serializer.data)
