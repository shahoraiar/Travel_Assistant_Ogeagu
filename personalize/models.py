from django.db import models
from django.conf import settings
from django.utils.text import slugify

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

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    preferences = models.ManyToManyField(Interest, blank=True, related_name='preferred_by') 

    def __str__(self):
        # prefs = ", ".join([p.name for p in self.preferences.all()])
        return f"{self.user.username} -- {self.preferences.name}"


class Itinerary(models.Model):
    TRIP_TYPES = [('SOLO', 'Solo'), ('COUPLE', 'Couple'), ('FAMILY', 'Family'), ('GROUP', 'Group')]
    BUDGETS = [('50-100', '$50/100 day'), ('100-200', '$100/200 day'), ('200-300', '$200/300 day'), ('300-500+', '$300/500+ day')]
    DURATIONS = [('3_DAYS', '3 days'), ('5_DAYS', '5 days'), ('1_WEEK', '1 week'), ('10_DAYS', '10 days'), ('2_WEEKS', '2 weeks')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='itineraries')
    destination = models.CharField(max_length=255) 

    trip_type = models.CharField(max_length=10, choices=TRIP_TYPES, default='SOLO')
    budget = models.CharField(max_length=10, choices=BUDGETS, default='50-100')
    duration = models.CharField(max_length=10, choices=DURATIONS, blank=True, null=True)

    start_date = models.DateField(blank=True, null=True) 
    end_date = models.DateField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.user.username} -- {self.destination}" 
    
class Day(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveIntegerField()  # Day 1, Day 2, Day 3, ...

    def __str__(self):
        return f"{self.day_number} of {self.itinerary.destination}"


class TouristSpot(models.Model):
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name="spots")
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.location}) on {self.day}"