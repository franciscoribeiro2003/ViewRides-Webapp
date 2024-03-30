# polls/forms.py
from django import forms
from .models import GPXData
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from .models import CustomUser, PointOfInterest
import requests

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

class GPXUploadForm(forms.ModelForm):
    class Meta:
        model = GPXData
        fields = ['gpx_file']

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class PointOfInterestForm(forms.ModelForm):
    class Meta:
        model = PointOfInterest
        fields = ['name', 'description', 'latitude', 'longitude', 'layer']
        

class GeoServerLayerWidget(forms.TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "http://localhost:8081/geoserver/rest/layers.json?list=available&detail=layerGroup&filter=enabled"  # GeoServer layers API URL

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        layers = self.fetch_layers()  # Fetch layers from GeoServer API
        options = '\n'.join([f'<option value="{layer["name"]}">{layer["name"]}</option>' for layer in layers])
        script = f'''
            <datalist id="{name}_datalist">
                {options}
            </datalist>
            <script>
            (function($) {{
                $(document).ready(function() {{
                    var input = $('input[name="{name}"]');
                    input.attr('list', '{name}_datalist');
                }});
            }})(django.jQuery);
            </script>
        '''
        return mark_safe(html + script)

    def fetch_layers(self):
        # Make a request to GeoServer layers API
        try:
            response = requests.get(self.base_url, auth=('admin', 'geoserver'))
            response.raise_for_status()
            data = response.json()
            if 'layers' in data and 'layer' in data['layers']:
                return data['layers']['layer']
            else:
                return []
        except Exception as e:
            print(f"Error fetching layers from GeoServer API: {e}")
            return []