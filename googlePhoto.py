import requests
import json

API_KEY = "AIzaSyDy8Q6MoVTQqGdWvypYZ1BDHzHv2Go_tHE"
QUERY = "cafes near mohakhali aqua Tower, dhaka"
BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"

params = {
    "query": QUERY,
    "key": API_KEY
}

try:
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if data["status"] == "OK":
        print("Search Results:\n")
        for place in data["results"]:
            name = place.get("name", "N/A")
            address = place.get("formatted_address", "N/A")
            rating = place.get("rating", "No Rating")
            total_ratings = place.get("user_ratings_total", "N/A")
            business_status = place.get("business_status", "N/A")

            print(f"Name: {name}")
            print(f"Address: {address}")
            print(f"Rating: {rating} ({total_ratings} reviews)")
            print(f"Status: {business_status}")

            # Collect up to 5 photo links
            photos = place.get("photos", [])
            if photos:
                print("Photos:")
                for i, photo in enumerate(photos[:5], 1):
                    photo_ref = photo["photo_reference"]
                    photo_url = f"{PHOTO_BASE_URL}?maxwidth=800&photoreference={photo_ref}&key={API_KEY}"
                    print(f"  {i}. {photo_url}")
            else:
                print("No photos available.")

            print("-" * 40)

    else:
        print(f"Error: {data['status']} - {data.get('error_message', 'No specific error message.')}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError:
    print("Failed to decode JSON response.")
