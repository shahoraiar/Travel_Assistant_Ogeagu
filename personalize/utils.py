import requests
import os
from dotenv import load_dotenv
load_dotenv()
    


# --- Configuration ---
# It's best practice to get the API key from environment variables
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

# Origin (Mohakhali Aqua Tower, Dhaka for example)
# ORIGIN_LAT = 23.7805
# ORIGIN_LNG = 90.4066

QUERY = "cafes near mohakhali aqua Tower, dhaka"

SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"


# --- Constants ---
SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
REVERSE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

API_KEY = "AIzaimport requests
import os
import logging
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Use Django settings instead of direct environment access
GOOGLE_MAPS_API_KEY = getattr(settings, 'GOOGLE_MAPS_API_KEY', os.environ.get("GOOGLE_MAPS_API_KEY"))

SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
REVERSE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def get_location_name_from_coords(lat: float, lng: float) -> str:
    """Convert coordinates to human-readable address with better error handling"""
    if not GOOGLE_MAPS_API_KEY:
        logger.error("Google Maps API key not configured")
        return "Unknown Location"
    
    params = {
        "latlng": f"{lat},{lng}",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(REVERSE_GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            # Try to get locality first, then fall back to other address components
            for result in data['results']:
                for component in result['address_components']:
                    if 'locality' in component['types']:
                        country = next(
                            (c['long_name'] for c in result['address_components'] 
                             if 'country' in c['types']), 
                            ''
                        )
                        return f"{component['long_name']}, {country}"
            
            # Fallback to first formatted address
            return data["results"][0]["formatted_address"]
            
        else:
            logger.warning(f"Reverse geocoding failed: {data.get('status')}")
            return "Unknown Location"
            
    except requests.exceptions.Timeout:
        logger.error("Reverse geocoding request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Reverse geocoding request failed: {e}")
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Error parsing reverse geocoding response: {e}")
    
    return "Unknown Location"


def get_actual_places_details(query: str, lat: float, lng: float) -> Optional[Dict[str, Any]]:
    """
    Find real places using search query and location with better error handling
    """
    if not query or not GOOGLE_MAPS_API_KEY:
        return None
    
    params = {
        "query": query,
        "location": f"{lat},{lng}",
        "radius": 50000,  # Increased to 50km for better results
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        places_data = response.json()
        
        if places_data.get("status") == "OK" and places_data.get("results"):
            place = places_data["results"][0]
            
            # Get additional details using place_id
            detailed_place = get_place_details(place.get("place_id"))
            if detailed_place:
                place.update(detailed_place)
            
            return place
        else:
            logger.warning(f"Place search failed for query '{query}': {places_data.get('status')}")
            
    except requests.exceptions.Timeout:
        logger.error(f"Place search timed out for query: {query}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Place search request failed for query '{query}': {e}")
    
    return None


def get_place_details(place_id: str) -> Optional[Dict[str, Any]]:
    """Get additional place details using place_id"""
    if not place_id:
        return None
    
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,rating,user_ratings_total,types,editorial_summary",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(PLACE_DETAILS_URL, params=params, timeout=10)
        response.raise_for_status()
        details_data = response.json()
        
        if details_data.get("status") == "OK" and details_data.get("result"):
            result = details_data["result"]
            return {
                "description": result.get("editorial_summary", {}).get("overview"),
                "types": result.get("types", [])
            }
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to get place details for {place_id}: {e}")
    
    return None