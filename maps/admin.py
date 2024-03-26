from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PointOfInterest, GPXData

# Register the CustomUser model with the admin site
admin.site.register(CustomUser, UserAdmin)

# Points of interest
#admin.site.register(PointOfInterest)

class PointOfInterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'latitude', 'longitude')
    search_fields = ('name', 'description')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.using('postgis')  # Specify the database alias for PostGIS
    
    def save_model(self, request, obj, form, change):
        # Set the database alias to 'postgis' before saving the object
        obj.save(using='postgis')

admin.site.register(PointOfInterest, PointOfInterestAdmin)

# GPX data

class GPXDataAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Customize queryset if needed
        return queryset

    def __str__(self):
        return self.gpx_file.name

admin.site.register(GPXData, GPXDataAdmin)

#admin.site.register(GPXData)