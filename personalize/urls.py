from django.urls import path
from .views import *

urlpatterns = [
    path('interests/', interests, name='interests-list'),
    path('preferences/create/', create_preference, name='create-preference'),
    path('preferences/update/', update_preference, name='update-preference'),
    path('preferences/delete/', delete_preference, name='delete-preference'),
    path('itineraries/create/', create_itinerary, name='create-itinerary'),
    path('itineraries/', get_itinerary, name='get-itinerary'), 

    path('days/<int:day_id>/add-spot/', add_tourist_spot, name='add-tourist-spot'),
    path('recommendations/', get_recommendations, name='get-recommendations'),

    # path('ai/place', place_ai_response, name='place-ai-response'),
    # path('google/token', get_google_access_token, name='get-google-token'),
]