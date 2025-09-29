import requests
import json

API_KEY = "AIzaSyDy8Q6MoVTQqGdWvypYZ1BDHzHv2Go_tHE"
QUERY = "cafes near mohakhali aqua Tower, dhaka" # Example query
BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

params = {
    "query": QUERY,
    "key": API_KEY
}

try:
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status() 
    data = response.json()

    if data["status"] == "OK":
        print("Search Results:")
        for place in data["results"]:
            print(place)  # Print the entire place dictionary
            # print(f"  Name: {place.get('name')}")
            # print(f"  Address: {place.get('formatted_address')}")
            # print(f"  Rating: {place.get('rating')}")
            print("-" * 20)
    else:
        print(f"Error: {data['status']} - {data.get('error_message', 'No specific error message.')}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError:
    print("Failed to decode JSON response.")