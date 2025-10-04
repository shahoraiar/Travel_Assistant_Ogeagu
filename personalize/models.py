from django.db import models
from django.conf import settings
from django.utils.text import slugify
from datetime import date

class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} -- {self.slug}"

    

# models.py (corrected UserPreference)

class UserPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences")
    preferences = models.ForeignKey(Interest, on_delete=models.CASCADE, related_name='preferred_by') 

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # This joins the names of all related Interest objects into a single string.
        # prefs = ", ".join([p.name for p in self.preferences.all()])
        return f"{self.user.username}'s Interests: {self.preferences.name}"

class Itinerary(models.Model):
    TRIP_TYPES = [('SOLO', 'Solo'), ('COUPLE', 'Couple'), ('FAMILY', 'Family'), ('GROUP', 'Group')]
    BUDGETS = [('50-100', '$50/100 day'), ('100-200', '$100/200 day'), ('200-300', '$200/300 day'), ('300-500+', '$300/500+ day')]
    DURATIONS = [('3_DAYS', '3 days'), ('5_DAYS', '5 days'), ('1_WEEK', '1 week'), ('10_DAYS', '10 days'), ('2_WEEKS', '2 weeks')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='itineraries')
    destination_name = models.CharField(max_length=255)
    latitude = models.CharField()
    longitude = models.CharField() 

    trip_type = models.CharField(max_length=10, choices=TRIP_TYPES, default='SOLO')
    budget = models.CharField(max_length=10, choices=BUDGETS, default='50-100')
    duration = models.CharField(max_length=10, choices=DURATIONS, blank=True, null=True)

    start_date = models.DateField(blank=True, null=True) 
    end_date = models.DateField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.user.username} -- {self.destination_name}" 
    
    def get_trip_type_display(self):
        return dict(self.TRIP_TYPES).get(self.trip_type, 'Unknown')

    def get_budget_display(self):
        return dict(self.BUDGETS).get(self.budget, 'Unknown')

    def get_duration_left_display(self):
        if self.duration is None or self.end_date is None:
            return 'Unknown'
        today = date.today()
        days_left = (self.end_date - today).days
        if days_left < 0:
            return "Trip ended"
        return f"{days_left} days left"

class Day(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveIntegerField()  
    visit_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    
    def __str__(self):
        return f"{self.day_number} of {self.itinerary.destination_name}"

class DaySpot(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name="places")
    place_id = models.CharField(max_length=255, blank=True, null=True)
    place_name = models.CharField(max_length=255, blank=True, null=True)
    place_location = models.CharField(max_length=255, blank=True, null=True)
    place_image = models.URLField(blank=True, null=True)
    place_type = models.CharField(max_length=255, blank=True, null=True)
    place_rating = models.CharField(max_length=50, blank=True, null=True)
    place_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f"{self.place_name} (Day {self.day.day_number})"

class Place(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(unique=True, max_length=255)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    longitude = models.CharField(max_length=100, blank=True, null=True) 
    rating = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.TextField()
    type = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



