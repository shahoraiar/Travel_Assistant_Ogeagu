import requests
import math

API_KEY = "AIzaSyDy8Q6MoVTQqGdWvypYZ1BDHzHv2Go_tHE"

# Origin (Mohakhali Aqua Tower, Dhaka for example)
ORIGIN_LAT = 23.7805
ORIGIN_LNG = 90.4066

QUERY = "cafes near mohakhali aqua Tower, dhaka"
SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"

# --- Haversine function ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# --- 1. Perform a Text Search ---
params = {"query": QUERY, "key": API_KEY}
search_resp = requests.get(SEARCH_URL, params=params)
search_data = search_resp.json()

if search_data["status"] == "OK":
    for place in search_data["results"]:
        name = place.get("name", "N/A")
        address = place.get("formatted_address", "N/A")
        rating = place.get("rating", "N/A")
        place_id = place.get("place_id")
        lat = place["geometry"]["location"]["lat"]
        lng = place["geometry"]["location"]["lng"]

        distance_km = haversine(ORIGIN_LAT, ORIGIN_LNG, lat, lng)

        print("\n--- Place ---")
        print(f"Name: {name}")
        print(f"Address: {address}")
        print(f"Rating: {rating}")
        print(f"Distance: {distance_km:.2f} km")

        if place_id:
            # --- 2. Get Place Details ---
            details_params = {
                "place_id": place_id,
                "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,editorial_summary,reviews,photos",
                "key": API_KEY
            }
            details_resp = requests.get(DETAILS_URL, params=details_params)
            details_data = details_resp.json()

            if details_data.get("status") == "OK":
                result = details_data["result"]

                phone = result.get("formatted_phone_number", "N/A")
                website = result.get("website", "N/A")
                opening_hours = result.get("opening_hours", {}).get("weekday_text", [])
                about = result.get("editorial_summary", {}).get("overview", "N/A")

                print(f"Phone: {phone}")
                print(f"Website: {website}")
                print(f"About: {about}")

                if opening_hours:
                    print("Opening Hours:")
                    for day in opening_hours:
                        print(f"  {day}")

                # --- Photos ---
                photos = result.get("photos", [])
                if photos:
                    print("Photos:")
                    for i, photo in enumerate(photos[:5], 1):
                        photo_ref = photo["photo_reference"]
                        photo_url = f"{PHOTO_BASE_URL}?maxwidth=800&photoreference={photo_ref}&key={API_KEY}"
                        print(f"  {i}. {photo_url}")
                else:
                    print("No photos available.")

            else:
                print(f"Details API error: {details_data.get('status')}")
        else:
            print("No place_id found for this place.")
else:
    print(f"Search failed: {search_data.get('status')}")