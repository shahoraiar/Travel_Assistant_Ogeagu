from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from .serializers import *
from math import radians, sin, cos, sqrt, atan2
from datetime import time
from django.http import JsonResponse
import json
from django.utils.timezone import now

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import requests
import math
from django.conf import settings

SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"

API_KEY = settings.GOOGLE_MAPS_API_KEY

# def haversine(lat1, lon1, lat2, lon2):
#     R = 6371  # Earth radius in km
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
#     return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

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

    valid_ids = set(Interest.objects.values_list("id", flat=True))
    invalid_ids = [pid for pid in pref_ids if pid not in valid_ids]

    if invalid_ids:
        return Response(
            {"error": f"The following preference IDs are invalid: {invalid_ids}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    preferences_name = []
    for pid in pref_ids:
        print('processing id: ', pid)
        pref, was_created = UserPreference.objects.get_or_create(
            user=user,
            preferences_id=pid
        )

        preferences_name.append(pref.preferences.name)

    return Response(
        {
            "message": "Preferences processed successfully",
            "preference_name": preferences_name
        },
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_preference_list(request): 
    user = request.user
    user_pref = user.preferences.select_related('preferences')
    serializer = UserPreferenceListSerializer(user_pref, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

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
    
    valid_ids = set(Interest.objects.values_list("id", flat=True))
    invalid_ids = [pid for pid in pref_ids if pid not in valid_ids]

    if invalid_ids:
        return Response(
            {"error": f"The following preference IDs are invalid: {invalid_ids}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    preferences_name = []
    for pid in pref_ids:
        print('processing id: ', pid)
        if UserPreference.objects.filter(user=user, preferences_id=pid).exists():
            pref = UserPreference.objects.get(user=user, preferences_id=pid)
            pref.delete()
            preferences_name.append(pref.preferences.name)
        else:
            print(f"Preference ID {pid} not found for user {user.username}")


    return Response(
        {
            "message": "Preferences deleted successfully",
            "preference_name": preferences_name
        },
        status=status.HTTP_200_OK
    )

# --- Function 3: Update user preference list ---
# @api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# def update_preference(request):
#     """Updates (replaces) the user's entire preference list."""
#     user = request.user
#     serializer = UserPreferenceSerializer(data=request.data)
#     if serializer.is_valid():
#         preference_ids = serializer.validated_data['preferences']
#         user.preferences.set(preference_ids)
#         return Response({"message": "Preference list updated successfully."}, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# --- Function 4: Create a new itinerary ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_itinerary(request):
    print('create itinerary request : ', request)
    user = request.user
    user_preferences = user.preferences.select_related('preferences')
    print('user preferences: ', user_preferences)
    
    if not user_preferences.exists():
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
        # print('time : ', now().date())
        itinerary = Itinerary.objects.filter(
            user=request.user,
            end_date__gte=now().date()  
        ) 
    except Itinerary.DoesNotExist:
        return Response({"error": "Itinerary not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ItineraryReadSerializer(itinerary, many=True) 
    return Response(serializer.data)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

@api_view(["POST"])
def nearest_restaurant(request):
    lat = request.data.get("latitude")
    lng = request.data.get("longitude")
    radius = int(request.data.get("radius", 5000)) 

    if not lat or not lng:
        return Response({"error": "Please provide latitude and longitude"}, status=400)

    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return Response({"error": "Latitude and longitude must be numeric"}, status=400)

    # Nearby search
    search_params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "restaurant",
        "key": API_KEY
    }

    try:
        search_resp = requests.get(SEARCH_URL, params=search_params)
        search_data = search_resp.json()

        if search_data.get("status") != "OK":
            return Response({"error": search_data.get("status")}, status=400)

        restaurants = []

        for place in search_data.get("results", []):
            place_id = place.get("place_id")
            place_lat = place["geometry"]["location"]["lat"]
            place_lng = place["geometry"]["location"]["lng"]
            distance_km = haversine(lat, lng, place_lat, place_lng)

            restaurant_info = {
                "name": place.get("name"),
                "location_name": place.get("vicinity"),
                "coordinates": {"latitude": place_lat, "longitude": place_lng},
                "distance_km": round(distance_km, 2),
                "opening_hours": [],
                "phone": None,
                "email": None,
                "website": None,
                "facebook": None,
                "instagram": None,
                "description": None,
                "reviews_summary": {}, 
                "reviews": [],
                "total_reviews": 0,
                "total_rating": 0.0,
                "photos": [],
                "map_link": f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}"
            }

            if place_id:
                details_params = {
                    "place_id": place_id,
                    "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,editorial_summary,reviews,photos",
                    "key": API_KEY
                }
                details_resp = requests.get(DETAILS_URL, params=details_params)
                details_data = details_resp.json()

                if details_data.get("status") == "OK":
                    result = details_data.get("result", {})

                    # Basic info
                    restaurant_info["description"] = result.get("editorial_summary", {}).get("overview", "")
                    restaurant_info["phone"] = result.get("formatted_phone_number")
                    restaurant_info["website"] = result.get("website")
                    restaurant_info["opening_hours"] = result.get("opening_hours", {}).get("weekday_text", [])
                    restaurant_info["total_reviews"] = result.get("user_ratings_total", 0)
                    restaurant_info["total_rating"] = result.get("rating", 0.0)

                    # Photos
                    photos = result.get("photos", [])
                    for photo in photos[:10]:
                        ref = photo.get("photo_reference")
                        if ref:
                            restaurant_info["photos"].append(f"{PHOTO_BASE_URL}?maxwidth=800&photoreference={ref}&key={API_KEY}")

                    # Reviews & rating breakdown
                    reviews = result.get("reviews", [])
                    star_count = {str(i): 0 for i in range(1,6)}
                    for review in reviews:
                        rating = review.get("rating")
                        if rating:
                            star_count[str(int(rating))] += 1
                            restaurant_info["reviews"].append({
                                "author": review.get("author_name"),
                                "rating": rating,
                                "text": review.get("text"),
                                "time": review.get("relative_time_description")
                            })
                    restaurant_info["reviews_summary"] = star_count

            restaurants.append(restaurant_info)

        # restaurants.sort(key=lambda x: x["distance_km"])

        return Response(restaurants, status=200)  

    except requests.RequestException as e:
        return Response({"error": str(e)}, status=500)


# @api_view(["POST"])
# def nearest_restaurant(request):
#     lat = request.data.get("latitude")
#     lng = request.data.get("longitude")

#     if not lat or not lng:
#         return Response({"error": "Please provide latitude and longitude"}, status=400)

#     try:
#         lat = float(lat)
#         lng = float(lng)
#     except ValueError:
#         return Response({"error": "Latitude and longitude must be numeric"}, status=400)

#     query_url = (
#         f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
#         f"?location={lat},{lng}&radius=500&type=restaurant&key={API_KEY}"
#     )

#     return Response({"query_url": query_url})

@api_view(["GET"])
def generate_ai_detailed_itinerary(request, id):
    """
    Generate AI-powered detailed itinerary with real place details
    """
    try:
        itinerary = Itinerary.objects.get(pk=pk, user_id=id)
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
