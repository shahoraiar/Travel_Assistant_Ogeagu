from django.contrib import admin
from .models import Interest, Itinerary

class InterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'created_at', 'updated_at')
    search_fields = ('name',)
    fields = ('name',)
    list_display_links = ('id', 'name')
    # prepopulated_fields = {'slug': ('name',)}  # Automatically populate slug from name
admin.site.register(Interest, InterestAdmin)

 
admin.site.register(Itinerary) # Also register Itinerary for easy viewing
