from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PointOfInterest, GPXData
from django.http import HttpResponse
from django.shortcuts import render
import requests
from django.urls import path, reverse
from django import forms

# Register the CustomUser model with the admin site
admin.site.register(CustomUser, UserAdmin)

# Points of interest
#admin.site.register(PointOfInterest)

class PointOfInterestAdminForm(forms.ModelForm):
    class Meta:
        model = PointOfInterest
        fields = '__all__'

    # Override __init__ to implement autocomplete for the layer field
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['layer'].widget.attrs['class'] = 'autocomplete'
        #self.fields['layer'].widget.attrs['data-autocomplete-source'] = reverse('get_layers_list') + '?term='  # Set autocomplete data source using the URL
    
@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'latitude', 'longitude')
    search_fields = ('name', 'description')

    # Use the PointOfInterestAdminForm for the PointOfInterest admin interface
    form = PointOfInterestAdminForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.using('postgis')  # Specify the database alias for PostGIS
    
    def save_model(self, request, obj, form, change):
        # Set the database alias to 'postgis' before saving the object
        obj.save(using='postgis')

# GPX data

class GPXDataAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Customize queryset if needed
        return queryset

    def __str__(self):
        return self.gpx_file.name

admin.site.register(GPXData, GPXDataAdmin)


class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('layer-list/', self.admin_view(self.layer_list), name='layer_list'),
        ]
        return custom_urls + urls

    def layer_list(self, request):
        # Make a request to GeoServer API to get the list of layers
        geoserver_url = "http://localhost:8081/geoserver/rest/workspaces/tutorial/layers.json?list=available&detail=layerGroup&filter=enabled"
        response = requests.get(geoserver_url, auth=('admin', 'geoserver'))

        if response.status_code == 200:
            layer_names = [layer['name'] for layer in response.json()['layers']['layer']]
            return render(request, 'custom_layer_list.html', {'layer_names': layer_names})
        else:
            return HttpResponse("Failed to fetch layer list from GeoServer.")

# Instantiate CustomAdminSite
custom_admin_site = CustomAdminSite(name='custom_admin')
custom_admin_site.register(CustomUser, UserAdmin)
custom_admin_site.register(PointOfInterest, PointOfInterestAdmin)
custom_admin_site.register(GPXData, GPXDataAdmin)


# Register the custom admin site
admin.site = custom_admin_site