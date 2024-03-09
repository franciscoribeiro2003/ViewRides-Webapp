# polls/forms.py
from django import forms
from .models import GPXData
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomUser


class GPXUploadForm(forms.ModelForm):
    class Meta:
        model = GPXData
        fields = ['gpx_file']

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']