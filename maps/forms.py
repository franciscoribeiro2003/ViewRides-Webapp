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
        

