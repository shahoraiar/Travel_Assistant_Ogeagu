import requests
import json
import io
from PIL import Image
import matplotlib.pyplot as plt
import math

API_KEY = "AIzaSyDy8Q6MoVTQqGdWvypYZ1BDHzHv2Go_tHE"

# Define your origin point (e.g., a specific address or current location)
# Example: Center of Paris for "Eiffel Tower" search
ORIGIN_LAT = 48.8566
ORIGIN_LNG = 2.3522

QUERY = "Eiffel Tower"
BASE_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
BASE_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"

# --- Helper function to calculate Haversine distance ---
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance # Distance in kilometers

# --- 1. Perform a Text Search ---
search_params = {
    "query": QUERY,
    "key": API_KEY
}

try:
    search_response = requests.get(BASE_SEARCH_URL, params=search_params)
    search_response.raise_for_status()
    search_data = search_response.json()

    if search_data["status"] == "OK" and search_data["results"]:
        for place in search_data["results"]: # Iterate through all found places
            place_name = place.get('name', 'N/A')
            place_rating = place.get('rating', 'No Rating')
            place_lat = place['geometry']['location']['lat']
            place_lng = place['geometry']['location']['lng']

            # Calculate distance
            distance_km = haversine_distance(ORIGIN_LAT, ORIGIN_LNG, place_lat, place_lng)

            print(f"\n--- Place Details ---")
            print(f"Name: {place_name}")
            print(f"Rating: {place_rating}")
            print(f"Distance from origin ({ORIGIN_LAT}, {ORIGIN_LNG}): {distance_km:.2f} km")

            photo_found = False
            if 'photos' in place and place['photos']:
                first_photo = place['photos'][0]
                photo_reference = first_photo['photo_reference']

                # --- 2. Construct and fetch the photo ---
                photo_params = {
                    "photo_reference": photo_reference,
                    "maxwidth": 400,
                    "key": API_KEY
                }
                photo_response = requests.get(BASE_PHOTO_URL, params=photo_params)
                photo_response.raise_for_status()

                try:
                    image_bytes = io.BytesIO(photo_response.content)
                    img = Image.open(image_bytes)

                    # Display image
                    plt.figure(figsize=(6,6)) # Optional: set figure size
                    plt.imshow(img)
                    plt.title(f"{place_name} Image")
                    plt.axis('off')
                    plt.show()
                    photo_found = True
                except Exception as e:
                    print(f"Could not display image for {place_name}: {e}")
            
            if not photo_found:
                print("No photo available for this place.")

    else:
        print(f"No results found for query: {QUERY} or error: {search_data.get('status')}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError:
    print("Failed to decode JSON response.")