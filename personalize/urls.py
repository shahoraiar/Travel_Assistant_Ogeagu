from django.urls import path
from .views import *

urlpatterns = [
    path('interests/', interests, name='interests-list'),
    path('preferences/user/list/', user_preference_list, name='user-preference-list'),
    path('preferences/create/', create_preference, name='create-preference'),
    # path('preferences/update/', update_preference, name='update-preference'),
    path('preferences/delete/', delete_preference, name='delete-preference'),
    path('itineraries/create/', create_itinerary, name='create-itinerary'),
    path('itineraries/', get_itinerary, name='get-itinerary'), 
    path('active-itinerary/', home_active_itinerary, name='home_active_itinerary'),

    # path('days/<int:day_id>/add-spot/', add_tourist_spot, name='add-tourist-spot'),
    # path('recommendations/', get_recommendations, name='get-recommendations'),

    # AI-powered itinerary generation for travel plans
    path('preferences/generate_day/', generate_day, name='generate_day'),

    path('home/all_day_plans/', all_day_plan, name="all_day_plan"),

    path('suggest/restaurant/', nearest_restaurant, name="nearest_restaurant"),
    path('suggest/hotel/', nearest_hotel, name="nearest_hotel"),
    path('suggest/art/', nearest_art_places, name="nearest_art_places"),

    path('nearby-retuarant/', nearby_restaurants, name="nearby_restaurants"),
    path('restaurant-details/<str:place_id>/', restaurant_details, name="restaurant_details")


    # path('itineraries/<int:itinerary_id>/complete/', complete_itinerary, name='complete-itinerary'),

]