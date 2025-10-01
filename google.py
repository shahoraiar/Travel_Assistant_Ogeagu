import requests
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # or paste your key here
print('API KEY : ', API_KEY)
LATITUDE = 21.447194
LONGITUDE = 91.958361

url = "https://maps.googleapis.com/maps/api/geocode/json"
params = {
    "latlng": f"{LATITUDE},{LONGITUDE}",
    "key": API_KEY
}

response = requests.get(url, params=params)
data = response.json()

if data["status"] == "OK":
    # Best match (formatted address)
    print("Formatted Address:", data["results"][0]["formatted_address"])
    
    # All possible address components
    for result in data["results"]:
        print(result["formatted_address"])
else:
    print("Error:", data["status"])